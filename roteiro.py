"""Visão Roteiro — experiência principal por dia e por cidade."""
from __future__ import annotations

import re
from datetime import date, timedelta
from html import escape

import pandas as pd
import streamlit as st

import ui

WEEKDAYS_PT = {
    0: "segunda",
    1: "terça",
    2: "quarta",
    3: "quinta",
    4: "sexta",
    5: "sábado",
    6: "domingo",
}

MAX_CITY_COLS = 4


def _key_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip())
    return slug.strip("_") or "x"


def _as_date(value) -> date | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, date) and not isinstance(value, pd.Timestamp):
        return value
    ts = pd.Timestamp(value)
    if pd.isna(ts):
        return None
    return ts.date()


def _fmt_date(d: date) -> str:
    return f"{WEEKDAYS_PT[d.weekday()].capitalize()}, {d.strftime('%d/%m/%Y')}"


def _hotels_for_day(hospedagem: pd.DataFrame, day: date) -> pd.DataFrame:
    if hospedagem.empty:
        return hospedagem
    day_ts = pd.Timestamp(day)
    mask = (hospedagem["checkin"] <= day_ts) & (hospedagem["checkout"] > day_ts)
    return hospedagem[mask]


def _transports_for_day(transportes: pd.DataFrame, day: date) -> pd.DataFrame:
    if transportes.empty:
        return transportes
    day_ts = pd.Timestamp(day)
    return transportes[transportes["data"].dt.normalize() == day_ts]


def _progress_counts(activities: pd.DataFrame) -> tuple[int, int]:
    if activities.empty:
        return 0, 0
    total = len(activities)
    confirmed = int((activities["status"] == "Confirmado").sum())
    return confirmed, total


def _render_empty_state() -> None:
    st.html(
        '<div class="et-empty">'
        "<strong>Nenhuma atividade neste filtro</strong>"
        "Ajuste cidade ou período na barra lateral — ou adicione itens na aba Itinerário."
        "</div>"
    )


def _render_hotel_chips(hotels: pd.DataFrame) -> None:
    if hotels.empty:
        return
    chips = []
    for _, h in hotels.iterrows():
        nome = escape(str(h.get("nome", "Hotel")))
        cidade = escape(str(h.get("cidade", "")))
        horario = escape(str(h.get("horario_checkin", "") or "").strip())
        extra = f" · check-in {horario}" if horario else ""
        chips.append(
            f'<span class="et-chip et-chip--hotel">Hotel: {nome} · {cidade}{extra}</span>'
        )
    st.html(f'<div class="et-chip-row">{"".join(chips)}</div>')


def _render_transport_chips(transports: pd.DataFrame) -> None:
    if transports.empty:
        return
    chips = []
    for _, t in transports.iterrows():
        tipo = escape(str(t.get("tipo", "Trecho")))
        origem = escape(str(t.get("origem", "")))
        destino = escape(str(t.get("destino", "")))
        saida = escape(str(t.get("hora_saida", "") or "").strip())
        chegada = escape(str(t.get("hora_chegada", "") or "").strip())
        if saida and chegada:
            hours = f" · {saida}→{chegada}"
        elif saida:
            hours = f" · sai {saida}"
        else:
            hours = " · horário a definir"
        chips.append(
            f'<span class="et-chip">{tipo}: {origem} → {destino}{hours}</span>'
        )
    st.html(f'<div class="et-chip-row">{"".join(chips)}</div>')


def _render_day_block(
    day: date,
    activities: pd.DataFrame,
    hotels: pd.DataFrame,
    transports: pd.DataFrame,
    today: date,
) -> None:
    confirmed, total = _progress_counts(activities)
    cities = sorted({str(c) for c in activities["cidade"].tolist() if str(c).strip()})
    if not cities and not hotels.empty:
        cities = sorted({str(c) for c in hotels["cidade"].tolist() if str(c).strip()})

    is_today = day == today
    cities_html = " · ".join(escape(c) for c in cities) if cities else "—"
    today_tag = '<span class="et-today-tag">Hoje</span>' if is_today else ""
    day_class = "et-day-head et-day-head--today" if is_today else "et-day-head"

    with st.container(border=True):
        st.html(
            f'<div class="{day_class}">'
            f'<span class="et-day-date">{escape(_fmt_date(day))} {today_tag}</span>'
            f'<span class="et-day-cities">{cities_html}</span>'
            f'<span class="et-day-progress">{confirmed}/{total} confirmados</span>'
            f"</div>"
        )

        _render_hotel_chips(hotels)
        _render_transport_chips(transports)

        if activities.empty:
            st.caption("Sem atividades neste dia — só deslocamento ou hospedagem.")
        else:
            for _, row in activities.sort_values(["tipo", "atividade"]).iterrows():
                ui.render_activity_card(row, key_prefix=f"day_{day.isoformat()}")


def render_por_dia(
    itinerario: pd.DataFrame,
    transportes: pd.DataFrame,
    hospedagem: pd.DataFrame,
) -> None:
    today = date.today()

    if itinerario.empty and transportes.empty and hospedagem.empty:
        _render_empty_state()
        return

    dates: set[date] = set()
    if not itinerario.empty:
        for d in itinerario["data"]:
            ad = _as_date(d)
            if ad:
                dates.add(ad)
    if not transportes.empty:
        for d in transportes["data"]:
            ad = _as_date(d)
            if ad:
                dates.add(ad)
    if not hospedagem.empty:
        for _, h in hospedagem.iterrows():
            start = _as_date(h["checkin"])
            end = _as_date(h["checkout"])
            if start and end:
                cur = start
                while cur < end:
                    dates.add(cur)
                    cur += timedelta(days=1)

    if not dates:
        _render_empty_state()
        return

    for day in sorted(dates):
        day_ts = pd.Timestamp(day)
        acts = (
            itinerario[itinerario["data"].dt.normalize() == day_ts]
            if not itinerario.empty
            else itinerario
        )
        hotels = _hotels_for_day(hospedagem, day)
        transports = _transports_for_day(transportes, day)
        if acts.empty and hotels.empty and transports.empty:
            continue
        _render_day_block(day, acts, hotels, transports, today)


def _cities_ordered(itinerario: pd.DataFrame, hospedagem: pd.DataFrame) -> list[str]:
    rows: list[tuple[pd.Timestamp, str]] = []
    if not itinerario.empty:
        for _, r in itinerario.iterrows():
            rows.append((r["data"], str(r["cidade"])))
    if not hospedagem.empty:
        for _, r in hospedagem.iterrows():
            rows.append((r["checkin"], str(r["cidade"])))
    rows.sort(key=lambda x: x[0])
    seen: list[str] = []
    for _, city in rows:
        city = city.strip()
        if city and city not in seen:
            seen.append(city)
    return seen


def _render_city_column(
    cidade: str,
    itinerario: pd.DataFrame,
    transportes: pd.DataFrame,
    hospedagem: pd.DataFrame,
) -> None:
    acts = itinerario[itinerario["cidade"] == cidade] if not itinerario.empty else itinerario
    hotels = hospedagem[hospedagem["cidade"] == cidade] if not hospedagem.empty else hospedagem

    if not transportes.empty:
        transports = transportes[
            (transportes["origem"] == cidade) | (transportes["destino"] == cidade)
        ]
    else:
        transports = transportes

    confirmed, total = _progress_counts(acts)
    pais = ""
    if not acts.empty and "pais" in acts.columns:
        pais = str(acts.iloc[0]["pais"])

    with st.container(border=True):
        st.html(
            f'<div class="et-city-head">'
            f"<h3>{escape(cidade)}</h3>"
            f'<div class="et-city-sub">{escape(pais) + " · " if pais else ""}'
            f"{confirmed}/{total} confirmados</div>"
            f"</div>"
        )

        if not hotels.empty:
            for _, h in hotels.iterrows():
                ci = _as_date(h["checkin"])
                co = _as_date(h["checkout"])
                range_txt = ""
                if ci and co:
                    range_txt = f" · {ci.strftime('%d/%m')}–{co.strftime('%d/%m')}"
                st.caption(f":material/hotel: {h['nome']}{range_txt}")

        if not transports.empty:
            for _, t in transports.sort_values("data").iterrows():
                d = _as_date(t["data"])
                d_txt = d.strftime("%d/%m") if d else "?"
                st.caption(
                    f":material/directions_transit: {d_txt} · {t['tipo']}: "
                    f"{t['origem']} → {t['destino']}"
                )

        if acts.empty:
            st.caption("Sem atividades nesta cidade no filtro atual.")
        else:
            city_key = _key_slug(cidade)
            for _, row in acts.sort_values(["data", "atividade"]).iterrows():
                d = _as_date(row["data"])
                if d:
                    st.caption(f":material/calendar_today: {_fmt_date(d)}")
                ui.render_activity_card(
                    row,
                    key_prefix=f"city_{city_key}",
                    compact=True,
                )


def render_por_cidade(
    itinerario: pd.DataFrame,
    transportes: pd.DataFrame,
    hospedagem: pd.DataFrame,
) -> None:
    cities = _cities_ordered(itinerario, hospedagem)
    if not cities:
        _render_empty_state()
        return

    default_visible = cities[:MAX_CITY_COLS]
    visible = st.multiselect(
        "Cidades visíveis",
        options=cities,
        default=default_visible,
        help=f"Mostre até {MAX_CITY_COLS} colunas por vez para manter a leitura confortável.",
        key="roteiro_cidades_visiveis",
    )

    if not visible:
        st.info("Selecione ao menos uma cidade para ver as colunas.", icon=":material/info:")
        return

    if len(visible) > MAX_CITY_COLS:
        st.warning(
            f"Mostrando as primeiras {MAX_CITY_COLS} cidades selecionadas. "
            "Desmarque algumas para ver as outras.",
            icon=":material/view_column:",
        )
        visible = visible[:MAX_CITY_COLS]

    cols = st.columns(len(visible), gap="medium")
    for col, cidade in zip(cols, visible):
        with col:
            _render_city_column(cidade, itinerario, transportes, hospedagem)


def render_roteiro(
    itinerario: pd.DataFrame,
    transportes: pd.DataFrame,
    hospedagem: pd.DataFrame,
) -> None:
    """Entrada principal da aba Roteiro."""
    ui.inject_roteiro_css()

    total = len(itinerario)
    confirmed = int((itinerario["status"] == "Confirmado").sum()) if total else 0
    pending = int((itinerario["status"] == "Sugestão - validar").sum()) if total else 0

    top_l, top_r = st.columns([2, 1], vertical_alignment="bottom")
    with top_l:
        st.markdown("### :material/map: Roteiro")
        st.caption(
            f"{confirmed} confirmadas · {pending} a validar · {total} atividades no filtro"
        )
    with top_r:
        modo = st.segmented_control(
            "Modo de visão",
            options=["Por dia", "Por cidade"],
            default="Por dia",
            key="roteiro_modo",
            label_visibility="collapsed",
            required=True,
        )

    st.space("small")

    if modo == "Por cidade":
        render_por_cidade(itinerario, transportes, hospedagem)
    else:
        # default / None → por dia
        render_por_dia(itinerario, transportes, hospedagem)

    with st.expander("Adicionar atividade ao itinerário", expanded=False):
        if st.button("Nova atividade", icon=":material/add:", type="primary", key="roteiro_add"):
            ui.open_form_dialog("add", "itinerario", "Itinerário", ui.ITINERARIO_FIELDS)

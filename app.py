"""EUROTRIP 2026 — painel de controle da viagem (Itália + Albânia).

Rodar com: streamlit run app.py
"""
from __future__ import annotations

from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

import db
import roteiro
import ui

st.set_page_config(
    page_title="EUROTRIP 2026",
    page_icon=":material/map:",
    layout="wide",
)

db.init_db()


# =============================================================================
# Carregamento de dados
# =============================================================================

itinerario = db.load_df("itinerario")
transportes = db.load_df("transportes")
hospedagem = db.load_df("hospedagem")
atracoes = db.load_df("atracoes")
financeiro = db.load_df("financeiro")
checklist = db.load_df("checklist")


# =============================================================================
# Helpers de filtro
# =============================================================================


def apply_cidade_filter(df: pd.DataFrame, cols: list[str], cidades: list[str]) -> pd.DataFrame:
    if not cidades:
        return df
    mask = pd.Series(False, index=df.index)
    for col in cols:
        mask = mask | df[col].isin(cidades)
    return df[mask]


def apply_period_filter(df: pd.DataFrame, cols: list[str], start: date, end: date) -> pd.DataFrame:
    start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
    if len(cols) == 1:
        col = cols[0]
        return df[(df[col] >= start_ts) & (df[col] <= end_ts)]
    col_start, col_end = cols
    return df[(df[col_start] <= end_ts) & (df[col_end] >= start_ts)]


def parse_date_range(value, fallback_start: date, fallback_end: date) -> tuple[date, date]:
    if isinstance(value, tuple) and len(value) == 2:
        return value
    if isinstance(value, tuple) and len(value) == 1:
        return value[0], fallback_end
    if value is None:
        return fallback_start, fallback_end
    return value, value


# =============================================================================
# Sidebar — navegação e filtros globais
# =============================================================================

with st.sidebar:
    st.markdown("## :material/map: EUROTRIP 2026")
    st.caption(" · ".join(sorted(itinerario["pais"].unique())))

    ui.render_theme_toggle()
    ui.apply_app_theme()

    todas_cidades = sorted(
        set(itinerario["cidade"]) | set(hospedagem["cidade"]) | set(atracoes["cidade"])
    )
    cidade_filtro = st.multiselect("Cidade", todas_cidades, default=[])

    min_data = itinerario["data"].min().date()
    max_data = itinerario["data"].max().date()
    periodo_raw = st.date_input(
        "Período",
        value=(min_data, max_data),
        min_value=min_data,
        max_value=max_data,
    )
    periodo_ini, periodo_fim = parse_date_range(periodo_raw, min_data, max_data)

    st.caption("Os filtros afetam Roteiro, Itinerário, Transportes, Hospedagem e Atrações.")

    st.space("small")
    if st.button("Restaurar roteiro original", icon=":material/restart_alt:", type="tertiary"):
        st.session_state["confirm_reset"] = True

    if st.session_state.get("confirm_reset"):
        st.warning(
            "Isso apaga todas as suas edições e recarrega o roteiro original dos CSVs.",
            icon=":material/warning:",
        )
        cc1, cc2 = st.columns(2)
        if cc1.button("Cancelar", width="stretch"):
            st.session_state["confirm_reset"] = False
            st.rerun()
        if cc2.button("Restaurar", type="primary", width="stretch"):
            db.reset_db()
            st.session_state["confirm_reset"] = False
            st.rerun()


# =============================================================================
# Cabeçalho + KPIs (compactos)
# =============================================================================

st.markdown("# :material/map: EUROTRIP 2026")

dias_viagem = (itinerario["data"].max() - itinerario["data"].min()).days + 1
paises = itinerario["pais"].nunique()
confirmados = int((itinerario["status"] == "Confirmado").sum())
orcamento_estimado = float(financeiro["valor_estimado"].sum(skipna=True))
gasto_real = float(financeiro["valor_real"].sum(skipna=True))
saldo = orcamento_estimado - gasto_real

st.caption(
    f"{itinerario['data'].min():%d/%m} a {itinerario['data'].max():%d/%m/%Y} · "
    f"{dias_viagem} dias · {paises} países · organize o dia a dia no Roteiro"
)

with st.expander("Resumo da viagem (KPIs, timeline e alertas)", expanded=False):
    with st.container(horizontal=True):
        st.metric("Dias de viagem", dias_viagem, border=True)
        st.metric("Países", paises, border=True)
        st.metric("Atividades", len(itinerario), border=True)
        st.metric("Confirmados", confirmados, border=True)
        st.metric("Orçamento estimado", f"€ {orcamento_estimado:,.0f}", border=True)
        st.metric(
            "Saldo (estimado − real)",
            f"€ {saldo:,.0f}",
            border=True,
            delta_color="off" if gasto_real == 0 else "normal",
        )

    st.space("small")
    col_timeline, col_alertas = st.columns([2, 1])

    with col_timeline:
        with st.container(border=True):
            st.markdown("**:material/timeline: Timeline da viagem**")
            tl = hospedagem.copy()
            tl["Noites"] = (tl["checkout"] - tl["checkin"]).dt.days
            chart = (
                alt.Chart(tl)
                .mark_bar(cornerRadius=4)
                .encode(
                    x=alt.X("checkin:T", title=None),
                    x2="checkout:T",
                    y=alt.Y(
                        "cidade:N",
                        sort=alt.EncodingSortField(field="checkin", op="min"),
                        title=None,
                    ),
                    color=alt.Color("cidade:N", legend=None),
                    tooltip=[
                        alt.Tooltip("cidade:N", title="Cidade"),
                        alt.Tooltip("checkin:T", title="Check-in", format="%d/%m"),
                        alt.Tooltip("checkout:T", title="Check-out", format="%d/%m"),
                        alt.Tooltip("Noites:Q", title="Noites"),
                    ],
                )
                .properties(height=280)
            )
            st.altair_chart(chart)
            st.caption("Hospedagens ao longo do período.")

    with col_alertas:
        with st.container(border=True, height="stretch"):
            st.markdown("**:material/schedule: Alertas de horário**")

            hoje = pd.Timestamp(date.today())
            futuros = transportes[transportes["data"] >= hoje].sort_values("data")
            if not futuros.empty:
                prox = futuros.iloc[0]
                st.info(
                    f"Próximo trecho: **{prox['origem']} → {prox['destino']}** "
                    f"em {prox['data'].strftime('%d/%m/%Y')}"
                    + (f" às {prox['hora_saida']}" if str(prox["hora_saida"]).strip() else ""),
                    icon=":material/flight_takeoff:",
                )
            else:
                st.caption("Nenhum trecho futuro a partir de hoje.")

            pendentes = transportes[
                (transportes["hora_saida"].astype(str).str.strip() == "")
                | (transportes["hora_chegada"].astype(str).str.strip() == "")
            ]
            if not pendentes.empty:
                st.warning(
                    f"{len(pendentes)} trecho(s) sem horário confirmado:",
                    icon=":material/warning:",
                )
                for _, row in pendentes.iterrows():
                    st.caption(
                        f"• {row['id']} — {row['origem']} → {row['destino']} "
                        f"({row['data'].strftime('%d/%m')})"
                    )
            else:
                st.success(
                    "Todos os trechos têm horário definido.",
                    icon=":material/check_circle:",
                )


# =============================================================================
# Abas — Roteiro primeiro
# =============================================================================

tabs = st.tabs(
    [
        ":material/map: Roteiro",
        ":material/calendar_month: Itinerário",
        ":material/directions_car: Transportes",
        ":material/hotel: Hospedagem",
        ":material/attractions: Atrações",
        ":material/payments: Financeiro",
        ":material/checklist: Checklist",
    ]
)

# --- ROTEIRO ---
with tabs[0]:
    it_f = apply_cidade_filter(itinerario, ["cidade"], cidade_filtro)
    it_f = apply_period_filter(it_f, ["data"], periodo_ini, periodo_fim)

    tr_f = apply_cidade_filter(transportes, ["origem", "destino"], cidade_filtro)
    tr_f = apply_period_filter(tr_f, ["data"], periodo_ini, periodo_fim)

    ho_f = apply_cidade_filter(hospedagem, ["cidade"], cidade_filtro)
    ho_f = apply_period_filter(ho_f, ["checkin", "checkout"], periodo_ini, periodo_fim)

    roteiro.render_roteiro(
        it_f,
        tr_f,
        ho_f,
        checklist=checklist,
        all_itinerario=itinerario,
        all_transportes=transportes,
        all_hospedagem=hospedagem,
    )

# --- ITINERÁRIO ---
with tabs[1]:
    filtered = apply_cidade_filter(itinerario, ["cidade"], cidade_filtro)
    filtered = apply_period_filter(filtered, ["data"], periodo_ini, periodo_fim)

    ui.render_crud_cards(
        "itinerario",
        "Itinerário",
        filtered,
        ui.ITINERARIO_FIELDS,
        display_fn=lambda r: f"{r['data']:%d/%m} — {r['atividade']} ({r['cidade']})",
        title_fn=lambda r: str(r["atividade"]),
        icon_fn=lambda r: ui.tipo_icon(str(r.get("tipo", "Outro"))),
        badge_fn=lambda r: ui.status_badge_html(str(r.get("status", "Sugestão - validar"))),
        lines_fn=lambda r: [
            f":material/calendar_today: {ui._fmt_date_short(r['data'])} · {r['cidade']} ({r['pais']})",
            f":material/category: {r['tipo']}",
            str(r.get("descricao", "") or "").strip() or None,
        ],
        quick_action=dict(
            label="Confirmar",
            icon=":material/check:",
            field="status",
            value="Confirmado",
            toast="Atividade confirmada.",
            when=lambda r: str(r.get("status")) != "Confirmado",
        ),
        columns=2,
    )

    with st.expander("Atividades por país", expanded=False):
        st.bar_chart(itinerario.groupby("pais").size(), x_label="País", y_label="Atividades")

# --- TRANSPORTES ---
with tabs[2]:
    filtered = apply_cidade_filter(transportes, ["origem", "destino"], cidade_filtro)
    filtered = apply_period_filter(filtered, ["data"], periodo_ini, periodo_fim)

    transportes_fields = [
        dict(key="tipo", label="Tipo", type="select", options=["Voo", "Trem", "Barco", "Ônibus", "Carro", "Outro"], default="Trem"),
        dict(key="origem", label="Origem", type="text"),
        dict(key="destino", label="Destino", type="text"),
        dict(key="data", label="Data", type="date", default=date(2026, 8, 6)),
        dict(key="hora_saida", label="Hora de saída", type="text", help="Formato HH:MM"),
        dict(key="hora_chegada", label="Hora de chegada", type="text", help="Formato HH:MM"),
        dict(key="status", label="Status", type="select", options=["Confirmado", "Sugestão - validar", "Cancelado"], default="Sugestão - validar"),
        dict(key="duracao", label="Duração", type="text", help="Ex.: 1h30"),
    ]

    def _transporte_lines(r):
        saida = str(r.get("hora_saida", "") or "").strip()
        chegada = str(r.get("hora_chegada", "") or "").strip()
        if saida and chegada:
            horas = f"{saida} → {chegada}"
        elif saida:
            horas = f"sai {saida}"
        else:
            horas = "horário a definir"
        dur = str(r.get("duracao", "") or "").strip()
        return [
            f":material/calendar_today: {ui._fmt_date_short(r['data'])}",
            f":material/schedule: {horas}" + (f" · {dur}" if dur else ""),
            f":material/tag: {r['id']}",
        ]

    ui.render_crud_cards(
        "transportes",
        "Transportes",
        filtered,
        transportes_fields,
        display_fn=lambda r: f"{r['origem']} → {r['destino']} ({r['data']:%d/%m})",
        title_fn=lambda r: f"{r['origem']} → {r['destino']}",
        icon_fn=lambda r: ui.tipo_icon(str(r.get("tipo", "Outro"))),
        badge_fn=lambda r: ui.status_badge_html(str(r.get("status", "Sugestão - validar"))),
        lines_fn=_transporte_lines,
        quick_action=dict(
            label="Confirmar",
            icon=":material/check:",
            field="status",
            value="Confirmado",
            toast="Trecho confirmado.",
            when=lambda r: str(r.get("status")) != "Confirmado",
        ),
        columns=1,
    )

# --- HOSPEDAGEM ---
with tabs[3]:
    filtered = apply_cidade_filter(hospedagem, ["cidade"], cidade_filtro)
    filtered = apply_period_filter(filtered, ["checkin", "checkout"], periodo_ini, periodo_fim)

    hospedagem_fields = [
        dict(key="cidade", label="Cidade", type="text"),
        dict(key="nome", label="Hotel / acomodação", type="text", default="A definir"),
        dict(key="checkin", label="Check-in", type="date", default=date(2026, 8, 6)),
        dict(key="checkout", label="Check-out", type="date", default=date(2026, 8, 7)),
        dict(key="horario_checkin", label="Horário check-in", type="text", help="Formato HH:MM", default="15:00"),
        dict(key="observacoes", label="Observações", type="textarea"),
    ]

    def _hotel_lines(r):
        noites = int((r["checkout"] - r["checkin"]).days) if pd.notna(r["checkout"]) and pd.notna(r["checkin"]) else 0
        horario = str(r.get("horario_checkin", "") or "").strip()
        obs = str(r.get("observacoes", "") or "").strip()
        return [
            f":material/location_on: {r['cidade']}",
            f":material/login: Check-in {ui._fmt_date_short(r['checkin'])}"
            + (f" às {horario}" if horario else ""),
            f":material/logout: Check-out {ui._fmt_date_short(r['checkout'])} · {noites} noite(s)",
            obs or None,
        ]

    ui.render_crud_cards(
        "hospedagem",
        "Hospedagem",
        filtered,
        hospedagem_fields,
        display_fn=lambda r: f"{r['cidade']} — {r['nome']}",
        title_fn=lambda r: str(r["nome"]),
        icon_fn=lambda _r: ":material/hotel:",
        lines_fn=_hotel_lines,
        columns=1,
    )

    noites_total = int((hospedagem["checkout"] - hospedagem["checkin"]).dt.days.sum())
    st.metric("Total de noites no roteiro", noites_total, border=True)

# --- ATRAÇÕES ---
with tabs[4]:
    filtered = apply_cidade_filter(atracoes, ["cidade"], cidade_filtro)

    atracoes_fields = [
        dict(key="nome", label="Atração", type="text"),
        dict(key="cidade", label="Cidade", type="text"),
        dict(key="tipo", label="Tipo", type="select", options=["Ponto turístico", "Museu", "Passeio", "Memorial/Museu", "Outro"], default="Ponto turístico"),
        dict(key="necessita_ingresso", label="Necessita ingresso?", type="checkbox", default=True),
        dict(key="preco_eur", label="Preço (EUR)", type="number", step=0.5),
        dict(key="horario_marcado", label="Horário marcado", type="text", default="A definir"),
        dict(key="duracao_estimada", label="Duração estimada", type="text", help="Ex.: 1h30"),
    ]

    def _atracao_lines(r):
        ingresso = "Precisa de ingresso" if bool(r.get("necessita_ingresso")) else "Sem ingresso"
        preco = ui._fmt_money(r.get("preco_eur"), "EUR")
        horario = str(r.get("horario_marcado", "") or "").strip() or "A definir"
        dur = str(r.get("duracao_estimada", "") or "").strip()
        return [
            f":material/location_on: {r['cidade']} · {r['tipo']}",
            f":material/confirmation_number: {ingresso} · {preco}",
            f":material/schedule: {horario}" + (f" · {dur}" if dur else ""),
        ]

    def _atracao_badge(r):
        if bool(r.get("necessita_ingresso")):
            return ui.plain_badge_html("Ingresso", kind="warn")
        return ui.plain_badge_html("Livre", kind="ok")

    ui.render_crud_cards(
        "atracoes",
        "Atrações",
        filtered,
        atracoes_fields,
        display_fn=lambda r: f"{r['nome']} ({r['cidade']})",
        title_fn=lambda r: str(r["nome"]),
        icon_fn=lambda _r: ":material/attractions:",
        badge_fn=_atracao_badge,
        lines_fn=_atracao_lines,
        columns=2,
    )

# --- FINANCEIRO ---
with tabs[5]:
    financeiro_fields = [
        dict(key="categoria", label="Categoria", type="select", options=["Passeio", "Hospedagem", "Transporte", "Alimentação", "Outro"], default="Passeio"),
        dict(key="item", label="Item", type="text"),
        dict(key="valor_estimado", label="Valor estimado", type="number", step=1.0),
        dict(key="valor_real", label="Valor real", type="number", step=1.0),
        dict(key="moeda", label="Moeda", type="select", options=["EUR", "BRL", "USD", "PLN", "ALL"], default="EUR"),
        dict(key="pago", label="Pago?", type="checkbox", default=False),
    ]

    def _fin_lines(r):
        moeda = str(r.get("moeda", "EUR"))
        return [
            f":material/category: {r['categoria']}",
            f":material/payments: Estimado {ui._fmt_money(r.get('valor_estimado'), moeda)}"
            f" · Real {ui._fmt_money(r.get('valor_real'), moeda)}",
        ]

    ui.render_crud_cards(
        "financeiro",
        "Financeiro",
        financeiro,
        financeiro_fields,
        display_fn=lambda r: f"{r['item']} (€ {r['valor_estimado']:.0f})" if pd.notna(r.get("valor_estimado")) else str(r["item"]),
        title_fn=lambda r: str(r["item"]),
        icon_fn=lambda _r: ":material/payments:",
        badge_fn=lambda r: ui.plain_badge_html("Pago", kind="ok") if bool(r.get("pago")) else ui.plain_badge_html("Pendente", kind="warn"),
        lines_fn=_fin_lines,
        quick_action=dict(
            label="Marcar pago",
            icon=":material/paid:",
            field="pago",
            value=True,
            toast="Item marcado como pago.",
            when=lambda r: not bool(r.get("pago")),
        ),
        columns=2,
    )

    fc1, fc2, fc3 = st.columns(3)
    fc1.metric("Total estimado", f"€ {financeiro['valor_estimado'].sum(skipna=True):,.0f}", border=True)
    fc2.metric("Total gasto real", f"€ {financeiro['valor_real'].sum(skipna=True):,.0f}", border=True)
    fc3.metric("Itens pagos", f"{int(financeiro['pago'].sum())} / {len(financeiro)}", border=True)

    with st.expander("Gasto estimado por categoria", expanded=False):
        st.bar_chart(
            financeiro.groupby("categoria")["valor_estimado"].sum(),
            x_label="Categoria",
            y_label="Valor estimado (EUR)",
        )

# --- CHECKLIST ---
with tabs[6]:
    checklist_fields = [
        dict(key="categoria", label="Categoria", type="select", options=["Documentos", "Medicamentos", "Bagagem", "Eletrônicos", "Financeiro", "Outro"], default="Documentos"),
        dict(key="item", label="Item", type="text"),
        dict(key="concluido", label="Concluído?", type="checkbox", default=False),
    ]

    ui.render_crud_cards(
        "checklist",
        "Checklist",
        checklist,
        checklist_fields,
        display_fn=lambda r: r["item"],
        title_fn=lambda r: str(r["item"]),
        icon_fn=lambda r: ":material/check_circle:" if bool(r.get("concluido")) else ":material/radio_button_unchecked:",
        badge_fn=lambda r: (
            ui.plain_badge_html("Feito", kind="ok")
            if bool(r.get("concluido"))
            else ui.plain_badge_html("Pendente", kind="warn")
        ),
        lines_fn=lambda r: [f":material/folder: {r['categoria']}"],
        quick_action=dict(
            label="Marcar feito",
            icon=":material/check:",
            field="concluido",
            value=True,
            toast="Item concluído.",
            when=lambda r: not bool(r.get("concluido")),
        ),
        columns=2,
    )

    pendentes_check = int((~checklist["concluido"]).sum())
    st.progress(1 - pendentes_check / max(len(checklist), 1))
    st.caption(f"{pendentes_check} de {len(checklist)} itens pendentes")

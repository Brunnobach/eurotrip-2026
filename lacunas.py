"""Detecta lacunas entre trechos do roteiro (transporte, hotel, docs, mobilidade)."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

import db


@dataclass(frozen=True)
class Gap:
    id: str
    kind: str
    title: str
    detail: str
    after_day: date | None  # aparece depois deste dia no Roteiro
    icon: str


def _as_date(value) -> date | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, date) and not isinstance(value, pd.Timestamp):
        return value
    ts = pd.Timestamp(value)
    if pd.isna(ts):
        return None
    return ts.date()


def _gap_id(*parts: str) -> str:
    raw = "|".join(str(p) for p in parts)
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()[:10]
    return f"GAP-{digest}"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


# Conexões geográficas do roteiro (trem/aeroporto ≠ nome da cidade base)
CITY_ALIASES: dict[str, set[str]] = {
    "milão": {"milão", "milan", "milano", "brasil"},
    "lago di garda": {"lago di garda", "pordenone", "peschiera", "desenzano", "garda"},
    "sorrento": {"sorrento", "nápoles", "napoles", "napoli", "veneza", "venice"},
    "positano": {"positano"},
    "amalfi": {"amalfi"},
    "capri": {"capri"},
    "pompeia": {"pompeia", "pompei", "herculano"},
    "roma": {"roma", "rome", "termini"},
    "tirana": {"tirana"},
}


def _aliases(city: str) -> set[str]:
    n = _norm(city)
    return CITY_ALIASES.get(n, {n}) if n else set()


def _city_in_text(city: str, text: str) -> bool:
    t = _norm(text)
    if not t:
        return False
    for alias in _aliases(city):
        if alias and alias in t:
            return True
    token = _norm(city).split(" ")[0]
    return len(token) >= 4 and token in t


def _text_blank(value) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return True
    s = str(value).strip().lower()
    return s in {"", "nan", "none", "nat"}


def _primary_city(day: date, itinerario: pd.DataFrame, hospedagem: pd.DataFrame) -> str | None:
    day_ts = pd.Timestamp(day)
    if not itinerario.empty:
        acts = itinerario[itinerario["data"].dt.normalize() == day_ts]
        if not acts.empty:
            # cidade mais frequente do dia
            return str(acts["cidade"].mode().iloc[0])
    if not hospedagem.empty:
        cover = hospedagem[
            (hospedagem["checkin"] <= day_ts) & (hospedagem["checkout"] > day_ts)
        ]
        if not cover.empty:
            return str(cover.iloc[0]["cidade"])
    return None


def _primary_country(day: date, itinerario: pd.DataFrame) -> str | None:
    if itinerario.empty:
        return None
    day_ts = pd.Timestamp(day)
    acts = itinerario[itinerario["data"].dt.normalize() == day_ts]
    if acts.empty or "pais" not in acts.columns:
        return None
    return str(acts["pais"].mode().iloc[0])


def _hotel_city(day: date, hospedagem: pd.DataFrame) -> str | None:
    if hospedagem.empty:
        return None
    day_ts = pd.Timestamp(day)
    cover = hospedagem[
        (hospedagem["checkin"] <= day_ts) & (hospedagem["checkout"] > day_ts)
    ]
    if cover.empty:
        return None
    return str(cover.iloc[0]["cidade"])


def _has_transport_link(
    transportes: pd.DataFrame,
    day: date,
    origem: str,
    destino: str,
) -> bool:
    if transportes.empty:
        return False
    # aceita no dia da mudança ou no dia anterior (saídas matinais)
    days = {day, day - timedelta(days=1)}
    for _, t in transportes.iterrows():
        td = _as_date(t["data"])
        if td not in days:
            continue
        o, d = str(t.get("origem", "")), str(t.get("destino", ""))
        # ligação frouxa: origem menciona cidade de saída OU destino a de chegada
        if _city_in_text(origem, o) or _city_in_text(origem, d):
            if _city_in_text(destino, o) or _city_in_text(destino, d):
                return True
        # também: qualquer trecho no dia cujo destino é a cidade nova
        if _city_in_text(destino, d):
            return True
    return False


def _has_local_mobility(transportes: pd.DataFrame, day: date, city: str) -> bool:
    if transportes.empty:
        return False
    day_ts = pd.Timestamp(day)
    for _, t in transportes[transportes["data"].dt.normalize() == day_ts].iterrows():
        if _city_in_text(city, str(t.get("origem", ""))) or _city_in_text(
            city, str(t.get("destino", ""))
        ):
            return True
    return False


def detect_gaps(
    itinerario: pd.DataFrame,
    transportes: pd.DataFrame,
    hospedagem: pd.DataFrame,
) -> list[Gap]:
    """Analisa o roteiro e devolve lacunas acionáveis entre trechos."""
    gaps: list[Gap] = []
    seen: set[str] = set()

    def add(gap: Gap) -> None:
        if gap.id not in seen:
            seen.add(gap.id)
            gaps.append(gap)

    # Datas do roteiro (união)
    dates: set[date] = set()
    if not itinerario.empty:
        for d in itinerario["data"]:
            ad = _as_date(d)
            if ad:
                dates.add(ad)
    if not hospedagem.empty:
        for _, h in hospedagem.iterrows():
            start, end = _as_date(h["checkin"]), _as_date(h["checkout"])
            if start and end:
                cur = start
                while cur < end:
                    dates.add(cur)
                    cur += timedelta(days=1)
    ordered = sorted(dates)
    if not ordered:
        return []

    # 1) Transições de base (hotel) / país — bate-volta não conta como mudança de cidade
    for prev, curr in zip(ordered, ordered[1:]):
        hotel_a = _hotel_city(prev, hospedagem)
        hotel_b = _hotel_city(curr, hospedagem)
        city_a = hotel_a or _primary_city(prev, itinerario, hospedagem)
        city_b = hotel_b or _primary_city(curr, itinerario, hospedagem)

        base_changed = bool(city_a and city_b and _norm(city_a) != _norm(city_b))
        if base_changed:
            if not _has_transport_link(transportes, curr, city_a, city_b):
                add(
                    Gap(
                        id=_gap_id("tr", city_a, city_b, curr.isoformat()),
                        kind="transporte",
                        title=f"Transporte {city_a} → {city_b}",
                        detail=(
                            f"Vocês mudam de base em {_fmt(curr)}. "
                            "Falta um trecho (trem, voo, barco, ônibus ou carro) ligando os dois."
                        ),
                        after_day=prev,
                        icon=":material/directions_transit:",
                    )
                )

        country_a = _primary_country(prev, itinerario)
        country_b = _primary_country(curr, itinerario)
        if country_a and country_b and _norm(country_a) != _norm(country_b):
            add(
                Gap(
                    id=_gap_id("docs", country_a, country_b, curr.isoformat()),
                    kind="documentos",
                    title=f"Documentos: {country_a} → {country_b}",
                    detail=(
                        f"Troca de país em {_fmt(curr)}. Conferir passaporte, seguro, "
                        "moeda local e regras de entrada (ex.: Schengen → Albânia)."
                    ),
                    after_day=prev,
                    icon=":material/badge:",
                )
            )

    # 2) Noites sem hotel + hotel "A definir"
    for day in ordered:
        # última data do roteiro pode ser dia de checkout/voo — só alerta se há atividade de pernoite
        hotel = None
        if not hospedagem.empty:
            day_ts = pd.Timestamp(day)
            cover = hospedagem[
                (hospedagem["checkin"] <= day_ts) & (hospedagem["checkout"] > day_ts)
            ]
            hotel = cover.iloc[0] if not cover.empty else None

        city = _primary_city(day, itinerario, hospedagem)
        is_last = day == ordered[-1]
        if hotel is None and city and not is_last:
            add(
                Gap(
                    id=_gap_id("hotel_miss", city, day.isoformat()),
                    kind="hospedagem",
                    title=f"Hotel em {city} ({_fmt(day)})",
                    detail="Não há hospedagem cobrindo esta noite. Reservar ou confirmar onde dormem.",
                    after_day=day - timedelta(days=1) if day != ordered[0] else day,
                    icon=":material/hotel:",
                )
            )
        elif hotel is not None:
            nome = str(hotel.get("nome", "")).strip()
            if _norm(nome) in {"a definir", "a definir.", "tbd", ""}:
                checkin = _as_date(hotel["checkin"])
                checkout = _as_date(hotel["checkout"])
                after = checkin
                if checkin and checkin != ordered[0]:
                    after = checkin - timedelta(days=1)
                add(
                    Gap(
                        id=_gap_id("hotel_tbd", str(hotel.get("id", city))),
                        kind="hospedagem",
                        title=f"Reservar hotel em {hotel['cidade']}",
                        detail=(
                            f"Estadia {_fmt(checkin)} → {_fmt(checkout)} "
                            "ainda está como “A definir”."
                        ),
                        after_day=after,
                        icon=":material/hotel:",
                    )
                )

    # 3) Bate-volta: cidade do dia ≠ cidade do hotel → falta mobilidade local
    for day in ordered:
        act_city = None
        if not itinerario.empty:
            day_ts = pd.Timestamp(day)
            acts = itinerario[itinerario["data"].dt.normalize() == day_ts]
            if not acts.empty:
                act_city = str(acts["cidade"].mode().iloc[0])
        hotel_city = _hotel_city(day, hospedagem)
        if act_city and hotel_city and _norm(act_city) != _norm(hotel_city):
            if not _has_local_mobility(transportes, day, act_city):
                add(
                    Gap(
                        id=_gap_id("local", hotel_city, act_city, day.isoformat()),
                        kind="mobilidade",
                        title=f"Como ir a {act_city}?",
                        detail=(
                            f"Base em {hotel_city} com passeio em {act_city} ({_fmt(day)}). "
                            "Definir barco, ônibus, trem, transfer ou aluguel de moto/carro."
                        ),
                        after_day=day - timedelta(days=1) if day != ordered[0] else day,
                        icon=":material/two_wheeler:",
                    )
                )

    # 4) Transportes sem horário
    if not transportes.empty:
        for _, t in transportes.iterrows():
            if not _text_blank(t.get("hora_saida")) and not _text_blank(t.get("hora_chegada")):
                continue
            td = _as_date(t["data"])
            add(
                Gap(
                    id=_gap_id("horas", str(t["id"])),
                    kind="horario",
                    title=f"Horário: {t['origem']} → {t['destino']}",
                    detail=(
                        f"Trecho {t['tipo']} em {_fmt(td) if td else '?'}: "
                        "falta hora de saída e/ou chegada."
                    ),
                    after_day=td - timedelta(days=1) if td and td != ordered[0] else td,
                    icon=":material/schedule:",
                )
            )

    # Ordena por dia de exibição
    gaps.sort(key=lambda g: (g.after_day or date.min, g.kind, g.title))
    return gaps


def _fmt(d: date | None) -> str:
    if not d:
        return "?"
    return d.strftime("%d/%m")


def sync_gaps_to_checklist(gaps: list[Gap], checklist: pd.DataFrame) -> pd.DataFrame:
    """Garante uma linha no checklist para cada lacuna (categoria Entre trechos)."""
    existing_ids = set(checklist["id"].astype(str)) if not checklist.empty else set()
    gap_ids = {g.id for g in gaps}

    for g in gaps:
        if g.id in existing_ids:
            continue
        db.insert_row(
            "checklist",
            {
                "id": g.id,
                "categoria": "Entre trechos",
                "item": f"{g.title} — {g.detail}",
                "concluido": False,
            },
        )
        existing_ids.add(g.id)

    # Remove lacunas obsoletas ainda pendentes (já resolvidas de verdade no roteiro)
    if not checklist.empty:
        orphans = checklist[
            checklist["id"].astype(str).str.startswith("GAP-")
            & ~checklist["id"].astype(str).isin(gap_ids)
            & (~checklist["concluido"].astype(bool))
        ]
        if not orphans.empty:
            db.delete_rows("checklist", list(orphans["id"]))

    return db.load_df("checklist")


def checklist_done_map(checklist: pd.DataFrame) -> dict[str, bool]:
    if checklist.empty:
        return {}
    out: dict[str, bool] = {}
    for _, r in checklist.iterrows():
        out[str(r["id"])] = bool(r.get("concluido"))
    return out

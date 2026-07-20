"""Componentes de CRUD reutilizáveis + helpers visuais do Roteiro."""
from __future__ import annotations

from datetime import date
from html import escape

import pandas as pd
import streamlit as st

import db

# -----------------------------------------------------------------------------
# Visual tokens (alinhados ao tema .streamlit/config.toml)
# -----------------------------------------------------------------------------

STATUS_META: dict[str, dict] = {
    "Confirmado": {
        "label": "Confirmado",
        "color": "#166534",
        "bg": "#DCFCE7",
        "border": "#86EFAC",
        "icon": ":material/check_circle:",
    },
    "Sugestão - validar": {
        "label": "A validar",
        "color": "#92400E",
        "bg": "#FEF3C7",
        "border": "#FCD34D",
        "icon": ":material/pending:",
    },
    "Cancelado": {
        "label": "Cancelado",
        "color": "#991B1B",
        "bg": "#FEE2E2",
        "border": "#FCA5A5",
        "icon": ":material/cancel:",
    },
}

TIPO_ICONS: dict[str, str] = {
    "Deslocamento": ":material/directions_transit:",
    "Turismo": ":material/attractions:",
    "Descanso": ":material/spa:",
    "Outro": ":material/more_horiz:",
    "Voo": ":material/flight:",
    "Trem": ":material/train:",
    "Barco": ":material/directions_boat:",
    "Ônibus": ":material/directions_bus:",
    "Carro": ":material/directions_car:",
}

ITINERARIO_FIELDS: list[dict] = [
    dict(key="data", label="Data", type="date", default=date(2026, 8, 6)),
    dict(key="cidade", label="Cidade", type="text"),
    dict(key="pais", label="País", type="text"),
    dict(key="atividade", label="Atividade", type="text"),
    dict(key="tipo", label="Tipo", type="select", options=["Deslocamento", "Turismo", "Descanso", "Outro"], default="Turismo"),
    dict(key="descricao", label="Descrição", type="textarea"),
    dict(
        key="status",
        label="Status",
        type="select",
        options=["Confirmado", "Sugestão - validar", "Cancelado"],
        default="Sugestão - validar",
    ),
]

ROTEIRO_CSS = """
<style>
/* —— EUROTRIP Roteiro —— */
.et-day-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.45rem 0.9rem;
  margin: 0 0 0.65rem 0;
  padding: 0.15rem 0 0.7rem 0;
  border-bottom: 1px solid #EAEDEC;
}
.et-day-head--today {
  border-bottom-color: #0F766E;
  background: linear-gradient(90deg, rgba(15,118,110,0.08), transparent 70%);
  margin: -0.25rem -0.35rem 0.65rem;
  padding: 0.45rem 0.5rem 0.75rem;
  border-radius: 8px 8px 0 0;
}
.et-day-date {
  font-size: 1.12rem;
  font-weight: 650;
  color: #1A1A1A;
  letter-spacing: -0.01em;
}
.et-day-cities {
  color: #0F766E;
  font-weight: 550;
  font-size: 0.95rem;
}
.et-day-progress {
  margin-left: auto;
  font-size: 0.78rem;
  color: #57534E;
  background: #F4F6F5;
  border: 1px solid #E2E5E4;
  border-radius: 999px;
  padding: 0.15rem 0.65rem;
}
.et-badge {
  display: inline-flex;
  align-items: center;
  font-size: 0.7rem;
  font-weight: 650;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  border-radius: 999px;
  padding: 0.2rem 0.55rem;
  border: 1px solid transparent;
  white-space: nowrap;
}
.et-chip {
  display: inline-flex;
  align-items: center;
  font-size: 0.84rem;
  background: #F0FDFA;
  border: 1px solid #99F6E4;
  color: #115E59;
  border-radius: 8px;
  padding: 0.35rem 0.65rem;
  margin: 0 0.35rem 0.35rem 0;
}
.et-chip--hotel {
  background: #FFF7ED;
  border-color: #FDBA74;
  color: #9A3412;
}
.et-chip-row {
  display: flex;
  flex-wrap: wrap;
  margin: 0.15rem 0 0.55rem 0;
}
.et-card-title {
  font-weight: 600;
  font-size: 0.98rem;
  color: #1A1A1A;
  margin: 0 0 0.15rem 0;
  line-height: 1.3;
}
.et-card-meta {
  font-size: 0.8rem;
  color: #737373;
  margin-bottom: 0.3rem;
}
.et-card-desc {
  font-size: 0.88rem;
  color: #44403C;
  line-height: 1.4;
  margin: 0 0 0.45rem 0;
}
.et-city-head h3 {
  margin: 0 0 0.1rem 0;
  font-size: 1.08rem;
  color: #0F766E;
  font-weight: 650;
}
.et-city-sub {
  font-size: 0.78rem;
  color: #737373;
  margin-bottom: 0.55rem;
}
.et-empty {
  text-align: center;
  padding: 2.5rem 1rem;
  color: #737373;
  border: 1px dashed #D6D3D1;
  border-radius: 12px;
  background: #FAFAF9;
}
.et-empty strong {
  display: block;
  color: #1A1A1A;
  font-size: 1.05rem;
  margin-bottom: 0.35rem;
}
.et-today-tag {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #0F766E;
  background: #CCFBF1;
  border-radius: 4px;
  padding: 0.12rem 0.4rem;
  vertical-align: middle;
}
.et-gap {
  border: 1px dashed #D97706;
  border-radius: 12px;
  padding: 0.75rem 0.9rem;
  margin: 0.35rem 0 1rem 0;
  background: #FFFBEB;
}
.et-gap-title {
  font-weight: 650;
  color: #92400E;
  font-size: 0.95rem;
  margin: 0 0 0.2rem 0;
}
.et-gap-detail {
  color: #78716C;
  font-size: 0.86rem;
  line-height: 1.4;
  margin: 0 0 0.45rem 0;
}
.et-gap-label {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #B45309;
  margin-bottom: 0.45rem;
}
.et-gap-summary {
  border: 1px solid #F59E0B;
  border-radius: 12px;
  padding: 0.85rem 1rem;
  margin: 0 0 1rem 0;
  background: linear-gradient(180deg, #FFFBEB 0%, #FFFFFF 100%);
}
</style>
"""

# Tokens de badge para fundo escuro (texto claro + fundo saturado = contraste alto)
STATUS_META_DARK: dict[str, dict] = {
    "Confirmado": {
        "label": "Confirmado",
        "color": "#BBF7D0",
        "bg": "#14532D",
        "border": "#4ADE80",
        "icon": ":material/check_circle:",
    },
    "Sugestão - validar": {
        "label": "A validar",
        "color": "#FDE68A",
        "bg": "#78350F",
        "border": "#FBBF24",
        "icon": ":material/pending:",
    },
    "Cancelado": {
        "label": "Cancelado",
        "color": "#FECACA",
        "bg": "#7F1D1D",
        "border": "#F87171",
        "icon": ":material/cancel:",
    },
}

# Shell do app em modo escuro — contraste alto, sem cinza-em-cinza
DARK_APP_CSS = """
<style>
/* —— EUROTRIP dark shell —— */
html, body, [data-testid="stAppViewContainer"], .stApp,
[data-testid="stAppViewBlockContainer"],
section.main {
  background-color: #0B1210 !important;
  color: #E8EEEC !important;
}
[data-testid="stHeader"] {
  background: rgba(11, 18, 16, 0.92) !important;
}
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebarContent"] {
  background-color: #121A17 !important;
  color: #E8EEEC !important;
  border-right: 1px solid #2A3531 !important;
}
[data-testid="stSidebar"] * {
  color: #E8EEEC;
}
/* Texto principal */
.stMarkdown, .stMarkdown p, .stMarkdown li, .stCaption, .stText,
[data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"],
label, .stSelectbox, .stMultiSelect {
  color: #E8EEEC !important;
}
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
  color: #F4F7F6 !important;
}
.stCaption, [data-testid="stCaptionContainer"] {
  color: #A8B5B0 !important;
}
/* Containers / cards nativos */
[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stExpander"],
[data-testid="stMetric"] {
  background-color: #16201C !important;
  border-color: #2F3D38 !important;
  color: #E8EEEC !important;
}
[data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
  color: #F4F7F6 !important;
}
/* Inputs */
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea,
[data-baseweb="select"] > div,
[data-baseweb="base-input"],
.stTextInput input, .stNumberInput input, .stDateInput input,
.stTextArea textarea {
  background-color: #0F1714 !important;
  color: #F4F7F6 !important;
  border-color: #3A4A44 !important;
  caret-color: #F4F7F6 !important;
}
[data-baseweb="popover"],
[data-baseweb="menu"],
ul[role="listbox"] {
  background-color: #16201C !important;
  color: #E8EEEC !important;
  border-color: #3A4A44 !important;
}
li[role="option"] {
  color: #E8EEEC !important;
}
li[role="option"]:hover {
  background-color: #1F2C27 !important;
}
/* Tabs */
button[data-baseweb="tab"] {
  color: #A8B5B0 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
  color: #5EEAD4 !important;
}
/* Dataframe */
[data-testid="stDataFrame"],
[data-testid="stDataFrameResizable"] {
  background-color: #121A17 !important;
  color: #E8EEEC !important;
}
/* Alertas legíveis */
[data-testid="stAlert"] {
  color: #F4F7F6 !important;
}
/* Diálogos */
[data-testid="stModal"], [role="dialog"] {
  background-color: #16201C !important;
  color: #E8EEEC !important;
}
/* Progress / dividers */
hr {
  border-color: #2F3D38 !important;
}
/* Links */
a { color: #5EEAD4 !important; }

/* —— Roteiro dark overrides —— */
.et-day-head {
  border-bottom-color: #2F3D38;
}
.et-day-head--today {
  border-bottom-color: #2DD4BF;
  background: linear-gradient(90deg, rgba(45, 212, 191, 0.16), transparent 72%);
}
.et-day-date { color: #F4F7F6; }
.et-day-cities { color: #5EEAD4; }
.et-day-progress {
  color: #D1DAD6;
  background: #1F2C27;
  border-color: #3A4A44;
}
.et-chip {
  background: #134E4A;
  border-color: #2DD4BF;
  color: #CCFBF1;
}
.et-chip--hotel {
  background: #7C2D12;
  border-color: #FB923C;
  color: #FFEDD5;
}
.et-card-title { color: #F4F7F6; }
.et-card-meta { color: #A8B5B0; }
.et-card-desc { color: #D1DAD6; }
.et-city-head h3 { color: #5EEAD4; }
.et-city-sub { color: #A8B5B0; }
.et-empty {
  color: #A8B5B0;
  border-color: #3A4A44;
  background: #121A17;
}
.et-empty strong { color: #F4F7F6; }
.et-today-tag {
  color: #042F2E;
  background: #5EEAD4;
}
.et-gap {
  border-color: #F59E0B;
  background: #291C0E;
}
.et-gap-title { color: #FDE68A; }
.et-gap-detail { color: #D6D3D1; }
.et-gap-label { color: #FBBF24; }
.et-gap-summary {
  border-color: #D97706;
  background: linear-gradient(180deg, #291C0E 0%, #16201C 100%);
}
</style>
"""


def is_dark_mode() -> bool:
    return bool(st.session_state.get("dark_mode", False))


def render_theme_toggle() -> bool:
    """Toggle na sidebar. Retorna se o modo escuro está ativo."""
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = False
    return bool(
        st.toggle(
            "Modo escuro",
            key="dark_mode",
            help="Alto contraste para leitura noturna. Badges e cards acompanham o tema.",
        )
    )


def apply_app_theme() -> None:
    """Aplica CSS global do modo escuro (se ativo)."""
    if is_dark_mode():
        st.html(DARK_APP_CSS)


def inject_roteiro_css() -> None:
    """Injeta CSS base do Roteiro (overrides escuros vêm de apply_app_theme)."""
    st.html(ROTEIRO_CSS)
    if is_dark_mode():
        # Garante overrides mesmo se a ordem de injeção variar
        st.html(DARK_APP_CSS)


def status_badge_html(status: str) -> str:
    palette = STATUS_META_DARK if is_dark_mode() else STATUS_META
    meta = palette.get(status, palette["Sugestão - validar"])
    return (
        f'<span class="et-badge" style="color:{meta["color"]};background:{meta["bg"]};'
        f'border-color:{meta["border"]};">{escape(meta["label"])}</span>'
    )


def tipo_icon(tipo: str) -> str:
    return TIPO_ICONS.get(tipo, TIPO_ICONS["Outro"])


def _render_field(field: dict, current):
    key, label, ftype = field["key"], field["label"], field["type"]
    help_text = field.get("help")

    if ftype == "date":
        val = current.date() if isinstance(current, pd.Timestamp) else field.get("default", date.today())
        return st.date_input(label, value=val, key=f"field_{key}_{id(field)}")

    if ftype == "select":
        options = field["options"]
        fallback = field.get("default", options[0])
        chosen = current if current in options else fallback
        idx = options.index(chosen) if chosen in options else 0
        return st.selectbox(label, options, index=idx, key=f"field_{key}_{id(field)}")

    if ftype == "number":
        val = float(current) if current is not None and not pd.isna(current) else field.get("default", 0.0)
        return st.number_input(
            label, value=val, step=field.get("step", 1.0), min_value=0.0,
            format="%.2f", help=help_text, key=f"field_{key}_{id(field)}",
        )

    if ftype == "checkbox":
        val = bool(current) if current is not None else field.get("default", False)
        return st.checkbox(label, value=val, key=f"field_{key}_{id(field)}")

    if ftype == "textarea":
        val = current if isinstance(current, str) and current else field.get("default", "")
        return st.text_area(label, value=val, help=help_text, key=f"field_{key}_{id(field)}")

    val = current if isinstance(current, str) and current else field.get("default", "")
    return st.text_input(label, value=val, help=help_text, key=f"field_{key}_{id(field)}")


def _reset_selection(table: str) -> None:
    st.session_state.pop(f"{table}_select", None)


def open_form_dialog(mode: str, table: str, label: str, fields: list[dict], row=None) -> None:
    title = f"Adicionar em {label}" if mode == "add" else f"Editar item de {label}"

    @st.dialog(title)
    def _dialog():
        values = {}
        for f in fields:
            current = row[f["key"]] if row is not None else None
            values[f["key"]] = _render_field(f, current)

        st.space("small")
        with st.container(horizontal=True, horizontal_alignment="distribute"):
            if st.button("Cancelar", width="stretch"):
                st.rerun()
            if st.button("Salvar", type="primary", icon=":material/check:", width="stretch"):
                if mode == "add":
                    db.insert_row(table, values)
                else:
                    db.update_row(table, row["id"], values)
                _reset_selection(table)
                st.toast(f"{label}: item salvo.", icon=":material/check_circle:")
                st.rerun()

    _dialog()


def open_delete_dialog(table: str, label: str, rows: pd.DataFrame, display_fn) -> None:
    @st.dialog(f"Excluir de {label}?")
    def _dialog():
        st.warning(
            f"Tem certeza que deseja excluir {len(rows)} item(ns)? Essa ação não pode ser desfeita.",
            icon=":material/warning:",
        )
        for _, r in rows.iterrows():
            st.caption(f"• {display_fn(r)}")

        st.space("small")
        with st.container(horizontal=True, horizontal_alignment="distribute"):
            if st.button("Cancelar", width="stretch"):
                st.rerun()
            if st.button("Excluir", type="primary", icon=":material/delete:", width="stretch"):
                db.delete_rows(table, list(rows["id"]))
                _reset_selection(table)
                st.toast(f"{len(rows)} item(ns) excluído(s).", icon=":material/delete:")
                st.rerun()

    _dialog()


def set_itinerario_status(row_id: str, status: str, toast: str) -> None:
    db.update_row("itinerario", row_id, {"status": status})
    st.toast(toast, icon=":material/check_circle:")
    st.rerun()


def render_activity_card(row: pd.Series, key_prefix: str, compact: bool = False) -> None:
    """Card de atividade do itinerário com ações rápidas."""
    status = str(row.get("status", "Sugestão - validar"))
    tipo = str(row.get("tipo", "Outro"))
    atividade = str(row.get("atividade", ""))
    descricao = str(row.get("descricao", "") or "").strip()
    cidade = str(row.get("cidade", ""))
    row_id = str(row["id"])

    with st.container(border=True):
        head_l, head_r = st.columns([3, 1], vertical_alignment="center")
        with head_l:
            st.markdown(f"**{tipo_icon(tipo)} {atividade}**")
            st.caption(f"{cidade} · {tipo}")
        with head_r:
            st.html(status_badge_html(status))

        if descricao and not compact:
            st.markdown(f'<p class="et-card-desc">{escape(descricao)}</p>', unsafe_allow_html=True)
        elif descricao and compact:
            short = descricao if len(descricao) <= 90 else descricao[:87] + "…"
            st.caption(short)

        actions = st.container(horizontal=True)
        with actions:
            if status != "Confirmado":
                if st.button(
                    "Confirmar",
                    icon=":material/check:",
                    key=f"{key_prefix}_ok_{row_id}",
                    type="primary",
                ):
                    set_itinerario_status(row_id, "Confirmado", "Atividade confirmada.")
            if st.button("Editar", icon=":material/edit:", key=f"{key_prefix}_edit_{row_id}"):
                open_form_dialog("edit", "itinerario", "Itinerário", ITINERARIO_FIELDS, row=row)
            if status != "Cancelado":
                if st.button(
                    "Cancelar",
                    icon=":material/cancel:",
                    key=f"{key_prefix}_cancel_{row_id}",
                    type="tertiary",
                ):
                    set_itinerario_status(row_id, "Cancelado", "Atividade cancelada.")


def _fmt_date_short(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return "—"
        return value.strftime("%d/%m/%Y")
    return str(value)


def _fmt_money(value, moeda: str = "EUR") -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "—"
    symbol = {"EUR": "€", "BRL": "R$", "USD": "$"}.get(moeda, moeda + " ")
    if moeda in {"EUR", "BRL", "USD"}:
        return f"{symbol} {n:,.0f}".replace(",", ".")
    return f"{n:,.0f} {moeda}"


def plain_badge_html(label: str, *, kind: str = "ok") -> str:
    """Badge simples para estados pago/pendente/concluído."""
    if is_dark_mode():
        styles = {
            "ok": ("#BBF7D0", "#14532D", "#4ADE80"),
            "warn": ("#FDE68A", "#78350F", "#FBBF24"),
            "off": ("#D1DAD6", "#1F2C27", "#3A4A44"),
        }
    else:
        styles = {
            "ok": ("#166534", "#DCFCE7", "#86EFAC"),
            "warn": ("#92400E", "#FEF3C7", "#FCD34D"),
            "off": ("#57534E", "#F4F6F5", "#E2E5E4"),
        }
    color, bg, border = styles.get(kind, styles["off"])
    return (
        f'<span class="et-badge" style="color:{color};background:{bg};'
        f'border-color:{border};">{escape(label)}</span>'
    )


def _card_toolbar(table: str, label: str, fields: list[dict], count: int) -> None:
    left, right = st.columns([2, 1], vertical_alignment="center")
    with left:
        st.caption(f"{count} item(ns) nesta vista")
    with right:
        if st.button("Adicionar", icon=":material/add:", key=f"{table}_add", type="primary", width="stretch"):
            open_form_dialog("add", table, label, fields)


def _card_actions(
    table: str,
    label: str,
    fields: list[dict],
    row: pd.Series,
    display_fn,
    *,
    quick_action: dict | None = None,
) -> None:
    row_id = str(row["id"])
    with st.container(horizontal=True):
        if quick_action is not None:
            show = quick_action.get("when", lambda _r: True)
            if show(row):
                if st.button(
                    quick_action["label"],
                    icon=quick_action.get("icon"),
                    key=f"{table}_qa_{row_id}",
                    type="primary",
                ):
                    db.update_row(
                        table,
                        row_id,
                        {quick_action["field"]: quick_action["value"]},
                    )
                    st.toast(quick_action["toast"], icon=":material/check_circle:")
                    st.rerun()
        if st.button("Editar", icon=":material/edit:", key=f"{table}_edit_{row_id}"):
            open_form_dialog("edit", table, label, fields, row=row)
        if st.button("Excluir", icon=":material/delete:", key=f"{table}_del_{row_id}", type="tertiary"):
            open_delete_dialog(table, label, pd.DataFrame([row.to_dict()]), display_fn)


def render_crud_cards(
    table: str,
    label: str,
    view_df: pd.DataFrame,
    fields: list[dict],
    display_fn,
    *,
    title_fn,
    lines_fn,
    badge_fn=None,
    icon_fn=None,
    quick_action: dict | None = None,
    columns: int = 1,
) -> None:
    """Lista de cards com adicionar / editar / excluir / ação rápida — sem tabelas."""
    inject_roteiro_css()
    _card_toolbar(table, label, fields, len(view_df))

    if view_df.empty:
        st.html(
            '<div class="et-empty">'
            f"<strong>Nada por aqui ainda</strong>"
            f"Toque em Adicionar para criar o primeiro item de {escape(label)}."
            "</div>"
        )
        return

    rows = list(view_df.iterrows())
    ncols = max(1, min(columns, 3))

    for i in range(0, len(rows), ncols):
        chunk = rows[i : i + ncols]
        cols = st.columns(len(chunk), gap="medium")
        for col, (_, row) in zip(cols, chunk):
            with col:
                title = title_fn(row)
                icon = icon_fn(row) if icon_fn else ""
                with st.container(border=True):
                    head_l, head_r = st.columns([3, 1], vertical_alignment="top")
                    with head_l:
                        st.markdown(f"**{icon} {title}**".strip() if icon else f"**{title}**")
                    with head_r:
                        if badge_fn is not None:
                            badge = badge_fn(row)
                            if badge:
                                st.html(badge)

                    for line in lines_fn(row):
                        if line:
                            st.caption(line)

                    _card_actions(
                        table,
                        label,
                        fields,
                        row,
                        display_fn,
                        quick_action=quick_action,
                    )


# Mantido como alias por compatibilidade interna
def render_crud_table(*args, **kwargs):
    raise RuntimeError("Use render_crud_cards — tabelas foram substituídas por cards.")

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
</style>
"""


def inject_roteiro_css() -> None:
    """Injeta CSS do Roteiro uma vez por sessão de página."""
    st.html(ROTEIRO_CSS)


def status_badge_html(status: str) -> str:
    meta = STATUS_META.get(status, STATUS_META["Sugestão - validar"])
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


def render_crud_table(
    table: str,
    label: str,
    view_df: pd.DataFrame,
    column_config: dict,
    fields: list[dict],
    display_fn,
    bulk_action: dict | None = None,
    height: int | None = None,
) -> None:
    """Tabela somente-leitura com seleção de linhas + barra de ações
    (adicionar / editar / excluir / ação em massa)."""
    dataframe_kwargs = {}
    if height is not None:
        dataframe_kwargs["height"] = height

    event = st.dataframe(
        view_df,
        column_config=column_config,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
        key=f"{table}_select",
        **dataframe_kwargs,
    )
    selected_idx = event.selection.rows
    selected_rows = view_df.iloc[selected_idx] if selected_idx else view_df.iloc[0:0]
    n_sel = len(selected_rows)

    with st.container(horizontal=True):
        if st.button("Adicionar", icon=":material/add:", key=f"{table}_add", type="primary"):
            open_form_dialog("add", table, label, fields)
        if st.button("Editar", icon=":material/edit:", key=f"{table}_edit", disabled=n_sel != 1):
            open_form_dialog("edit", table, label, fields, row=selected_rows.iloc[0])
        if st.button("Excluir", icon=":material/delete:", key=f"{table}_delete", disabled=n_sel == 0):
            open_delete_dialog(table, label, selected_rows, display_fn)
        if bulk_action is not None:
            if st.button(
                bulk_action["label"], icon=bulk_action.get("icon"), key=f"{table}_bulk", disabled=n_sel == 0
            ):
                db.update_rows(table, list(selected_rows["id"]), bulk_action["field"], bulk_action["value"])
                _reset_selection(table)
                st.toast(bulk_action["toast"], icon=":material/check_circle:")
                st.rerun()

    st.caption(f"{n_sel} selecionado(s) · {len(view_df)} exibido(s)")

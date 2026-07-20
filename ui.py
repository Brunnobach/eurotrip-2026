"""Componentes de CRUD reutilizáveis: tabela com seleção + adicionar/editar/excluir
via diálogos com formulário (em vez de edição direta de células de grade)."""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

import db


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

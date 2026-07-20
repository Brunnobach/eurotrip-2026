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


EUR = "€ %.2f"


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

    roteiro.render_roteiro(it_f, tr_f, ho_f)

# --- ITINERÁRIO ---
with tabs[1]:
    filtered = apply_cidade_filter(itinerario, ["cidade"], cidade_filtro)
    filtered = apply_period_filter(filtered, ["data"], periodo_ini, periodo_fim)

    itinerario_config = {
        "id": st.column_config.TextColumn("Código", width="small"),
        "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
        "cidade": st.column_config.TextColumn("Cidade"),
        "pais": st.column_config.TextColumn("País"),
        "atividade": st.column_config.TextColumn("Atividade", width="large"),
        "tipo": st.column_config.TextColumn("Tipo"),
        "descricao": st.column_config.TextColumn("Descrição", width="large"),
        "status": st.column_config.TextColumn("Status"),
    }
    ui.render_crud_table(
        "itinerario",
        "Itinerário",
        filtered,
        itinerario_config,
        ui.ITINERARIO_FIELDS,
        display_fn=lambda r: f"{r['data']:%d/%m} — {r['atividade']} ({r['cidade']})",
        bulk_action=dict(
            label="Marcar confirmado",
            icon=":material/check:",
            field="status",
            value="Confirmado",
            toast="Itens marcados como confirmados.",
        ),
    )

    st.bar_chart(itinerario.groupby("pais").size(), x_label="País", y_label="Atividades")

# --- TRANSPORTES ---
with tabs[2]:
    filtered = apply_cidade_filter(transportes, ["origem", "destino"], cidade_filtro)
    filtered = apply_period_filter(filtered, ["data"], periodo_ini, periodo_fim)

    transportes_config = {
        "id": st.column_config.TextColumn("Código", width="small"),
        "tipo": st.column_config.TextColumn("Tipo"),
        "origem": st.column_config.TextColumn("Origem"),
        "destino": st.column_config.TextColumn("Destino"),
        "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
        "hora_saida": st.column_config.TextColumn("Saída"),
        "hora_chegada": st.column_config.TextColumn("Chegada"),
        "status": st.column_config.TextColumn("Status"),
        "duracao": st.column_config.TextColumn("Duração", width="small"),
    }
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
    ui.render_crud_table(
        "transportes",
        "Transportes",
        filtered,
        transportes_config,
        transportes_fields,
        display_fn=lambda r: f"{r['origem']} → {r['destino']} ({r['data']:%d/%m})",
        bulk_action=dict(
            label="Marcar confirmado",
            icon=":material/check:",
            field="status",
            value="Confirmado",
            toast="Trechos marcados como confirmados.",
        ),
    )

# --- HOSPEDAGEM ---
with tabs[3]:
    filtered = apply_cidade_filter(hospedagem, ["cidade"], cidade_filtro)
    filtered = apply_period_filter(filtered, ["checkin", "checkout"], periodo_ini, periodo_fim)

    hospedagem_config = {
        "id": st.column_config.TextColumn("Código", width="small"),
        "cidade": st.column_config.TextColumn("Cidade"),
        "nome": st.column_config.TextColumn("Hotel / acomodação", width="large"),
        "checkin": st.column_config.DateColumn("Check-in", format="DD/MM/YYYY"),
        "checkout": st.column_config.DateColumn("Check-out", format="DD/MM/YYYY"),
        "horario_checkin": st.column_config.TextColumn("Horário check-in", width="small"),
        "observacoes": st.column_config.TextColumn("Observações", width="large"),
    }
    hospedagem_fields = [
        dict(key="cidade", label="Cidade", type="text"),
        dict(key="nome", label="Hotel / acomodação", type="text", default="A definir"),
        dict(key="checkin", label="Check-in", type="date", default=date(2026, 8, 6)),
        dict(key="checkout", label="Check-out", type="date", default=date(2026, 8, 7)),
        dict(key="horario_checkin", label="Horário check-in", type="text", help="Formato HH:MM", default="15:00"),
        dict(key="observacoes", label="Observações", type="textarea"),
    ]
    ui.render_crud_table(
        "hospedagem",
        "Hospedagem",
        filtered,
        hospedagem_config,
        hospedagem_fields,
        display_fn=lambda r: f"{r['cidade']} — {r['nome']}",
    )

    noites_total = int((hospedagem["checkout"] - hospedagem["checkin"]).dt.days.sum())
    st.metric("Total de noites no roteiro", noites_total, border=True)

# --- ATRAÇÕES ---
with tabs[4]:
    filtered = apply_cidade_filter(atracoes, ["cidade"], cidade_filtro)

    atracoes_config = {
        "id": st.column_config.TextColumn("Código", width="small"),
        "nome": st.column_config.TextColumn("Atração", width="large"),
        "cidade": st.column_config.TextColumn("Cidade"),
        "tipo": st.column_config.TextColumn("Tipo"),
        "necessita_ingresso": st.column_config.CheckboxColumn("Ingresso?"),
        "preco_eur": st.column_config.NumberColumn("Preço (EUR)", format=EUR),
        "horario_marcado": st.column_config.TextColumn("Horário marcado"),
        "duracao_estimada": st.column_config.TextColumn("Duração estimada", width="small"),
    }
    atracoes_fields = [
        dict(key="nome", label="Atração", type="text"),
        dict(key="cidade", label="Cidade", type="text"),
        dict(key="tipo", label="Tipo", type="select", options=["Ponto turístico", "Museu", "Passeio", "Memorial/Museu", "Outro"], default="Ponto turístico"),
        dict(key="necessita_ingresso", label="Necessita ingresso?", type="checkbox", default=True),
        dict(key="preco_eur", label="Preço (EUR)", type="number", step=0.5),
        dict(key="horario_marcado", label="Horário marcado", type="text", default="A definir"),
        dict(key="duracao_estimada", label="Duração estimada", type="text", help="Ex.: 1h30"),
    ]
    ui.render_crud_table(
        "atracoes",
        "Atrações",
        filtered,
        atracoes_config,
        atracoes_fields,
        display_fn=lambda r: f"{r['nome']} ({r['cidade']})",
    )

# --- FINANCEIRO ---
with tabs[5]:
    financeiro_config = {
        "id": st.column_config.TextColumn("Código", width="small"),
        "categoria": st.column_config.TextColumn("Categoria"),
        "item": st.column_config.TextColumn("Item", width="large"),
        "valor_estimado": st.column_config.NumberColumn("Valor estimado", format=EUR),
        "valor_real": st.column_config.NumberColumn("Valor real", format=EUR),
        "moeda": st.column_config.TextColumn("Moeda"),
        "pago": st.column_config.CheckboxColumn("Pago?"),
    }
    financeiro_fields = [
        dict(key="categoria", label="Categoria", type="select", options=["Passeio", "Hospedagem", "Transporte", "Alimentação", "Outro"], default="Passeio"),
        dict(key="item", label="Item", type="text"),
        dict(key="valor_estimado", label="Valor estimado", type="number", step=1.0),
        dict(key="valor_real", label="Valor real", type="number", step=1.0),
        dict(key="moeda", label="Moeda", type="select", options=["EUR", "BRL", "USD", "PLN", "ALL"], default="EUR"),
        dict(key="pago", label="Pago?", type="checkbox", default=False),
    ]
    ui.render_crud_table(
        "financeiro",
        "Financeiro",
        financeiro,
        financeiro_config,
        financeiro_fields,
        display_fn=lambda r: f"{r['item']} (€ {r['valor_estimado']:.0f})",
        bulk_action=dict(
            label="Marcar pago",
            icon=":material/paid:",
            field="pago",
            value=True,
            toast="Itens marcados como pagos.",
        ),
    )

    fc1, fc2, fc3 = st.columns(3)
    fc1.metric("Total estimado", f"€ {financeiro['valor_estimado'].sum(skipna=True):,.0f}", border=True)
    fc2.metric("Total gasto real", f"€ {financeiro['valor_real'].sum(skipna=True):,.0f}", border=True)
    fc3.metric("Itens pagos", f"{int(financeiro['pago'].sum())} / {len(financeiro)}", border=True)

    st.bar_chart(
        financeiro.groupby("categoria")["valor_estimado"].sum(),
        x_label="Categoria",
        y_label="Valor estimado (EUR)",
    )

# --- CHECKLIST ---
with tabs[6]:
    checklist_config = {
        "id": st.column_config.TextColumn("Código", width="small"),
        "categoria": st.column_config.TextColumn("Categoria"),
        "item": st.column_config.TextColumn("Item", width="large"),
        "concluido": st.column_config.CheckboxColumn("Concluído?"),
    }
    checklist_fields = [
        dict(key="categoria", label="Categoria", type="select", options=["Documentos", "Medicamentos", "Bagagem", "Eletrônicos", "Financeiro", "Outro"], default="Documentos"),
        dict(key="item", label="Item", type="text"),
        dict(key="concluido", label="Concluído?", type="checkbox", default=False),
    ]
    ui.render_crud_table(
        "checklist",
        "Checklist",
        checklist,
        checklist_config,
        checklist_fields,
        display_fn=lambda r: r["item"],
        bulk_action=dict(
            label="Marcar concluído",
            icon=":material/check:",
            field="concluido",
            value=True,
            toast="Itens marcados como concluídos.",
        ),
    )

    pendentes_check = int((~checklist["concluido"]).sum())
    st.progress(1 - pendentes_check / max(len(checklist), 1))
    st.caption(f"{pendentes_check} de {len(checklist)} itens pendentes")

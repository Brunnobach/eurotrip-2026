
# ============================================================================
# EUROTRIP 2026 — App Streamlit (dados embutidos, funciona offline)
# Rodar com: streamlit run app.py
# ============================================================================
import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="EUROTRIP 2026", page_icon="🗺️", layout="wide")

@st.cache_data
def load_data():
    itinerario = pd.read_csv(io.StringIO(ITINERARIO_CSV), parse_dates=["Data"])
    transportes = pd.read_csv(io.StringIO(TRANSPORTES_CSV), parse_dates=["Data"])
    hospedagem = pd.read_csv(io.StringIO(HOSPEDAGEM_CSV), parse_dates=["Check-in", "Check-out"])
    atracoes = pd.read_csv(io.StringIO(ATRACOES_CSV))
    financeiro = pd.read_csv(io.StringIO(FINANCEIRO_CSV))
    checklist = pd.read_csv(io.StringIO(CHECKLIST_CSV))
    return itinerario, transportes, hospedagem, atracoes, financeiro, checklist

itinerario, transportes, hospedagem, atracoes, financeiro, checklist = load_data()

def parse_valor(v):
    if pd.isna(v):
        return 0.0
    s = str(v).split("(")[0].strip().replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0

financeiro["Valor Estimado (num)"] = financeiro["Valor Estimado"].apply(parse_valor)

st.title("🗺️ EUROTRIP 2026 — Painel de Controle")
st.caption("Itália · França · Luxemburgo · Alemanha · Polônia · Albânia — 30 dias (06/08 a 04/09/2026)")

confirmados = (itinerario["Status"] == "Confirmado").sum()
sugeridos = (itinerario["Status"] == "Sugestão - validar").sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Dias de viagem", 30)
c2.metric("Países", 6)
c3.metric("Atividades", len(itinerario))
c4.metric("Confirmados", int(confirmados))
c5.metric("Orçamento estimado (EUR)", f"{financeiro['Valor Estimado (num)'].sum():,.0f}")

tabs = st.tabs([
    "🗺️ Itinerário", "🚗 Transportes", "🏨 Hospedagem",
    "🎟️ Atrações", "💸 Financeiro", "🎒 Checklist"
])

# --- ITINERARIO ---
with tabs[0]:
    st.subheader("Itinerário completo")
    colf1, colf2, colf3 = st.columns(3)
    paises = colf1.multiselect("País", sorted(itinerario["País"].unique()), default=list(itinerario["País"].unique()))
    status_f = colf2.multiselect("Status", sorted(itinerario["Status"].unique()), default=list(itinerario["Status"].unique()))
    tipo_f = colf3.multiselect("Tipo", sorted(itinerario["Tipo"].unique()), default=list(itinerario["Tipo"].unique()))
    filtered = itinerario[
        itinerario["País"].isin(paises) & itinerario["Status"].isin(status_f) & itinerario["Tipo"].isin(tipo_f)
    ]
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.caption(f"{len(filtered)} de {len(itinerario)} atividades exibidas.")
    st.bar_chart(itinerario.groupby("País").size())

# --- TRANSPORTES ---
with tabs[1]:
    st.subheader("Transportes")
    st.dataframe(transportes, use_container_width=True, hide_index=True)
    st.caption("Duração calculada automaticamente a partir da hora de saída/chegada.")

# --- HOSPEDAGEM ---
with tabs[2]:
    st.subheader("Hospedagem")
    hosp = hospedagem.copy()
    hosp["Noites"] = (hosp["Check-out"] - hosp["Check-in"]).dt.days
    st.dataframe(hosp, use_container_width=True, hide_index=True)
    st.metric("Total de noites no roteiro", int(hosp["Noites"].sum()))

# --- ATRACOES ---
with tabs[3]:
    st.subheader("Atrações")
    cidade_f = st.multiselect("Cidade", sorted(atracoes["Cidade"].unique()), default=list(atracoes["Cidade"].unique()))
    st.dataframe(atracoes[atracoes["Cidade"].isin(cidade_f)], use_container_width=True, hide_index=True)

# --- FINANCEIRO ---
with tabs[4]:
    st.subheader("Controle financeiro")
    st.caption("Edite 'Valor Real' e 'Pago?' conforme for gastando. Os totais abaixo são recalculados automaticamente.")
    edited = st.data_editor(
        financeiro.drop(columns=["Valor Estimado (num)"]),
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key="fin_editor",
    )
    total_est = financeiro["Valor Estimado (num)"].sum()
    edited["_valor_real_num"] = edited["Valor Real"].apply(parse_valor)
    total_real = edited["_valor_real_num"].sum()
    fc1, fc2, fc3 = st.columns(3)
    fc1.metric("Total estimado (EUR)", f"{total_est:,.0f}")
    fc2.metric("Total gasto real (EUR)", f"{total_real:,.0f}")
    fc3.metric("Diferença", f"{total_real - total_est:,.0f}")
    st.bar_chart(financeiro.groupby("Categoria")["Valor Estimado (num)"].sum())

# --- CHECKLIST ---
with tabs[5]:
    st.subheader("Checklist de viagem")
    edited_check = st.data_editor(checklist, use_container_width=True, hide_index=True, key="check_editor")
    pendentes = (edited_check["Status"] == "Pendente").sum()
    st.metric("Itens pendentes", int(pendentes))
    st.progress(1 - pendentes / max(len(edited_check), 1))

st.divider()
st.caption("Gerado a partir do roteiro bruto EUROTRIP 2026. Trechos com status 'Sugestão - validar' são rascunhos propostos — confirme datas, preços e disponibilidade antes de reservar.")

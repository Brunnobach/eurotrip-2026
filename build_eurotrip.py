# -*- coding: utf-8 -*-
"""
EUROTRIP 2026 - Gerador do sistema de tabelas relacionadas
Cria: CSVs individuais + pickle de dados para o workbook Excel e o app Streamlit
"""
import pandas as pd
from datetime import datetime

OUT = "/sessions/intelligent-festive-noether/mnt/outputs"

# ---------------------------------------------------------------------------
# 1) ITINERARIO
# CONFIRMADO = veio do documento original / SUGESTAO = rascunho proposto (a validar)
# ---------------------------------------------------------------------------
itinerario = [
    ("IT-01","2026-08-06","Milão","Itália","Chegada (voo/trem internacional)","Deslocamento","Chegada a Milão - conferir bilhete de trem/avião até a cidade","Confirmado"),
    ("IT-02","2026-08-06","Milão","Itália","Duomo di Milano + terraço","Turismo","Comprar ingresso com acesso ao terraço","Confirmado"),
    ("IT-03","2026-08-06","Milão","Itália","Galleria Vittorio Emanuele II","Turismo","Passagem pela galeria - acesso gratuito","Confirmado"),
    ("IT-04","2026-08-06","Milão","Itália","Santa Maria delle Grazie (A Última Ceia)","Turismo","Ingresso com horário marcado no site do museu - 15 EUR","Confirmado"),
    ("IT-05","2026-08-06","Milão","Itália","Castello Sforzesco","Turismo","Pátio gratuito; museus internos com ingresso à parte","Confirmado"),
    ("IT-06","2026-08-06","Milão","Itália","Museu Leonardo da Vinci (Ciência e Tecnologia)","Turismo","Comprar ingresso - 10 EUR","Confirmado"),
    ("IT-07","2026-08-07","Milão","Itália","Dia livre / compras / restaurantes","Descanso","Dia livre em Milão","Confirmado"),
    ("IT-08","2026-08-08","Lago di Garda","Itália","Estadia Lago di Garda (dia 1)","Turismo","Passeio pela região do lago","Confirmado"),
    ("IT-09","2026-08-09","Lago di Garda","Itália","Estadia Lago di Garda (dia 2)","Turismo","Passeio pela região do lago","Confirmado"),
    ("IT-10","2026-08-10","Sorrento","Itália","Trem Pordenone -> Veneza (07:21-08:27)","Deslocamento","Ver tabela Transportes","Confirmado"),
    ("IT-11","2026-08-10","Sorrento","Itália","Voo Veneza -> Nápoles (15:05-16:25)","Deslocamento","Ver tabela Transportes","Confirmado"),
    ("IT-12","2026-08-10","Sorrento","Itália","Check-in Hotel Sorrento Coast Suites","Deslocamento","Check-in a partir das 14h","Confirmado"),
    ("IT-13","2026-08-11","Positano","Itália","Passeio em Positano","Turismo","Bate-volta a partir de Sorrento (barco ou ônibus SITA)","Sugestão - validar"),
    ("IT-14","2026-08-12","Amalfi","Itália","Passeio em Amalfi","Turismo","Bate-volta a partir de Sorrento (barco recomendado)","Sugestão - validar"),
    ("IT-15","2026-08-13","Capri","Itália","Passeio de barco a Capri","Turismo","Grotta Azzurra, Marina Piccola, teleférico Monte Solaro","Sugestão - validar"),
    ("IT-16","2026-08-14","Pompeia","Itália","Sítio arqueológico de Pompeia/Herculano","Turismo","Trem Circumvesuviana a partir de Sorrento","Sugestão - validar"),
    ("IT-17","2026-08-15","Roma","Itália","Deslocamento Sorrento/Nápoles -> Roma","Deslocamento","Trem regional + Frecciarossa via Nápoles","Sugestão - validar"),
    ("IT-18","2026-08-16","Roma","Itália","Coliseu + Fórum Romano + Palatino","Turismo","Ingresso combinado - reservar com antecedência","Sugestão - validar"),
    ("IT-19","2026-08-17","Roma","Itália","Museus Vaticanos + Capela Sistina + Basílica de São Pedro","Turismo","Reservar horário online","Sugestão - validar"),
    ("IT-20","2026-08-18","Florença","Itália","Deslocamento Roma -> Florença","Deslocamento","Trem de alta velocidade (~1h30)","Sugestão - validar"),
    ("IT-21","2026-08-19","Florença","Itália","Duomo di Firenze + Uffizi + Ponte Vecchio","Turismo","Reservar Uffizi com antecedência (fila grande)","Sugestão - validar"),
    ("IT-22","2026-08-20","Milão","Itália","Deslocamento Florença -> Milão (buffer pré-voo)","Deslocamento","Dia-tampão antes do voo para Paris","Sugestão - validar"),
    ("FR-01","2026-08-21","Paris","França","Voo Milão -> Paris + check-in","Deslocamento","Fim da Itália / chegada à França","Sugestão - validar"),
    ("FR-02","2026-08-22","Paris","França","Torre Eiffel + Champs-Élysées + Arco do Triunfo","Turismo","Reservar horário da Torre Eiffel online","Sugestão - validar"),
    ("FR-03","2026-08-23","Paris","França","Museu do Louvre + Montmartre/Sacré-Cœur","Turismo","Reservar Louvre com antecedência","Sugestão - validar"),
    ("FR-04","2026-08-24","Versalhes","França","Palácio de Versalhes (bate-volta)","Turismo","Trem RER C a partir de Paris (~1h)","Sugestão - validar"),
    ("LU-01","2026-08-25","Luxemburgo","Luxemburgo","Deslocamento Paris -> Luxemburgo + city tour","Deslocamento","Trem direto (~2h10); Casemates, Palácio Grão-Ducal","Sugestão - validar"),
    ("DE-01","2026-08-26","Colônia","Alemanha","Deslocamento Luxemburgo -> Colônia + Catedral de Colônia","Deslocamento","Trem (~2h30)","Sugestão - validar"),
    ("DE-02","2026-08-27","Colônia","Alemanha","Dia livre / passeio às margens do Reno","Descanso","Dia livre em Colônia","Sugestão - validar"),
    ("DE-03","2026-08-28","Berlim","Alemanha","Deslocamento Colônia -> Berlim","Deslocamento","Trem ICE (~4h30)","Sugestão - validar"),
    ("DE-04","2026-08-29","Berlim","Alemanha","Portão de Brandemburgo + East Side Gallery + Museum Island","Turismo","Portão e East Side Gallery são gratuitos (área externa)","Sugestão - validar"),
    ("PL-01","2026-08-30","Cracóvia","Polônia","Deslocamento Berlim -> Cracóvia","Deslocamento","Trem (~7h, via Wroclaw ou EuroCity direto)","Sugestão - validar"),
    ("PL-02","2026-08-31","Cracóvia","Polônia","Old Town + Wawel Castle + Kazimierz","Turismo","Bairro judeu Kazimierz e Praça do Mercado","Sugestão - validar"),
    ("PL-03","2026-09-01","Auschwitz-Birkenau","Polônia","Visita guiada a Auschwitz-Birkenau","Turismo","Reservar guia oficial com 1 mês de antecedência","Sugestão - validar"),
    ("AL-01","2026-09-02","Tirana","Albânia","Voo Cracóvia -> Tirana + check-in","Deslocamento","Voo direto Ryanair/Wizz Air (~1h50)","Sugestão - validar"),
    ("AL-02","2026-09-03","Tirana","Albânia","City tour + Bunk'Art + Praça Skanderbeg","Turismo","Museu Bunk'Art (bunker da era comunista)","Sugestão - validar"),
    ("AL-03","2026-09-04","Tirana","Albânia","Dia livre / compras / voo de volta","Descanso","Último dia - conferir horário do voo de retorno","Sugestão - validar"),
]
df_itinerario = pd.DataFrame(itinerario, columns=[
    "ID","Data","Cidade","País","Atividade","Tipo","Descrição","Status"
])

# ---------------------------------------------------------------------------
# 2) TRANSPORTES
# ---------------------------------------------------------------------------
transportes = [
    ("TR-01","Voo","Brasil","Milão","2026-08-06","","","Confirmado"),
    ("TR-02","Trem","Pordenone","Veneza","2026-08-10","07:21","08:27","Confirmado"),
    ("TR-03","Voo","Veneza","Nápoles","2026-08-10","15:05","16:25","Confirmado"),
    ("TR-04","Barco","Sorrento","Capri (ida e volta)","2026-08-13","09:00","18:00","Sugestão - validar"),
    ("TR-05","Trem","Sorrento/Nápoles","Roma","2026-08-15","08:00","10:40","Sugestão - validar"),
    ("TR-06","Trem","Roma","Florença","2026-08-18","09:00","10:30","Sugestão - validar"),
    ("TR-07","Trem","Florença","Milão","2026-08-20","09:00","10:50","Sugestão - validar"),
    ("TR-08","Voo","Milão","Paris","2026-08-21","18:00","19:40","Sugestão - validar"),
    ("TR-09","Trem","Paris","Luxemburgo","2026-08-25","09:00","11:10","Sugestão - validar"),
    ("TR-10","Trem","Luxemburgo","Colônia","2026-08-26","09:00","11:30","Sugestão - validar"),
    ("TR-11","Trem","Colônia","Berlim","2026-08-28","09:00","13:30","Sugestão - validar"),
    ("TR-12","Trem","Berlim","Cracóvia","2026-08-30","08:00","15:00","Sugestão - validar"),
    ("TR-13","Voo","Cracóvia","Tirana","2026-09-02","05:40","07:30","Sugestão - validar"),
    ("TR-14","Voo","Tirana","Brasil","2026-09-04","23:00","","Sugestão - validar"),
]
df_transportes = pd.DataFrame(transportes, columns=[
    "ID","Tipo","Origem","Destino","Data","Hora Saída","Hora Chegada","Status"
])

def calc_duracao(row):
    hs, hc = row["Hora Saída"], row["Hora Chegada"]
    if not hs or not hc:
        return ""
    try:
        t1 = datetime.strptime(hs, "%H:%M")
        t2 = datetime.strptime(hc, "%H:%M")
        delta = t2 - t1
        if delta.total_seconds() < 0:
            delta += pd.Timedelta(days=1)
        total_min = int(delta.total_seconds() // 60)
        return f"{total_min//60}h{total_min%60:02d}"
    except Exception:
        return ""

df_transportes["Duração"] = df_transportes.apply(calc_duracao, axis=1)

# ---------------------------------------------------------------------------
# 3) HOSPEDAGEM
# ---------------------------------------------------------------------------
hospedagem = [
    ("H-01","Milão","A definir","2026-08-06","2026-08-08","15:00","2 noites - próximo ao Duomo/metrô recomendado"),
    ("H-02","Lago di Garda","A definir","2026-08-08","2026-08-10","15:00","2 noites - base em Pordenone/Peschiera"),
    ("H-03","Sorrento","Hotel Sorrento Coast Suites","2026-08-10","2026-08-15","14:00","5 noites - base p/ Positano, Amalfi, Capri, Pompeia (confirmado)"),
    ("H-04","Roma","A definir","2026-08-15","2026-08-18","15:00","3 noites - próximo a estação Termini recomendado"),
    ("H-05","Florença","A definir","2026-08-18","2026-08-20","15:00","2 noites - próximo ao centro histórico"),
    ("H-06","Milão","A definir (hotel aeroporto/buffer)","2026-08-20","2026-08-21","15:00","1 noite - dia-tampão antes do voo p/ Paris"),
    ("H-07","Paris","A definir","2026-08-21","2026-08-25","15:00","4 noites"),
    ("H-08","Luxemburgo","A definir","2026-08-25","2026-08-26","15:00","1 noite"),
    ("H-09","Colônia","A definir","2026-08-26","2026-08-28","15:00","2 noites"),
    ("H-10","Berlim","A definir","2026-08-28","2026-08-30","15:00","2 noites"),
    ("H-11","Cracóvia","A definir","2026-08-30","2026-09-02","15:00","3 noites"),
    ("H-12","Tirana","A definir","2026-09-02","2026-09-04","14:00","2 noites - último trecho da viagem"),
]
df_hospedagem = pd.DataFrame(hospedagem, columns=[
    "ID","Cidade","Nome","Check-in","Check-out","Horário Check-in","Observações"
])

# ---------------------------------------------------------------------------
# 4) ATRAÇÕES
# ---------------------------------------------------------------------------
atracoes = [
    ("AT-01","Duomo di Milano + terraço","Milão","Ponto turístico","Sim","20 (estimado)","A definir","1h30"),
    ("AT-02","Galleria Vittorio Emanuele II","Milão","Ponto turístico","Não","0","-","0h30"),
    ("AT-03","Santa Maria delle Grazie (A Última Ceia)","Milão","Museu","Sim","15","Com horário marcado","0h30"),
    ("AT-04","Castello Sforzesco (pátio)","Milão","Ponto turístico","Não","0","-","1h00"),
    ("AT-05","Museu Leonardo da Vinci","Milão","Museu","Sim","10","A definir","2h00"),
    ("AT-06","Positano (passeio)","Positano","Passeio","Não","0 (transporte à parte)","-","4h00"),
    ("AT-07","Amalfi (passeio)","Amalfi","Passeio","Não","0 (transporte à parte)","-","4h00"),
    ("AT-08","Capri - barco + funicular","Capri","Passeio","Sim","40 (estimado)","A definir","8h00"),
    ("AT-09","Pompeia (sítio arqueológico)","Pompeia","Museu","Sim","18 (estimado)","A definir","3h00"),
    ("AT-10","Coliseu + Fórum Romano + Palatino","Roma","Ponto turístico","Sim","18","A definir","3h00"),
    ("AT-11","Museus Vaticanos + Capela Sistina","Roma","Museu","Sim","20","A definir (reservar online)","3h00"),
    ("AT-12","Uffizi + Duomo Firenze","Florença","Museu","Sim","25 (estimado)","A definir (reservar online)","3h00"),
    ("AT-13","Torre Eiffel (cume)","Paris","Ponto turístico","Sim","36,70","A definir (reservar online)","2h00"),
    ("AT-14","Museu do Louvre","Paris","Museu","Sim","22 (estimado)","A definir (reservar online)","3h00"),
    ("AT-15","Palácio de Versalhes","Versalhes","Ponto turístico","Sim","21 (estimado)","A definir","4h00"),
    ("AT-16","Casemates + city tour","Luxemburgo","Ponto turístico","Sim","7 (estimado)","-","3h00"),
    ("AT-17","Catedral de Colônia","Colônia","Ponto turístico","Não (torre paga à parte)","0 / 6 (torre)","-","1h00"),
    ("AT-18","Portão de Brandemburgo + East Side Gallery","Berlim","Ponto turístico","Não","0","-","2h00"),
    ("AT-19","Museum Island (ex: Pergamon)","Berlim","Museu","Sim","19 (estimado)","A definir","2h30"),
    ("AT-20","Old Town + Wawel Castle","Cracóvia","Ponto turístico","Sim (interior do castelo)","15 (estimado)","A definir","3h00"),
    ("AT-21","Auschwitz-Birkenau (tour guiado)","Auschwitz","Memorial/Museu","Sim","150 PLN (~35 EUR)","Reservar com antecedência","7h00"),
    ("AT-22","Bunk'Art + city tour","Tirana","Museu","Sim","8 (estimado)","-","2h30"),
]
df_atracoes = pd.DataFrame(atracoes, columns=[
    "ID","Nome","Cidade","Tipo","Necessita Ingresso","Preço (EUR)","Horário Marcado","Duração Estimada"
])

# ---------------------------------------------------------------------------
# 5) CONTROLE FINANCEIRO
# ---------------------------------------------------------------------------
financeiro = []
fid = 1
def add_fin(cat, item, valor, moeda="EUR"):
    global fid
    financeiro.append((f"F-{fid:02d}", cat, item, valor, "", moeda, "Não"))
    fid += 1

for row in atracoes:
    nome, preco = row[1], row[5]
    if preco not in ("0","0 (transporte à parte)","-"):
        add_fin("Passeio", f"Ingresso - {nome}", preco)

hotel_estimates = {
    "H-01":("Milão",2,110), "H-02":("Lago di Garda",2,100), "H-03":("Sorrento",5,130),
    "H-04":("Roma",3,120), "H-05":("Florença",2,110), "H-06":("Milão",1,90),
    "H-07":("Paris",4,140), "H-08":("Luxemburgo",1,120), "H-09":("Colônia",2,100),
    "H-10":("Berlim",2,100), "H-11":("Cracóvia",3,70), "H-12":("Tirana",2,50),
}
for hid,(cidade,noites,diaria) in hotel_estimates.items():
    add_fin("Hospedagem", f"Hospedagem {cidade} ({noites} noites x ~{diaria} EUR/noite)", str(noites*diaria))

transporte_estimates = [
    ("Voo internacional Brasil -> Milão","900"),
    ("Trem Pordenone -> Veneza","15"),
    ("Voo Veneza -> Nápoles","80"),
    ("Barco Sorrento <-> Capri","40"),
    ("Trem Sorrento/Nápoles -> Roma","35"),
    ("Trem Roma -> Florença","45"),
    ("Trem Florença -> Milão","35"),
    ("Voo Milão -> Paris","90"),
    ("Trem Paris -> Luxemburgo","60"),
    ("Trem Luxemburgo -> Colônia","45"),
    ("Trem Colônia -> Berlim","70"),
    ("Trem Berlim -> Cracóvia","90"),
    ("Voo Cracóvia -> Tirana","60"),
    ("Voo Tirana -> Brasil (retorno)","950"),
]
for item, valor in transporte_estimates:
    add_fin("Transporte", item, valor)

alimentacao_estimates = [
    ("Alimentação - Itália (15 dias x ~45 EUR/dia)","675"),
    ("Alimentação - França (4 dias x ~50 EUR/dia)","200"),
    ("Alimentação - Luxemburgo (1 dia x ~50 EUR/dia)","50"),
    ("Alimentação - Alemanha (4 dias x ~40 EUR/dia)","160"),
    ("Alimentação - Polônia (3 dias x ~30 EUR/dia)","90"),
    ("Alimentação - Albânia (3 dias x ~25 EUR/dia)","75"),
]
for item, valor in alimentacao_estimates:
    add_fin("Alimentação", item, valor)

df_financeiro = pd.DataFrame(financeiro, columns=[
    "ID","Categoria","Item","Valor Estimado","Valor Real","Moeda","Pago?"
])

# ---------------------------------------------------------------------------
# 6) CHECKLIST DE VIAGEM
# ---------------------------------------------------------------------------
checklist = [
    ("Documentos","Passaporte válido (6+ meses)","Pendente"),
    ("Documentos","Visto Schengen (verificar necessidade)","Pendente"),
    ("Documentos","Seguro saúde internacional","OK"),
    ("Documentos","Cartão de vacinação internacional (febre amarela)","OK"),
    ("Documentos","Reservas de hotel impressas/salvas offline","Pendente"),
    ("Documentos","Reservas de ingressos com horário marcado","Pendente"),
    ("Medicamentos","Protetor solar","Pendente"),
    ("Medicamentos","Receita médica + bula dos remédios (dipirona não entra na bagagem)","Pendente"),
    ("Medicamentos","Kit básico (analgésico permitido, curativos)","Pendente"),
    ("Bagagem","Mala grande 20kg","OK"),
    ("Bagagem","Mochila 40x30x15 (bagagem de mão)","OK"),
    ("Bagagem","Saquinho de vedação transparente p/ líquidos (20x20 cm)","Pendente"),
    ("Bagagem","Frascos até 100ml cada (máx. 1L somado)","Pendente"),
    ("Bagagem","Embalagens travel size","Pendente"),
    ("Bagagem","Gancho para lacrar bolsa","Pendente"),
    ("Eletrônicos","Adaptador de tomada (padrão europeu tipo C/F)","Pendente"),
    ("Eletrônicos","Power bank","Pendente"),
    ("Eletrônicos","Chip/eSIM de internet internacional","OK"),
    ("Financeiro","Cartão de crédito internacional (avisar banco da viagem)","Pendente"),
    ("Financeiro","Trocar euros (dinheiro vivo para pequenas despesas)","Pendente"),
    ("Financeiro","Verificar necessidade de zloty (Polônia) e lek (Albânia)","Pendente"),
]
df_checklist = pd.DataFrame(checklist, columns=["Categoria","Item","Status"])

# ---------------------------------------------------------------------------
# EXPORTA CSVs
# ---------------------------------------------------------------------------
df_itinerario.to_csv(f"{OUT}/csv/01_itinerario.csv", index=False, encoding="utf-8-sig")
df_transportes.to_csv(f"{OUT}/csv/02_transportes.csv", index=False, encoding="utf-8-sig")
df_hospedagem.to_csv(f"{OUT}/csv/03_hospedagem.csv", index=False, encoding="utf-8-sig")
df_atracoes.to_csv(f"{OUT}/csv/04_atracoes.csv", index=False, encoding="utf-8-sig")
df_financeiro.to_csv(f"{OUT}/csv/05_financeiro.csv", index=False, encoding="utf-8-sig")
df_checklist.to_csv(f"{OUT}/csv/06_checklist.csv", index=False, encoding="utf-8-sig")

print("CSVs exportados.")
print(df_itinerario.shape, df_transportes.shape, df_hospedagem.shape, df_atracoes.shape, df_financeiro.shape, df_checklist.shape)

import pickle
with open(f"{OUT}/eurotrip_data.pkl","wb") as f:
    pickle.dump({
        "itinerario": df_itinerario, "transportes": df_transportes,
        "hospedagem": df_hospedagem, "atracoes": df_atracoes,
        "financeiro": df_financeiro, "checklist": df_checklist
    }, f)
print("Pickle salvo.")

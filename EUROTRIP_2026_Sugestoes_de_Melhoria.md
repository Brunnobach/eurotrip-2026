# EUROTRIP 2026 — Análise Arquitetural do Roteiro e Sugestões de Melhoria

## 1. Diagnóstico do input bruto

O documento original (`EUROTRIP 2026.docx`) contém dados **confirmados e completos apenas para Itália, 06–10/08** (Milão, Lago di Garda, transição para Sorrento) mais uma checklist de bagagem. Os outros ~20 dias — Itália 11–21/08, França, Luxemburgo, Alemanha, Polônia e Albânia — existem só como títulos de país, sem cidades, hotéis ou atividades. O sistema entregue trata esses dois blocos de forma diferente: linhas com `Status = Confirmado` vieram do seu documento; linhas com `Status = Sugestão - validar` são um rascunho que montei para fechar os 30 dias com uma rota geograficamente coerente (Milão → Sul da Itália → Roma/Florença → Paris → Luxemburgo → Colônia/Berlim → Cracóvia → Tirana). **Trate o segundo bloco como ponto de partida para edição, não como reserva.**

## 2. Riscos e inconsistências encontrados no bloco confirmado

**Conflito de datas em Lago di Garda.** O documento diz "08–10/08 estadia no Lago di Garda" e, separadamente, que no dia 10/08 você já sai de trem de Pordenone às 07h21. Ou seja, o dia 10 é simultaneamente "estadia" e "dia de saída" — na prática são só 2 noites (8 e 9), não 3. Ajustei o sistema para 2 noites; confirme se o hotel está reservado assim, para não pagar uma diária a mais ou perder o check-out.

**Zero buffer entre atividades de bagagem cultural e trem matinal.** Sair de Pordenone às 07h21 exige estar de pé ~06h00 se o hotel não for na própria estação. Se a última atividade combinada em Lago di Garda for à noite do dia 9, o risco de perder o trem é real — vale reservar hospedagem a <15 min da estação ou considerar um trem mais tardio.

**Janela curta Veneza → Nápoles → Sorrento.** O voo pousa em Nápoles às 16h25 e o check-in em Sorrento é "a partir das 14h" — folga de tempo automática, mas o trajeto Nápoles-Sorrento (trem Circumvesuviana ou táxi, ~1h) só começa depois de retirar bagagem, então chegada real ao hotel provavelmente só depois das 18h. Isso é administrável, mas **não sobra tempo para nenhum passeio no dia 10** — o sistema já reflete isso (dia 10 = 100% deslocamento).

## 3. Onde o roteiro rascunhado está sob risco (validar antes de reservar)

**Ritmo Colônia → Berlim → Cracóvia é o trecho mais apertado dos 30 dias:** 3 deslocamentos de trem de longa distância (2h30 + 4h30 + ~7h) em 5 dias, sem dia de descanso puro. Se o objetivo é descanso e não só "ver o máximo de cidades", vale cortar Colônia (fica frequentemente pulada em roteiros Alemanha-Polônia) e ganhar 1 dia extra em Berlim ou Cracóvia.

**Berlim–Cracóvia não tem trem direto rápido:** a via mais realista (~7h, com baldeação) é o gargalo logístico do roteiro. Alternativa: voo Berlim–Cracóvia (~1h15, companhias low-cost) libera um dia inteiro. Vale pesquisar preço mais perto da data.

**Polônia → Albânia é a única rota sem conexão terrestre direta viável** — por isso mantive como voo (Cracóvia–Tirana, ~1h50, Ryanair/Wizz Air, confirmado disponível várias vezes por semana). Esse é o trecho de maior certeza de que **voo é a única opção sensata**, então reserve esse cedo, pois preços de low-cost sobem conforme a data se aproxima.

**Auschwitz-Birkenau exige reserva de guia com ~1 mês de antecedência** — é o único item do roteiro sugerido com prazo de reserva rígido e vagas limitadas. Se for confirmar esse trecho, é o primeiro ingresso a comprar.

## 4. Pontos de decisão que só você resolve

1. **Confirmar ou substituir os últimos ~9 dias na Itália (11–21/08).** Propus Amalfi Coast + Roma + Florença por serem os destinos mais comuns nessa janela partindo de Sorrento, mas isso não veio do seu documento — se você já tinha outro plano em mente (ex: ficar mais tempo no Sul, ou pular Roma/Florença), me diga e eu reestruturo as 3 tabelas (Itinerário, Transportes, Hospedagem) de uma vez.
2. **Definir cidades específicas em França, Luxemburgo, Alemanha e Polônia.** Usei Paris/Versalhes, Luxemburgo Cidade, Colônia+Berlim e Cracóvia por serem os hubs mais lógicos de trem/voo na sequência, mas se você tem preferência (ex: Estrasburgo em vez de Paris, Munique em vez de Berlim), a estrutura do sistema já está pronta para receber a edição — é só substituir linhas nas 6 tabelas mantendo os IDs sequenciais.
3. **Número de viajantes.** O Controle Financeiro assume valores "por pessoa" — se vocês forem 2+ pessoas, multiplique a coluna "Valor Estimado" pelo número de viajantes (ou me diga a contagem e eu ajusto a tabela).

## 5. Sistema entregue

| Arquivo | Uso |
|---|---|
| `EUROTRIP_2026_Sistema.xlsx` | Fonte única de verdade — 6 abas inter-relacionadas + painel-resumo, com fórmulas (duração, noites, total financeiro) e dropdowns de status |
| `EUROTRIP_2026_CSVs.zip` | Um CSV por tabela — importar direto no Google Sheets (Arquivo → Importar) ou como base de datasource no Notion |
| `app.py` | App Streamlit standalone (dados embutidos, roda offline) — `pip install streamlit pandas && streamlit run app.py` |

Notion não está autorizado nesta sessão (conector requer login em Configurações do Claude); se quiser que eu crie as databases diretamente no seu workspace, autorize o conector Notion e eu populo tudo via API em vez de depender de import manual de CSV.

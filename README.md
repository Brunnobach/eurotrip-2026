# EUROTRIP 2026

Painel de controle da viagem Itália + Albânia (06/08 a 20/08/2026), feito em Streamlit.

A aba **Roteiro** é a visão principal: cards por dia (hotel + transportes + atividades)
ou colunas por cidade, com ações rápidas para confirmar/editar. As demais abas
continuam com tabelas CRUD para edição detalhada.

## Rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Precisa de um arquivo `.streamlit/secrets.toml` (não versionado) com:

```toml
[supabase]
url = "https://SEU-PROJETO.supabase.co"
key = "sua-anon-key"
```

## Dados

Os dados ficam em um banco Postgres no Supabase (tabelas `itinerario`, `transportes`,
`hospedagem`, `atracoes`, `financeiro`, `checklist`). Os CSVs em `csv/` são só o roteiro
original, usados para semear o banco na primeira execução ou ao clicar em
"Restaurar roteiro original" no app.

## Deploy (Streamlit Community Cloud)

1. Acesse [share.streamlit.io](https://share.streamlit.io) e entre com sua conta GitHub.
2. "New app" → escolha este repositório → arquivo principal `app.py`.
3. Em "Advanced settings" → "Secrets", cole o mesmo conteúdo do `.streamlit/secrets.toml`.
4. Deploy.

"""Persistência do EUROTRIP 2026 em Supabase (Postgres na nuvem).

Cada tabela do app (itinerário, transportes, hospedagem, atrações,
financeiro, checklist) mora em uma tabela homônima no Supabase. Operações
são feitas linha a linha (insert/update/delete) em vez de substituir a
tabela inteira, para permitir edição concorrente por mais de uma pessoa
sem que uma sobrescreva a outra. Na primeira execução (tabela vazia), o
Supabase é semeado a partir dos CSVs em ./csv (roteiro original).
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import streamlit as st
from supabase import Client, create_client

BASE_DIR = Path(__file__).parent
CSV_DIR = BASE_DIR / "csv"

TABLE_SPECS: dict[str, dict] = {
    "itinerario": {
        "csv": "01_itinerario.csv",
        "id_prefix": "IT",
        "columns": ["id", "data", "cidade", "pais", "atividade", "tipo", "descricao", "status"],
        "csv_columns": ["ID", "Data", "Cidade", "País", "Atividade", "Tipo", "Descrição", "Status"],
        "date_cols": ["data"],
        "bool_cols": [],
        "num_cols": [],
        "order_by": "data",
    },
    "transportes": {
        "csv": "02_transportes.csv",
        "id_prefix": "TR",
        "columns": ["id", "tipo", "origem", "destino", "data", "hora_saida", "hora_chegada", "status", "duracao"],
        "csv_columns": ["ID", "Tipo", "Origem", "Destino", "Data", "Hora Saída", "Hora Chegada", "Status", "Duração"],
        "date_cols": ["data"],
        "bool_cols": [],
        "num_cols": [],
        "order_by": "data",
    },
    "hospedagem": {
        "csv": "03_hospedagem.csv",
        "id_prefix": "H",
        "columns": ["id", "cidade", "nome", "checkin", "checkout", "horario_checkin", "observacoes"],
        "csv_columns": ["ID", "Cidade", "Nome", "Check-in", "Check-out", "Horário Check-in", "Observações"],
        "date_cols": ["checkin", "checkout"],
        "bool_cols": [],
        "num_cols": [],
        "order_by": "checkin",
    },
    "atracoes": {
        "csv": "04_atracoes.csv",
        "id_prefix": "AT",
        "columns": ["id", "nome", "cidade", "tipo", "necessita_ingresso", "preco_eur", "horario_marcado", "duracao_estimada"],
        "csv_columns": ["ID", "Nome", "Cidade", "Tipo", "Necessita Ingresso", "Preço (EUR)", "Horário Marcado", "Duração Estimada"],
        "date_cols": [],
        "bool_cols": ["necessita_ingresso"],
        "num_cols": ["preco_eur"],
        "order_by": "id",
    },
    "financeiro": {
        "csv": "05_financeiro.csv",
        "id_prefix": "F",
        "columns": ["id", "categoria", "item", "valor_estimado", "valor_real", "moeda", "pago"],
        "csv_columns": ["ID", "Categoria", "Item", "Valor Estimado", "Valor Real", "Moeda", "Pago?"],
        "date_cols": [],
        "bool_cols": ["pago"],
        "num_cols": ["valor_estimado", "valor_real"],
        "order_by": "id",
    },
    "checklist": {
        "csv": "06_checklist.csv",
        "id_prefix": "CK",
        "columns": ["id", "categoria", "item", "concluido"],
        "csv_columns": None,
        "date_cols": [],
        "bool_cols": ["concluido"],
        "num_cols": [],
        "order_by": "id",
    },
}


def _parse_number(raw) -> float | None:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    s = str(raw).strip()
    if not s:
        return None
    m = re.search(r"~?\s*(\d+[.,]?\d*)\s*EUR", s, re.IGNORECASE)
    if not m:
        m = re.search(r"(\d+[.,]?\d*)", s)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


def _parse_bool(raw) -> bool:
    return str(raw).strip().lower() in {"sim", "ok", "yes", "true", "1"}


@st.cache_resource
def get_client() -> Client:
    cfg = st.secrets["supabase"]
    return create_client(cfg["url"], cfg["key"])


def _clean_value(table: str, key: str, value):
    spec = TABLE_SPECS[table]
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if key in spec["date_cols"]:
        ts = pd.to_datetime(value, errors="coerce")
        return None if pd.isna(ts) else ts.strftime("%Y-%m-%d")
    if key in spec["bool_cols"]:
        return bool(value)
    if key in spec["num_cols"]:
        n = pd.to_numeric(value, errors="coerce")
        return None if pd.isna(n) else float(n)
    return str(value)


def _clean_record(table: str, values: dict) -> dict:
    return {k: _clean_value(table, k, v) for k, v in values.items()}


def _seed_rows_checklist() -> pd.DataFrame:
    df = pd.read_csv(CSV_DIR / TABLE_SPECS["checklist"]["csv"])
    return pd.DataFrame(
        {
            "id": [f"CK-{i + 1:02d}" for i in range(len(df))],
            "categoria": df["Categoria"],
            "item": df["Item"],
            "concluido": df["Status"].apply(_parse_bool),
        }
    )


def _seed_rows_generic(table: str) -> pd.DataFrame:
    spec = TABLE_SPECS[table]
    df = pd.read_csv(CSV_DIR / spec["csv"])
    out = pd.DataFrame()
    for db_col, csv_col in zip(spec["columns"], spec["csv_columns"]):
        col = df[csv_col]
        if db_col in spec["date_cols"]:
            out[db_col] = pd.to_datetime(col, errors="coerce").dt.strftime("%Y-%m-%d")
        elif db_col in spec["bool_cols"]:
            out[db_col] = col.apply(_parse_bool)
        elif db_col in spec["num_cols"]:
            out[db_col] = col.apply(_parse_number)
        else:
            out[db_col] = col.fillna("").astype(str)
    return out


def _seed_rows(table: str) -> pd.DataFrame:
    return _seed_rows_checklist() if table == "checklist" else _seed_rows_generic(table)


def _delete_all(client: Client, table: str) -> None:
    client.table(table).delete().neq("id", "").execute()


def _insert_df(client: Client, table: str, df: pd.DataFrame) -> None:
    if df.empty:
        return
    records = [_clean_record(table, row) for row in df.to_dict("records")]
    client.table(table).insert(records).execute()


def init_db() -> None:
    """Semeia cada tabela a partir dos CSVs originais, só se ela estiver vazia."""
    client = get_client()
    for table in TABLE_SPECS:
        resp = client.table(table).select("id", count="exact").limit(1).execute()
        if resp.count:
            continue
        _insert_df(client, table, _seed_rows(table))


def reset_db() -> None:
    """Apaga tudo e recarrega o roteiro original dos CSVs (descarta edições)."""
    client = get_client()
    for table in TABLE_SPECS:
        _delete_all(client, table)
        _insert_df(client, table, _seed_rows(table))


def load_df(table: str) -> pd.DataFrame:
    spec = TABLE_SPECS[table]
    client = get_client()
    resp = client.table(table).select("*").order(spec["order_by"]).execute()
    df = pd.DataFrame(resp.data) if resp.data else pd.DataFrame(columns=spec["columns"])
    for col in spec["date_cols"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in spec["bool_cols"]:
        df[col] = df[col].fillna(False).astype(bool)
    for col in spec["num_cols"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.reset_index(drop=True)


def _next_id(table: str, client: Client) -> str:
    spec = TABLE_SPECS[table]
    resp = client.table(table).select("id").execute()
    max_n = 0
    for row in resp.data or []:
        m = re.search(r"(\d+)\s*$", str(row["id"]))
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"{spec['id_prefix']}-{max_n + 1:02d}"


def insert_row(table: str, values: dict) -> str:
    """Insere uma linha nova (gera um código se não vier um) e retorna o ID usado."""
    client = get_client()
    row_id = str(values.get("id") or "").strip() or _next_id(table, client)
    record = _clean_record(table, {**values, "id": row_id})
    client.table(table).insert(record).execute()
    return row_id


def update_row(table: str, row_id: str, values: dict) -> None:
    client = get_client()
    record = _clean_record(table, values)
    client.table(table).update(record).eq("id", row_id).execute()


def update_rows(table: str, row_ids: list[str], field: str, value) -> None:
    client = get_client()
    record = _clean_record(table, {field: value})
    client.table(table).update(record).in_("id", list(row_ids)).execute()


def delete_rows(table: str, row_ids: list[str]) -> None:
    client = get_client()
    client.table(table).delete().in_("id", list(row_ids)).execute()

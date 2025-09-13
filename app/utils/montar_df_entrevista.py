import sqlite3
import pandas as pd
from pathlib import Path

caminho_db = Path.cwd() / "app" / "data" / "extraidos" / "dados.db"

# Funções auxiliares
def montar_df_entrevista(email_candidato):
    """Busca o candidato por e-mail e faz join com prospects e vagas."""

    conn = sqlite3.connect(caminho_db)
    df_applicants = pd.read_sql_query(
        "SELECT * FROM applicants WHERE LOWER(infos_basicas_email) LIKE ?",
        conn, params=(email_candidato.lower(),)
    )
    if df_applicants.empty:
        conn.close()
        return None
    df_prospects = pd.read_sql_query("SELECT * FROM prospects", conn)
    df_vagas = pd.read_sql_query("SELECT * FROM vagas", conn)
    conn.close()
    df_merged = df_applicants.merge(df_prospects, on="codigo", how="left")
    df_merged = df_merged.merge(df_vagas, left_on="codigo_vaga", right_on="codigo", how="left", suffixes=('', '_vaga'))
    return df_merged
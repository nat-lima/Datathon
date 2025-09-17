from ml3_drift.monitoring.ks import KSDriftDetector
import pandas as pd
import sqlite3
from datetime import datetime
import mlflow
import os

def monitorar_drift_ml3():
    # Caminho do banco
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'data', 'extraidos', 'dados.db')

    # Extrai dados
    conn = sqlite3.connect(db_path)
    query = """
    SELECT formacao_academica, informacoes_profissionais_conhecimentos_tecnicos, cv_pt, infos_basicas_data_criacao
    FROM prospects
    WHERE infos_basicas_data_criacao IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    df["infos_basicas_data_criacao"] = pd.to_datetime(df["infos_basicas_data_criacao"], errors="coerce")
    df = df.dropna(subset=["infos_basicas_data_criacao"])

    # Divide os dados por tempo
    data_min = df["infos_basicas_data_criacao"].min()
    data_max = df["infos_basicas_data_criacao"].max()
    intervalo = data_max - data_min
    limite = data_max - intervalo * 0.2

    df_ref = df[df["infos_basicas_data_criacao"] < limite].drop(columns=["infos_basicas_data_criacao"])
    df_cur = df[df["infos_basicas_data_criacao"] >= limite].drop(columns=["infos_basicas_data_criacao"])

    # Codifica texto como números
    df_all = pd.concat([df_ref, df_cur])
    df_encoded = df_all.apply(lambda col: pd.factorize(col)[0])
    n_ref = len(df_ref)
    X_ref = df_encoded.iloc[:n_ref].to_numpy()
    X_cur = df_encoded.iloc[n_ref:].to_numpy()

    # Detecta drift com KS
    detector = KSDriftDetector()
    detector.fit(X_ref)
    result = detector.detect(X_cur)

    drift_detectado = result["is_drift"]
    p_values = result["p_values"]
    drift_features = [df_encoded.columns[i] for i, p in enumerate(p_values) if p < 0.05]

    # Log no MLflow
    mlflow.set_tracking_uri(f"file:///{os.path.join(base_dir, '..', 'mlruns')}")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with mlflow.start_run(run_name=f"Drift_ml3_{timestamp}"):
        mlflow.log_param("drift_detectado", drift_detectado)
        mlflow.log_param("features_com_drift", ", ".join(drift_features))
        mlflow.log_metric("num_features_drift", len(drift_features))

    return drift_detectado, drift_features
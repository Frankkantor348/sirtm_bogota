"""
========================================================================================
MÓDULO: APRENDIZAJE NO SUPERVISADO - TÉCNICAS DE AGRUPAMIENTO (SIRTM BOGOTÁ)
========================================================================================
Fundamentación Teórica:
    Basado en el Capítulo 16 ("Técnicas de agrupamiento") del libro:
    Palma Méndez, J. T. (2008). Inteligencia artificial: métodos, técnicas y aplicaciones.
    Madrid: McGraw-Hill España.

Propósito Académico:
    Descubrir estructuras y agrupamientos latentes (clusters) en los patrones de viaje
    del sistema de transporte TransMilenio sin requerir etiquetas predefinidas.
    Permite a la Secretaría de Movilidad y TransMilenio identificar perfiles operativos
    de vulnerabilidad, regímenes de flujo libre y ventanas de colapso por congestión.

Técnicas Implementadas (Cap. 16 Palma Méndez, 2008):
    1. Agrupamiento Particional (K-Means / K-Medias):
       Minimización de la inercia intra-cluster (Within-Cluster Sum of Squares, WCSS).
    2. Determinación del Número Óptimo de Clusters (k):
       - Método del Codo (Elbow Method).
       - Coeficiente de Silueta (Silhouette Score) para cohesión y separación.
    3. Agrupamiento Jerárquico Aglomerativo (Agglomerative Hierarchical Clustering):
       Con enlace Ward y generación de dendrograma.
    4. Reducción de Dimensionalidad (PCA - Análisis de Componentes Principales):
       Proyección ortogonal en 2D para visualización e interpretación geométrica.
========================================================================================
"""

import os
import json
from typing import Tuple, Dict, Any, List
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Componentes de Scikit-Learn y SciPy
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from scipy.cluster.hierarchy import dendrogram, linkage

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "datos", "dataset_viajes_transmilenio.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "datos")


def cargar_y_preparar_datos_clustering(ruta_csv: str = DATA_PATH) -> Tuple[pd.DataFrame, np.ndarray, List[str]]:
    """
    Carga el dataset y selecciona las variables cuantitativas de interés para el agrupamiento.

    Variables Operativas Utilizadas:
    - 'distancia_km': Longitud del recorrido.
    - 'hora': Momento del día.
    - 'afluencia_pasajeros': Demanda de usuarios en estación.
    - 'tiempo_base_minutos': Duración programada ideal.
    - 'tiempo_real_minutos': Duración observada.
    - 'retraso_minutos': Demora efectiva acumulada.

    Retorna:
    --------
    Tuple[pd.DataFrame, np.ndarray, List[str]]:
        - df: DataFrame original.
        - X_scaled: Matriz normalizada (media 0, varianza 1).
        - features: Lista de nombres de las características utilizadas.
    """
    if not os.path.exists(ruta_csv):
        raise FileNotFoundError(f"No se encontró el dataset en {ruta_csv}. Ejecute primero src/generar_dataset.py.")

    df = pd.read_csv(ruta_csv)

    feature_cols = [
        "distancia_km",
        "hora",
        "afluencia_pasajeros",
        "tiempo_base_minutos",
        "tiempo_real_minutos",
        "retraso_minutos"
    ]

    X = df[feature_cols].copy()

    # Normalización indispensable para clustering: distancia euclidiana sensible a escalas
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return df, X_scaled, feature_cols


def evaluar_numero_optimo_k(X_scaled: np.ndarray, k_min: int = 2, k_max: int = 8) -> Dict[str, Any]:
    """
    Evalúa diferentes valores de k usando la Inercia (Método del Codo) y el Coeficiente de Silueta.

    Fundamentación (Capítulo 16 Palma Méndez, 2008):
    - Inercia (WCSS): Suma de distancias cuadráticas de cada punto a su centroide.
    - Silueta s(i): (b(i) - a(i)) / max(a(i), b(i)), donde a(i) es la distancia media intra-cluster
      y b(i) es la distancia media al cluster vecino más cercano. Rango [-1, 1].

    Retorna:
    --------
    Dict[str, Any]:
        Valores de k, inercias, siluetas y el k óptimo sugerido.
    """
    k_valores = list(range(k_min, k_max + 1))
    inercias = []
    siluetas = []

    for k in k_valores:
        km = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=42)
        etiquetas = km.fit_predict(X_scaled)
        inercias.append(km.inertia_)
        sil = silhouette_score(X_scaled, etiquetas)
        siluetas.append(sil)

    # Identificar k con máximo silhouette score
    k_optimo = k_valores[int(np.argmax(siluetas))]

    return {
        "k_valores": k_valores,
        "inercias": inercias,
        "siluetas": siluetas,
        "k_optimo": k_optimo
    }


def entrenar_kmeans(X_scaled: np.ndarray, k: int = 3) -> Dict[str, Any]:
    """
    Ajusta el algoritmo K-Means con el número k de clusters seleccionado.

    Parámetros:
    -----------
    X_scaled : np.ndarray
        Matriz de características normalizada.
    k : int
        Número de clusters a formar.

    Retorna:
    --------
    Dict[str, Any]:
        Modelo ajustado, etiquetas asignadas, centroides y métricas de validación.
    """
    kmeans = KMeans(n_clusters=k, init="k-means++", n_init=15, max_iter=300, random_state=42)
    etiquetas = kmeans.fit_predict(X_scaled)

    # Métricas de validación interna de clusters (Cap. 16 Palma Méndez, 2008)
    sil = silhouette_score(X_scaled, etiquetas)
    ch = calinski_harabasz_score(X_scaled, etiquetas)
    db = davies_bouldin_score(X_scaled, etiquetas)

    return {
        "modelo": kmeans,
        "etiquetas": etiquetas,
        "centroides": kmeans.cluster_centers_,
        "inercia": kmeans.inertia_,
        "silhouette": sil,
        "calinski_harabasz": ch,
        "davies_bouldin": db
    }


def caracterizar_clusters(df: pd.DataFrame, etiquetas: np.ndarray, feature_cols: List[str]) -> pd.DataFrame:
    """
    Calcula los promedios y características operativas de cada cluster para interpretación de negocio.
    """
    df_analisis = df.copy()
    df_analisis["cluster_kmeans"] = etiquetas

    # Perfiles promedio por cluster
    resumen = df_analisis.groupby("cluster_kmeans")[feature_cols].mean().round(2)
    resumen["total_viajes"] = df_analisis.groupby("cluster_kmeans")["id_viaje"].count()
    resumen["porcentaje"] = ((resumen["total_viajes"] / len(df_analisis)) * 100).round(1)

    # Asignar nombres semánticos según las medias operativas observadas
    nombres_perfil = {}
    for cl in resumen.index:
        retraso_medio = resumen.loc[cl, "retraso_minutos"]
        afluencia_media = resumen.loc[cl, "afluencia_pasajeros"]
        if retraso_medio > 10.0:
            nombres_perfil[cl] = "Perfil Crítico / Alta Vulnerabilidad (Pico + Incidentes)"
        elif afluencia_media > 1800:
            nombres_perfil[cl] = "Perfil Demanda Alta / Tráfico Controlado"
        else:
            nombres_perfil[cl] = "Perfil Flujo Libre / Operación Estable (Valle)"

    resumen["perfil_operativo"] = resumen.index.map(nombres_perfil)
    return resumen


def graficar_y_guardar_no_supervisado(
    X_scaled: np.ndarray,
    df: pd.DataFrame,
    res_optimo: Dict[str, Any],
    res_kmeans: Dict[str, Any],
    feature_cols: List[str],
    resumen_clusters: pd.DataFrame
) -> Tuple[str, str, str, str]:
    """
    Genera visualizaciones del Método del Codo, Proyección PCA de Clusters,
    Dendrograma Jerárquico y exporta las métricas y perfiles en JSON/CSV.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Gráfico del Método del Codo y Coeficiente de Silueta
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    ax1.plot(res_optimo["k_valores"], res_optimo["inercias"], "bo-", linewidth=2, markersize=8)
    ax1.set_xlabel("Número de Clusters (k)", fontweight="bold")
    ax1.set_ylabel("Inercia (WCSS)", fontweight="bold")
    ax1.set_title("Método del Codo (Elbow Method)", fontsize=12, fontweight="bold")
    ax1.grid(True, linestyle="--", alpha=0.6)

    ax2.plot(res_optimo["k_valores"], res_optimo["siluetas"], "ro-", linewidth=2, markersize=8)
    ax2.axvline(x=res_kmeans["modelo"].n_clusters, color="green", linestyle="--", label=f"k seleccionado = {res_kmeans['modelo'].n_clusters}")
    ax2.set_xlabel("Número de Clusters (k)", fontweight="bold")
    ax2.set_ylabel("Coeficiente de Silueta", fontweight="bold")
    ax2.set_title("Coeficiente de Silueta vs. k", fontsize=12, fontweight="bold")
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    ruta_codo = os.path.join(OUTPUT_DIR, "metodo_codo_silueta.png")
    plt.savefig(ruta_codo, dpi=300)
    plt.close()

    # 2. Proyección 2D mediante PCA para visualizar separación geométrica
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    var_exp = pca.explained_variance_ratio_ * 100

    plt.figure(figsize=(9, 6))
    scatter = plt.scatter(
        X_pca[:, 0], X_pca[:, 1],
        c=res_kmeans["etiquetas"],
        cmap="viridis",
        alpha=0.65,
        edgecolors="none",
        s=35
    )
    # Proyectar centroides en espacio PCA
    centroides_pca = pca.transform(res_kmeans["centroides"])
    plt.scatter(
        centroides_pca[:, 0], centroides_pca[:, 1],
        marker="X", s=200, c="red", edgecolors="black", linewidth=2, label="Centroides de Cluster"
    )
    plt.colorbar(scatter, label="Cluster Asignado (K-Means)")
    plt.xlabel(f"Componente Principal 1 ({var_exp[0]:.1f}% varianza)", fontweight="bold")
    plt.ylabel(f"Componente Principal 2 ({var_exp[1]:.1f}% varianza)", fontweight="bold")
    plt.title(f"Agrupamiento No Supervisado (K-Means k={res_kmeans['modelo'].n_clusters}) en Espacio PCA", fontsize=12, fontweight="bold")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    ruta_pca = os.path.join(OUTPUT_DIR, "clustering_kmeans.png")
    plt.savefig(ruta_pca, dpi=300)
    plt.close()

    # 3. Dendrograma Jerárquico Aglomerativo (submuestra de 50 para visualización nítida)
    np.random.seed(42)
    idx_sample = np.random.choice(X_scaled.shape[0], size=50, replace=False)
    X_sub = X_scaled[idx_sample]
    Z = linkage(X_sub, method="ward")

    plt.figure(figsize=(10, 5))
    dendrogram(Z, leaf_rotation=90, leaf_font_size=8)
    plt.title("Dendrograma de Agrupamiento Jerárquico Aglomerativo (Método Ward)", fontsize=12, fontweight="bold")
    plt.xlabel("Muestra de Viajes (Índice)", fontweight="bold")
    plt.ylabel("Distancia de Disimilitud (Ward)", fontweight="bold")
    plt.tight_layout()
    ruta_dendro = os.path.join(OUTPUT_DIR, "dendrograma.png")
    plt.savefig(ruta_dendro, dpi=300)
    plt.close()

    # 4. Guardar archivo CSV con los perfiles operativos
    ruta_csv_perfiles = os.path.join(OUTPUT_DIR, "clusters_resumen.csv")
    resumen_clusters.to_csv(ruta_csv_perfiles, encoding="utf-8")

    # 5. Guardar métricas en JSON
    metricas = {
        "algoritmo": "K-Means",
        "k_clusters": int(res_kmeans["modelo"].n_clusters),
        "inercia_wcss": round(float(res_kmeans["inercia"]), 2),
        "silhouette_score": round(float(res_kmeans["silhouette"]), 4),
        "calinski_harabasz_score": round(float(res_kmeans["calinski_harabasz"]), 2),
        "davies_bouldin_score": round(float(res_kmeans["davies_bouldin"]), 4),
        "pca_varianza_explicada_acumulada_pct": round(float(np.sum(var_exp)), 2),
        "perfiles": resumen_clusters.to_dict(orient="index")
    }
    ruta_json = os.path.join(OUTPUT_DIR, "metricas_no_supervisado.json")
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=4, ensure_ascii=False)

    print(f"[OK] Visualizaciones y métricas no supervisadas guardadas en: {OUTPUT_DIR}")
    return ruta_codo, ruta_pca, ruta_dendro, ruta_json


def ejecutar_pipeline_no_supervisado():
    """Función principal que orquesta el agrupamiento no supervisado completo."""
    print("=" * 70)
    print("SIRTM BOGOTÁ: APRENDIZAJE NO SUPERVISADO - TÉCNICAS DE AGRUPAMIENTO")
    print("MÉTODO: K-MEANS Y CLUSTERING JERÁRQUICO (PALMA MÉNDEZ, 2008 - CAP. 16)")
    print("=" * 70)

    # 1. Carga de datos
    df, X_scaled, feature_cols = cargar_y_preparar_datos_clustering()
    print(f"Observaciones analizadas: {X_scaled.shape[0]} viajes")
    print(f"Dimensiones normalizadas: {feature_cols}")

    # 2. Evaluación de k óptimo
    print("\n[1/3] Evaluando número óptimo de clusters (Método del Codo y Silueta)...")
    res_opt = evaluar_numero_optimo_k(X_scaled, k_min=2, k_max=7)
    for k, iner, sil in zip(res_opt["k_valores"], res_opt["inercias"], res_opt["siluetas"]):
        print(f"  k = {k} | Inercia: {iner:.1f} | Silueta: {sil:.4f}")
    k_sel = 3  # Valor representativo para interpretabilidad del negocio de movilidad
    print(f"  -> k seleccionado para perfilamiento: {k_sel}")

    # 3. Entrenamiento K-Means
    print(f"\n[2/3] Entrenando modelo K-Means con k={k_sel}...")
    res_km = entrenar_kmeans(X_scaled, k=k_sel)
    print(f"  -> Coeficiente de Silueta: {res_km['silhouette']:.4f}")
    print(f"  -> Calinski-Harabasz: {res_km['calinski_harabasz']:.2f}")
    print(f"  -> Davies-Bouldin: {res_km['davies_bouldin']:.4f}")

    # 4. Caracterización de perfiles
    print("\n[3/3] Caracterizando perfiles operativos identificados:")
    resumen = caracterizar_clusters(df, res_km["etiquetas"], feature_cols)
    print(resumen[["total_viajes", "porcentaje", "afluencia_pasajeros", "retraso_minutos", "perfil_operativo"]].to_string())

    # 5. Exportar gráficos
    graficar_y_guardar_no_supervisado(X_scaled, df, res_opt, res_km, feature_cols, resumen)

    return res_km, resumen


if __name__ == "__main__":
    ejecutar_pipeline_no_supervisado()

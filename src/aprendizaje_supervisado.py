"""
========================================================================================
MÓDULO: APRENDIZAJE SUPERVISADO - ÁRBOLES Y REGLAS DE DECISIÓN (SIRTM BOGOTÁ)
========================================================================================
Fundamentación Teórica:
    Basado en el Capítulo 17 ("Aprendizaje de árboles y reglas de decisión") del libro:
    Palma Méndez, J. T. (2008). Inteligencia artificial: métodos, técnicas y aplicaciones.
    Madrid: McGraw-Hill España.

Objetivos de este Módulo:
    1. Preprocesar las variables multivariadas (categóricas y numéricas) de la red TransMilenio.
    2. Entrenar un Árbol de Decisión de Clasificación para predecir el 'Nivel de Congestión'
       (Bajo, Medio, Alto, Crítico) aplicando pre-poda (pre-pruning) para evitar sobreajuste.
    3. Extraer inductivamente el conjunto formal de Reglas de Decisión lógicas (IF ... THEN ...)
       a partir de los caminos raíz-hoja del árbol, calculando su soporte y confianza.
    4. Entrenar un Árbol de Decisión de Regresión para predecir el tiempo real de viaje (minutos).
    5. Evaluar los modelos mediante métricas rigurosas (Accuracy, F1-Score, Matriz de Confusión,
       Validación Cruzada 5-Fold, R², MAE y RMSE) y permitir inferencias en tiempo real.
========================================================================================
"""

import os
import json
from typing import Tuple, List, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Importación de componentes de Scikit-Learn para aprendizaje supervisado
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor, plot_tree
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

# Definición de rutas relativas al proyecto para portabilidad en cualquier sistema operativo
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "datos", "dataset_viajes_transmilenio.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "datos")


def cargar_y_preparar_datos(ruta_csv: str = DATA_PATH) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Carga el dataset de viajes de TransMilenio y descompone las columnas en variables predictoras
    (características o features) y variables objetivo (targets de clasificación y regresión).

    Parámetros:
    -----------
    ruta_csv : str
        Ruta absoluta o relativa al archivo CSV con las observaciones de viaje.

    Retorna:
    --------
    Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        - df: DataFrame original completo con todas las observaciones.
        - X: Matriz de características predictoras (9 variables operativas y de contexto).
        - y_clasificacion: Vector objetivo con los niveles de congestión (Bajo, Medio, Alto, Crítico).
        - y_regresion: Vector objetivo continuo con el tiempo real cronometrado en minutos.
    """
    # Verificar existencia física del archivo
    if not os.path.exists(ruta_csv):
        raise FileNotFoundError(
            f"No se encontró el archivo de datos en: {ruta_csv}. "
            "Por favor, ejecute primero el script 'src/generar_dataset.py'."
        )

    # Lectura del archivo CSV mediante pandas
    df = pd.read_csv(ruta_csv)

    # Selección explícita de las características independientes predictoras (Features)
    feature_cols = [
        "troncal",              # Corredor vial (Caracas, Autonorte, Suba, etc.)
        "distancia_km",         # Longitud del tramo recorrido
        "tipo_dia",             # Laboral o Fin de Semana
        "hora",                 # Hora del día (5 a 21)
        "franja_horaria",       # Pico Mañana, Valle Día, Pico Tarde, Valle Noche
        "clima",                # Despejado, Lluvia Ligera, Lluvia Fuerte
        "afluencia_pasajeros",  # Densidad de usuarios en estación
        "incidente_vial",       # Ninguno, Accidente, Bloqueo o Falla
        "tiempo_base_minutos"   # Tiempo programado ideal de viaje
    ]

    # Separación de matrices predictoras y vectores objetivo
    X = df[feature_cols].copy()
    y_clasificacion = df["nivel_congestion"].copy()
    y_regresion = df["tiempo_real_minutos"].copy()

    return df, X, y_clasificacion, y_regresion


def construir_preprocesador() -> Tuple[ColumnTransformer, List[str], List[str]]:
    """
    Construye la canalización (Pipeline) de preprocesamiento de datos usando ColumnTransformer.

    ¿Qué hace esta función?
    -----------------------
    - Aplica 'One-Hot Encoding' a las variables categóricas (nominales), convirtiéndolas
      en representaciones numéricas binarias independientes y eliminando la primera categoría
      (drop='first') para evitar colinealidad matemática.
    - Aplica 'StandardScaler' (Z-score normalization: media 0, varianza 1) a las variables
      numéricas para evitar que escalas grandes (como afluencia de 3000 pasajeros) distorsionen
      los umbrales de decisión frente a distancias pequeñas en kilómetros.

    Retorna:
    --------
    Tuple[ColumnTransformer, List[str], List[str]]:
        - preprocesador: Objeto ColumnTransformer configurado listo para fit_transform.
        - categoricas: Lista de nombres de columnas cualitativas.
        - numericas: Lista de nombres de columnas cuantitativas.
    """
    categoricas = ["troncal", "tipo_dia", "franja_horaria", "clima", "incidente_vial"]
    numericas = ["distancia_km", "hora", "afluencia_pasajeros", "tiempo_base_minutos"]

    preprocesador = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore"),
                categoricas
            ),
            (
                "num",
                StandardScaler(),
                numericas
            )
        ],
        remainder="passthrough"
    )
    return preprocesador, categoricas, numericas


def extraer_reglas_legibles(tree_model: DecisionTreeClassifier, feature_names: List[str], class_names: List[str]) -> List[str]:
    """
    Extrae inductivamente un conjunto formal de Reglas de Decisión tipo 'IF ... THEN ...'
    a partir de la estructura interna del árbol de decisión entrenado.

    Fundamentación (Capítulo 17 de Palma Méndez, 2008):
    ---------------------------------------------------
    Todo árbol de decisión puede traducirse en un conjunto equivalente de reglas de producción
    lógicas en Forma Normal Disyuntiva. Cada camino orientado desde la raíz hasta un nodo hoja
    constituye una conjunción lógica de premisas (antecedente) que implica una clase consecuente.

    Para cada regla inducida se calculan:
    - Soporte (Support): Cantidad de instancias empíricas del dataset que caen en ese nodo hoja.
    - Confianza (Confidence): Proporción de aciertos de la clase mayoritaria en dicho nodo hoja.

    Parámetros:
    -----------
    tree_model : DecisionTreeClassifier
        Modelo de árbol entrenado cuya estructura 'tree_' será recorrida.
    feature_names : List[str]
        Lista con los nombres descriptivos de las columnas tras la codificación.
    class_names : List[str]
        Lista ordenada de las clases objetivo del problema (ej. ['Alto', 'Bajo', 'Critico', 'Medio']).

    Retorna:
    --------
    List[str]:
        Lista de cadenas de texto formateadas con las reglas de decisión en lenguaje natural.
    """
    arbol = tree_model.tree_
    reglas = []

    def recorrer_nodo(node_id: int, condiciones_actuales: List[str]):
        """Función recursiva interna de recorrido en profundidad (DFS) sobre los nodos del árbol."""
        # Condición de parada: Si el hijo izquierdo y derecho son iguales (-1), es un nodo hoja (terminal)
        if arbol.children_left[node_id] == arbol.children_right[node_id]:
            # Identificar el índice de la clase mayoritaria en este nodo hoja
            clase_idx = np.argmax(arbol.value[node_id][0])
            clase = class_names[clase_idx]

            # Soporte: número de muestras de entrenamiento asignadas a este nodo hoja
            muestras = int(arbol.n_node_samples[node_id])

            # Confianza: probabilidad o frecuencia relativa de la clase mayoritaria en la hoja
            distribucion = arbol.value[node_id][0]
            suma_val = np.sum(distribucion)
            confianza = distribucion[clase_idx] / suma_val if suma_val > 0 else 0.0

            # Formatear la regla lógica en formato estándar IF-THEN
            regla_str = (
                f"IF {' AND '.join(condiciones_actuales)} "
                f"THEN Nivel_Congestion = '{clase}' (Soporte: {muestras} muestras, Confianza: {confianza:.1%})"
            )
            reglas.append(regla_str)
            return

        # Si no es hoja, es un nodo de bifurcación (prueba de división)
        feature_name = feature_names[arbol.feature[node_id]]
        threshold = arbol.threshold[node_id]

        # Explorar rama izquierda: condición (Atributo <= Umbral)
        recorrer_nodo(
            arbol.children_left[node_id],
            condiciones_actuales + [f"({feature_name} <= {threshold:.2f})"]
        )

        # Explorar rama derecha: condición (Atributo > Umbral)
        recorrer_nodo(
            arbol.children_right[node_id],
            condiciones_actuales + [f"({feature_name} > {threshold:.2f})"]
        )

    # Iniciar el recorrido recursivo desde el nodo raíz (identificador 0)
    recorrer_nodo(0, [])
    return reglas


def entrenar_clasificador(X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """
    Entrena y evalúa un modelo de Árbol de Decisión de Clasificación para predecir 'Nivel de Congestión'.

    Metodología y Control de Sobreajuste:
    ------------------------------------
    - Se aplica partición 80% Entrenamiento y 20% Prueba bajo muestreo estratificado
      (Stratified Split) para conservar las proporciones relativas de cada clase.
    - Se implementa técnica de PRE-PODA (Pre-pruning) recomendada por Palma Méndez (2008):
        * max_depth = 5: Limita la profundidad máxima del árbol a 5 niveles para evitar memorización de ruido.
        * min_samples_split = 20: Exige al menos 20 observaciones para autorizar una partición interna.
        * min_samples_leaf = 10: Garantiza que cada hoja contenga un soporte estadístico mínimo de 10 muestras.
    - Se evalúa con Validación Cruzada Estratificada de 5 pliegues (5-Fold Stratified CV).

    Retorna:
    --------
    Dict[str, Any]:
        Diccionario exhaustivo con el modelo entrenado, preprocesador, métricas (Accuracy,
        F1 macro/ponderado, CV), matriz de confusión, reporte detallado y reglas extraídas.
    """
    # 1. Configurar y ajustar el preprocesador sobre las características
    preprocesador, cat_cols, num_cols = construir_preprocesador()
    X_proc = preprocesador.fit_transform(X)

    # Obtener los nombres resultantes de las columnas tras One-Hot Encoding
    cat_feature_names = preprocesador.named_transformers_["cat"].get_feature_names_out(cat_cols)
    feature_names = list(cat_feature_names) + num_cols
    clases_orden = sorted(list(y.unique()))

    # 2. Partición Estratificada en Train (80%) y Test (20%)
    X_train, X_test, y_train, y_test = train_test_split(
        X_proc, y, test_size=0.20, random_state=42, stratify=y
    )

    # 3. Creación y ajuste del árbol con criterio de impureza Gini y pre-poda
    clf = DecisionTreeClassifier(
        criterion="gini",         # Criterio CART de impureza de Gini (Palma Méndez, 2008)
        max_depth=5,              # Pre-poda: máxima profundidad para evitar overfitting
        min_samples_split=20,     # Pre-poda: mínimo de muestras para bifurcar
        min_samples_leaf=10,      # Pre-poda: mínimo de muestras en hojas
        random_state=42
    )
    clf.fit(X_train, y_train)

    # 4. Inferencia sobre el conjunto independiente de prueba
    y_pred = clf.predict(X_test)

    # 5. Cálculo riguroso de métricas de desempeño
    acc = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average="macro")
    f1_weighted = f1_score(y_test, y_pred, average="weighted")
    report = classification_report(y_test, y_pred, output_dict=True)
    matriz_conf = confusion_matrix(y_test, y_pred, labels=clases_orden)

    # 6. Validación cruzada estratificada de 5 pliegues para verificar estabilidad
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(clf, X_proc, y, cv=cv, scoring="accuracy")

    # 7. Extracción de las reglas de decisión lógicas equivalentes
    reglas = extraer_reglas_legibles(clf, feature_names, clases_orden)

    return {
        "modelo": clf,
        "preprocesador": preprocesador,
        "feature_names": feature_names,
        "clases": clases_orden,
        "accuracy": acc,
        "f1_macro": f1_macro,
        "f1_weighted": f1_weighted,
        "cv_mean": cv_scores.mean(),
        "cv_std": cv_scores.std(),
        "report": report,
        "matriz_conf": matriz_conf,
        "reglas": reglas,
        "X_test": X_test,
        "y_test": y_test,
        "y_pred": y_pred
    }


def entrenar_regresor(X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """
    Entrena un Árbol de Decisión de Regresión (DecisionTreeRegressor) para predecir
    el tiempo real de viaje en minutos a través de la red de transporte.

    ¿Por qué un regresor complementario?
    ------------------------------------
    Permite cuantificar de manera continua la demora exacta en minutos causada por lluvia
    e incidentes, complementando la etiqueta cualitativa de congestión para ajustar
    la función de costo g(n) en el algoritmo heurístico de búsqueda A*.

    Métricas calculadas:
    - R² Score: Coeficiente de determinación (porcentaje de varianza explicada).
    - MAE: Error Absoluto Medio (en minutos).
    - RMSE: Raíz del Error Cuadrático Medio (en minutos).
    """
    # Preprocesar variables independientes
    preprocesador, cat_cols, num_cols = construir_preprocesador()
    X_proc = preprocesador.fit_transform(X)

    # Partición 80% Entrenamiento y 20% Prueba
    X_train, X_test, y_train, y_test = train_test_split(
        X_proc, y, test_size=0.20, random_state=42
    )

    # Modelo de árbol con criterio de error cuadrático medio (squared_error)
    reg = DecisionTreeRegressor(
        criterion="squared_error",
        max_depth=6,
        min_samples_split=20,
        min_samples_leaf=10,
        random_state=42
    )
    reg.fit(X_train, y_train)

    # Predicción y cálculo de errores sobre el conjunto de prueba
    y_pred = reg.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    return {
        "modelo": reg,
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "y_test": y_test,
        "y_pred": y_pred
    }


def graficar_y_guardar_resultados(clf_results: Dict[str, Any], reg_results: Dict[str, Any]) -> Tuple[str, str, str, str]:
    """
    Genera y guarda en disco las representaciones visuales y reportes del modelo entrenado:
    1. 'matriz_confusion.png': Heatmap con los aciertos y errores de clasificación.
    2. 'arbol_decision.png': Gráfico renderizado del árbol podado a nivel 3 para inspección visual.
    3. 'metricas_modelo.json': Registro estructurado con las métricas cuantitativas calculadas.
    4. 'reglas_decision.txt': Archivo de texto formal con las 27 reglas lógicas IF-THEN extraídas.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Renderizado de la Matriz de Confusión
    clases = clf_results["clases"]
    cm = clf_results["matriz_conf"]

    fig, ax = plt.subplots(figsize=(6, 5))
    cax = ax.matshow(cm, cmap=plt.cm.Blues, alpha=0.85)

    # Anotar cada celda con el conteo numérico de observaciones
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(x=j, y=i, s=str(cm[i, j]), va='center', ha='center', size='large', weight='bold')

    fig.colorbar(cax)
    ax.set_xticks(range(len(clases)))
    ax.set_yticks(range(len(clases)))
    ax.set_xticklabels(clases, rotation=45, ha="left")
    ax.set_yticklabels(clases)
    plt.xlabel('Predicción del Modelo', fontweight='bold')
    plt.ylabel('Valor Real (Ground Truth)', fontweight='bold')
    plt.title('Matriz de Confusión - Nivel de Congestión SIRTM Bogotá', pad=20, fontweight='bold')
    plt.tight_layout()
    ruta_cm = os.path.join(OUTPUT_DIR, "matriz_confusion.png")
    plt.savefig(ruta_cm, dpi=300)
    plt.close()

    # 2. Renderizado gráfico del Árbol de Decisión (primeros 3 niveles para legibilidad visual)
    fig, ax = plt.subplots(figsize=(16, 9))
    plot_tree(
        clf_results["modelo"],
        feature_names=clf_results["feature_names"],
        class_names=clases,
        filled=True,
        rounded=True,
        max_depth=3,
        fontsize=8,
        ax=ax
    )
    plt.title("Árbol de Decisión de Clasificación (Nivel de Congestión - Podado a Nivel 3)", fontsize=14, fontweight='bold')
    plt.tight_layout()
    ruta_arbol = os.path.join(OUTPUT_DIR, "arbol_decision.png")
    plt.savefig(ruta_arbol, dpi=300)
    plt.close()

    # 3. Guardar métricas cuantitativas consolidadas en formato JSON
    metricas = {
        "clasificacion": {
            "accuracy": round(clf_results["accuracy"], 4),
            "f1_macro": round(clf_results["f1_macro"], 4),
            "f1_weighted": round(clf_results["f1_weighted"], 4),
            "cv_accuracy_mean": round(clf_results["cv_mean"], 4),
            "cv_accuracy_std": round(clf_results["cv_std"], 4),
            "clases": clases,
            "reporte_por_clase": {
                c: {
                    "precision": round(clf_results["report"][c]["precision"], 4),
                    "recall": round(clf_results["report"][c]["recall"], 4),
                    "f1-score": round(clf_results["report"][c]["f1-score"], 4),
                    "support": clf_results["report"][c]["support"]
                } for c in clases
            }
        },
        "regresion": {
            "mae_minutos": round(reg_results["mae"], 4),
            "rmse_minutos": round(reg_results["rmse"], 4),
            "r2_score": round(reg_results["r2"], 4)
        }
    }

    ruta_json = os.path.join(OUTPUT_DIR, "metricas_modelo.json")
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=4, ensure_ascii=False)

    # 4. Guardar archivo de reglas lógicas extraídas
    ruta_reglas = os.path.join(OUTPUT_DIR, "reglas_decision.txt")
    with open(ruta_reglas, "w", encoding="utf-8") as f:
        f.write("========================================================================\n")
        f.write("REGLAS DE DECISIÓN APRENDIDAS - CAPÍTULO 17 PALMA MÉNDEZ (2008)\n")
        f.write("SISTEMA INTELIGENTE DE RUTAS TRANSMILENIO (SIRTM BOGOTÁ)\n")
        f.write("========================================================================\n\n")
        for i, regla in enumerate(clf_results["reglas"], 1):
            f.write(f"REGLA #{i:02d}:\n  {regla}\n\n")

    print(f"[OK] Visualizaciones, métricas y reglas exportadas en: {OUTPUT_DIR}")
    return ruta_cm, ruta_arbol, ruta_json, ruta_reglas


def predecir_nuevo_escenario(preprocesador: ColumnTransformer, clf_model: DecisionTreeClassifier, reg_model: DecisionTreeRegressor, nuevo_caso_dict: Dict[str, Any]) -> Tuple[str, float]:
    """
    Ejecuta inferencia predictiva para un viaje no observado previamente, respondiendo
    tanto la categoría estimada de congestión como los minutos reales pronosticados.

    Parámetros:
    -----------
    preprocesador : ColumnTransformer
        Pipeline de codificación previamente ajustado con los datos de entrenamiento.
    clf_model : DecisionTreeClassifier
        Árbol de clasificación entrenado.
    reg_model : DecisionTreeRegressor
        Árbol de regresión entrenado.
    nuevo_caso_dict : Dict[str, Any]
        Diccionario con las condiciones operativas y climáticas del viaje.

    Retorna:
    --------
    Tuple[str, float]:
        - pred_congestion: Etiqueta cualitativa ('Bajo', 'Medio', 'Alto', 'Critico').
        - pred_tiempo: Estimación continua del tiempo de viaje en minutos.
    """
    df_caso = pd.DataFrame([nuevo_caso_dict])
    X_caso_proc = preprocesador.transform(df_caso)

    pred_congestion = clf_model.predict(X_caso_proc)[0]
    pred_tiempo = float(reg_model.predict(X_caso_proc)[0])

    return pred_congestion, pred_tiempo


def ejecutar_pipeline_completo():
    """
    Función orquestadora principal:
    Ejecuta de extremo a extremo la carga de datos, el entrenamiento de los dos modelos,
    la exportación de métricas/gráficos y la simulación interactiva de 3 casos reales en Bogotá.
    """
    print("=" * 70)
    print("SIRTM BOGOTÁ: ENTRENAMIENTO DE MODELOS DE APRENDIZAJE SUPERVISADO")
    print("MÉTODO: ÁRBOLES Y REGLAS DE DECISIÓN (PALMA MÉNDEZ, 2008 - CAP. 17)")
    print("=" * 70)

    # Paso 1: Carga y preparación del dataset
    df, X, y_clf, y_reg = cargar_y_preparar_datos()
    print(f"Total registros cargados: {len(df)}")
    print(f"Variables predictoras: {list(X.columns)}")

    # Paso 2: Entrenamiento del clasificador
    print("\n[1/3] Entrenando Árbol de Decisión de Clasificación...")
    clf_res = entrenar_clasificador(X, y_clf)
    print(f"  -> Exactitud (Accuracy): {clf_res['accuracy']:.4f}")
    print(f"  -> F1-Score (Ponderado): {clf_res['f1_weighted']:.4f}")
    print(f"  -> Validación Cruzada (5-Fold Accuracy): {clf_res['cv_mean']:.4f} (+/- {clf_res['cv_std']:.4f})")
    print(f"  -> Total reglas de decisión extraídas: {len(clf_res['reglas'])}")

    # Paso 3: Entrenamiento del regresor
    print("\n[2/3] Entrenando Árbol de Decisión de Regresión (Tiempo de Viaje)...")
    reg_res = entrenar_regresor(X, y_reg)
    print(f"  -> R² Score: {reg_res['r2']:.4f}")
    print(f"  -> Error Absoluto Medio (MAE): {reg_res['mae']:.2f} minutos")
    print(f"  -> Raíz del Error Cuadrático Medio (RMSE): {reg_res['rmse']:.2f} minutos")

    # Paso 4: Exportación de gráficos y archivos
    print("\n[3/3] Exportando visualizaciones, reportes y reglas...")
    cm_path, arbol_path, json_path, reglas_path = graficar_y_guardar_resultados(clf_res, reg_res)

    # Paso 5: Demostración en escenarios operativos reales de Bogotá
    print("\n" + "=" * 70)
    print("PRUEBA DE INFERENCIA EN ESCENARIOS REALES DE BOGOTÁ:")
    print("=" * 70)

    casos_prueba = [
        {
            "nombre": "Caso 1: Troncal Caracas Hora Pico con Lluvia Fuerte e Incidente",
            "datos": {
                "troncal": "Caracas",
                "distancia_km": 18.5,
                "tipo_dia": "Laboral",
                "hora": 18,
                "franja_horaria": "Pico_Tarde",
                "clima": "Lluvia_Fuerte",
                "afluencia_pasajeros": 3100,
                "incidente_vial": "Accidente_Transito",
                "tiempo_base_minutos": 25.0
            }
        },
        {
            "nombre": "Caso 2: Troncal Autonorte Domingo Medio Día Despejado",
            "datos": {
                "troncal": "Autonorte",
                "distancia_km": 8.2,
                "tipo_dia": "FinDeSemana",
                "hora": 12,
                "franja_horaria": "Valle_Dia",
                "clima": "Despejado",
                "afluencia_pasajeros": 750,
                "incidente_vial": "Ninguno",
                "tiempo_base_minutos": 10.0
            }
        },
        {
            "nombre": "Caso 3: Troncal Suba Mañana Laboral con Lluvia Ligera",
            "datos": {
                "troncal": "Suba",
                "distancia_km": 9.4,
                "tipo_dia": "Laboral",
                "hora": 7,
                "franja_horaria": "Pico_Manana",
                "clima": "Lluvia_Ligera",
                "afluencia_pasajeros": 2600,
                "incidente_vial": "Ninguno",
                "tiempo_base_minutos": 17.0
            }
        }
    ]

    for caso in casos_prueba:
        pred_c, pred_t = predecir_nuevo_escenario(
            clf_res["preprocesador"],
            clf_res["modelo"],
            reg_res["modelo"],
            caso["datos"]
        )
        t_base = caso["datos"]["tiempo_base_minutos"]
        print(f"\n{caso['nombre']}:")
        print(f"  Entrada: Troncal={caso['datos']['troncal']}, Clima={caso['datos']['clima']}, Hora={caso['datos']['hora']}:00, Incidente={caso['datos']['incidente_vial']}")
        print(f"  -> Nivel de Congestión Predicho: [{pred_c}]")
        print(f"  -> Tiempo Base: {t_base} min | Tiempo Real Estimado por Árbol: {pred_t:.1f} min (Retraso: +{pred_t - t_base:.1f} min)")

    return clf_res, reg_res


if __name__ == "__main__":
    ejecutar_pipeline_completo()

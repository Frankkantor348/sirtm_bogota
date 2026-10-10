"""
========================================================================================
MÓDULO: GENERACIÓN DE DATASET SINTÉTICO CALIBRADO (SIRTM BOGOTÁ)
========================================================================================
Propósito Académico:
    Generar un conjunto de datos estocástico pero representativo de la dinámica de viajes
    en el Sistema Inteligente de Rutas TransMilenio (SIRTM Bogotá). Este dataset sirve de
    insumo para el entrenamiento de modelos de Aprendizaje Supervisado (Árboles y Reglas
    de Decisión), conforme al Capítulo 17 de Palma Méndez (2008).

Fundamentación de los Datos:
    - Fuentes de referencia: Portal de Datos Abiertos de Bogotá y telemetría SAE TransMilenio.
    - Estaciones modeladas: 10 estaciones reales en 3 troncales (Caracas, Autonorte, Suba)
      más la ruta alimentadora Portal Usme <-> Marruecos.
    - Factores incorporados: Variación por franja horaria (pico/valle), día laboral vs. fin
      de semana, condiciones climatológicas (lluvia frecuente en Bogotá) e incidentes viales.
========================================================================================
"""

import numpy as np
import pandas as pd
import random
import os


def generar_dataset_transmilenio(n_muestras: int = 2500, semilla: int = 42) -> pd.DataFrame:
    """
    Sintetiza un DataFrame de viajes en TransMilenio con variables operativas y ambientales.

    Parámetros:
    -----------
    n_muestras : int, opcional (por defecto 2500)
        Número total de observaciones de viajes a simular en la red.
    semilla : int, opcional (por defecto 42)
        Semilla para el generador pseudoaleatorio que asegura reproducibilidad científica.

    Retorna:
    --------
    pd.DataFrame:
        Conjunto de datos estructurado con 16 columnas que abarcan identificadores,
        atributos descriptivos, predictores numéricos/categóricos y las variables objetivo
        tanto para clasificación (nivel_congestion) como para regresión (tiempo_real_minutos).
    """
    # 1. Fijar semillas para garantizar que los resultados de las pruebas sean reproducibles
    np.random.seed(semilla)
    random.seed(semilla)

    # 2. Definición de la infraestructura modelada en SIRTM Bogotá
    # Cada tupla contiene: (Origen, Destino, Troncal, Distancia en Km, Tiempo Base en Minutos)
    tramos_base = [
        ("Portal Usme", "Danubio", "Caracas", 3.2, 5),
        ("Danubio", "Museo Nacional", "Caracas", 9.8, 8),
        ("Museo Nacional", "Calle 72", "Caracas", 5.5, 12),
        ("Calle 72", "Héroes", "Autonorte", 2.1, 6),
        ("Héroes", "Calle 100", "Autonorte", 2.4, 7),
        ("Calle 100", "Portal Norte", "Autonorte", 8.2, 10),
        ("Portal Suba", "Niza", "Suba", 5.1, 9),
        ("Niza", "Calle 100", "Suba", 4.3, 8),
        ("Portal Usme", "Marruecos", "Alimentador", 3.0, 15),
        ("Calle 72", "Portal Usme", "Caracas", 18.5, 25),
        ("Portal Norte", "Calle 72", "Autonorte", 12.7, 23),
        ("Portal Suba", "Calle 100", "Suba", 9.4, 17),
        ("Portal Usme", "Calle 100", "Intertroncal", 23.0, 38),
        ("Portal Suba", "Portal Norte", "Intertroncal", 17.6, 27)
    ]

    # Dominios de atributos cualitativos
    dias = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
    climas = ["Despejado", "Lluvia_Ligera", "Lluvia_Fuerte"]
    incidentes = ["Ninguno", "Bloqueo_Parcial", "Falla_Mecanica", "Accidente_Transito"]

    # Vector para almacenar cada registro generado
    registros = []

    # 3. Iteración estocástica para construir cada observación de viaje
    for i in range(1, n_muestras + 1):
        # Selección aleatoria del trayecto físico
        origen, destino, troncal, distancia_km, tiempo_base = random.choice(tramos_base)

        # Asignación del día y tipo de jornada (Laboral vs. Fin de Semana)
        dia = random.choice(dias)
        es_laboral = 1 if dia in ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"] else 0
        tipo_dia = "Laboral" if es_laboral == 1 else "FinDeSemana"

        # Simulación de la hora del día basada en la curva de demanda real de Bogotá:
        # Se asigna mayor probabilidad a las horas pico (7-8 am y 5-6 pm).
        horas_prob = [
            0.02, 0.03,        # 05:00, 06:00
            0.12, 0.14,        # 07:00, 08:00 (Pico Mañana)
            0.05, 0.04, 0.04,  # 09:00, 10:00, 11:00
            0.04, 0.04, 0.05,  # 12:00, 13:00, 14:00
            0.06, 0.07,        # 15:00, 16:00
            0.12, 0.11,        # 17:00, 18:00 (Pico Tarde)
            0.04, 0.02, 0.01   # 19:00, 20:00, 21:00
        ]
        horas_posibles = list(range(5, 22))
        hora = np.random.choice(horas_posibles, p=horas_prob / np.sum(horas_prob))

        # Determinación de la franja horaria y factor multiplicador de congestión
        if 6 <= hora <= 8:
            franja = "Pico_Manana"
            factor_franja = 1.45 if es_laboral else 1.05
        elif 17 <= hora <= 19:
            franja = "Pico_Tarde"
            factor_franja = 1.50 if es_laboral else 1.10
        elif 9 <= hora <= 16:
            franja = "Valle_Dia"
            factor_franja = 1.10 if es_laboral else 1.00
        else:
            franja = "Valle_Noche"
            factor_franja = 1.00

        # Modelado del clima: en las tardes bogotanas (14:00 - 18:00) la probabilidad de lluvia es superior
        if hora in [14, 15, 16, 17, 18]:
            clima = np.random.choice(climas, p=[0.45, 0.35, 0.20])
        else:
            clima = np.random.choice(climas, p=[0.70, 0.22, 0.08])

        # Impacto del clima sobre la velocidad de circulación de los articulados
        factor_clima = 1.0 if clima == "Despejado" else (1.20 if clima == "Lluvia_Ligera" else 1.45)

        # Modelado de incidentes en la vía exclusiva de TransMilenio
        # En la mayoría de casos la vía opera sin novedad (82%), pero pueden presentarse contingencias
        incidente = np.random.choice(incidentes, p=[0.82, 0.08, 0.06, 0.04])
        factor_incidente = {
            "Ninguno": 1.0,
            "Falla_Mecanica": 1.25,
            "Bloqueo_Parcial": 1.40,
            "Accidente_Transito": 1.55
        }[incidente]

        # Simulación de la afluencia de pasajeros en la estación de abordaje (personas/hora)
        # Sigue una distribución normal centrada en la capacidad de la troncal
        base_afluencia = 1200 if troncal != "Alimentador" else 600
        if franja in ["Pico_Manana", "Pico_Tarde"] and es_laboral:
            afluencia = int(np.random.normal(loc=base_afluencia * 2.2, scale=350))
        elif not es_laboral:
            afluencia = int(np.random.normal(loc=base_afluencia * 0.9, scale=200))
        else:
            afluencia = int(np.random.normal(loc=base_afluencia * 1.2, scale=250))
        afluencia = max(150, afluencia)  # Restricción física de mínimo de usuarios

        # 4. Cálculo del tiempo real observado
        # Se compone del tiempo base multiplicado por los factores de congestión, clima e incidentes,
        # añadiendo una perturbación estocástica gaussiana (ruido blanco experimental)
        ruido = np.random.normal(loc=0, scale=0.8)
        factor_total = factor_franja * factor_clima * factor_incidente
        tiempo_real = round(max(tiempo_base * 0.85, (tiempo_base * factor_total) + ruido), 1)
        retraso = round(max(0.0, tiempo_real - tiempo_base), 1)

        # 5. Determinación de la variable objetivo categórica (Nivel de Congestión)
        # Esta etiqueta supervisada se clasifica con base en la tasa de sobrecosto temporal
        ratio_tiempo = tiempo_real / tiempo_base
        if ratio_tiempo <= 1.15 and retraso <= 3.0:
            nivel_congestion = "Bajo"
        elif ratio_tiempo <= 1.40 and retraso <= 8.0:
            nivel_congestion = "Medio"
        elif ratio_tiempo <= 1.75 or retraso <= 15.0:
            nivel_congestion = "Alto"
        else:
            nivel_congestion = "Critico"

        # 6. Almacenamiento estructurado del registro
        registros.append({
            "id_viaje": i,
            "origen": origen,
            "destino": destino,
            "troncal": troncal,
            "distancia_km": distancia_km,
            "dia_semana": dia,
            "tipo_dia": tipo_dia,
            "hora": int(hora),
            "franja_horaria": franja,
            "clima": clima,
            "afluencia_pasajeros": afluencia,
            "incidente_vial": incidente,
            "tiempo_base_minutos": tiempo_base,
            "tiempo_real_minutos": tiempo_real,
            "retraso_minutos": retraso,
            "nivel_congestion": nivel_congestion
        })

    # Construir y retornar el DataFrame de pandas
    df = pd.DataFrame(registros)
    return df


if __name__ == "__main__":
    # Ruta de destino dentro de la estructura modular del proyecto
    ruta_salida = os.path.join(os.path.dirname(__file__), "..", "datos", "dataset_viajes_transmilenio.csv")

    # Ejecución de la función generadora
    df = generar_dataset_transmilenio(2500)
    df.to_csv(ruta_salida, index=False, encoding="utf-8")

    # Confirmación en consola con resumen estadístico
    print(f"[OK] Dataset generado exitosamente en: {os.path.abspath(ruta_salida)}")
    print(f"Dimensiones del dataset: {df.shape[0]} filas x {df.shape[1]} columnas")
    print("\nDistribución porcentual de la variable objetivo 'nivel_congestion':")
    print((df["nivel_congestion"].value_counts(normalize=True).round(3) * 100).to_string())

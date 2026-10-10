"""
========================================================================================
MÓDULO DE PRUEBAS UNITARIAS: APRENDIZAJE SUPERVISADO (SIRTM BOGOTÁ)
========================================================================================
Propósito:
    Validar de forma automatizada y rigurosa la integridad del dataset de viajes, la
    calidad del preprocesamiento, el desempeño mínimo exigido a los modelos de árboles
    de decisión (clasificación y regresión), la extracción sintáctica de reglas lógicas
    IF-THEN y la capacidad de inferencia ante nuevos escenarios operativos de Bogotá.

Ejecución en consola:
    python -m unittest tests/test_aprendizaje_supervisado.py
========================================================================================
"""

import os
import unittest
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

# Importación de las funciones del componente supervisado a evaluar
from src.aprendizaje_supervisado import (
    cargar_y_preparar_datos,
    construir_preprocesador,
    entrenar_clasificador,
    entrenar_regresor,
    extraer_reglas_legibles,
    predecir_nuevo_escenario
)


class TestAprendizajeSupervisado(unittest.TestCase):
    """Suite de pruebas unitarias para el componente de Machine Learning Supervisado."""

    @classmethod
    def setUpClass(cls):
        """
        Método de inicialización de la suite de pruebas.
        Carga el dataset y entrena los modelos una sola vez para optimizar el tiempo de ejecución.
        """
        cls.df, cls.X, cls.y_clf, cls.y_reg = cargar_y_preparar_datos()
        cls.clf_res = entrenar_clasificador(cls.X, cls.y_clf)
        cls.reg_res = entrenar_regresor(cls.X, cls.y_reg)

    def test_01_integridad_dataset(self):
        """
        PRUEBA 1: Integridad y calidad del Dataset.
        Verifica que el dataset contenga al menos 2,000 registros, que no existan valores
        nulos (limpieza de datos) y que todas las columnas requeridas estén presentes.
        """
        # Validar tamaño muestral mínimo
        self.assertGreaterEqual(
            len(self.df), 2000,
            "El dataset debe tener al menos 2,000 registros para garantizar significancia estadística."
        )

        # Validar ausencia de valores faltantes (NaN)
        self.assertEqual(
            self.df.isnull().sum().sum(), 0,
            "El dataset no debe contener valores nulos o faltantes."
        )

        # Validar esquema de columnas indispensables
        columnas_esperadas = [
            "id_viaje", "origen", "destino", "troncal", "distancia_km",
            "hora", "franja_horaria", "clima", "afluencia_pasajeros",
            "incidente_vial", "tiempo_base_minutos", "tiempo_real_minutos", "nivel_congestion"
        ]
        for col in columnas_esperadas:
            self.assertIn(col, self.df.columns, f"Falta la columna indispensable '{col}' en el dataset.")

    def test_02_clasificador_metricas_minimas(self):
        """
        PRUEBA 2: Calidad métrica del Árbol de Clasificación.
        Verifica que la exactitud (Accuracy), el F1-Score ponderado y el puntaje medio de
        validación cruzada estratificada (5-Fold CV) superen el umbral académico del 70%.
        """
        acc = self.clf_res["accuracy"]
        f1 = self.clf_res["f1_weighted"]
        cv = self.clf_res["cv_mean"]

        self.assertGreater(
            acc, 0.70,
            f"La exactitud del clasificador ({acc:.2%}) debe superar el umbral mínimo del 70%."
        )
        self.assertGreater(
            f1, 0.70,
            f"El F1-score ponderado ({f1:.2%}) debe superar el umbral mínimo del 70%."
        )
        self.assertGreater(
            cv, 0.70,
            f"La validación cruzada 5-Fold ({cv:.2%}) debe ser consistente y superar el 70%."
        )

    def test_03_extraccion_reglas_decision(self):
        """
        PRUEBA 3: Extracción inductiva de Reglas de Decisión (Palma Méndez, 2008 - Cap. 17).
        Verifica que el árbol genere un conjunto no vacío de reglas lógicas, y que cada una
        cumpla con la estructura formal IF ... THEN ..., reportando soporte empírico y confianza.
        """
        reglas = self.clf_res["reglas"]

        # Validar que se haya inducido al menos una regla
        self.assertGreater(len(reglas), 0, "Se debe inducir al menos una regla de decisión a partir del árbol.")

        # Validar sintaxis y componentes en una muestra de las reglas extraídas
        for r in reglas[:5]:
            self.assertTrue(r.startswith("IF "), f"La regla debe iniciar con la cláusula 'IF ': {r}")
            self.assertIn("THEN Nivel_Congestion =", r, "La regla debe incluir la conclusión 'THEN'.")
            self.assertIn("Soporte:", r, "La regla debe cuantificar su soporte empírico en muestras.")
            self.assertIn("Confianza:", r, "La regla debe cuantificar su nivel de confianza porcentual.")

    def test_04_regresor_calidad_ajuste(self):
        """
        PRUEBA 4: Calidad de ajuste del Árbol de Regresión (Tiempo Real).
        Verifica que el coeficiente de determinación R² sea superior a 0.85 (alta capacidad
        explicativa) y que el Error Absoluto Medio (MAE) no supere los 5 minutos de desviación.
        """
        r2 = self.reg_res["r2"]
        mae = self.reg_res["mae"]

        self.assertGreater(
            r2, 0.85,
            f"El coeficiente R² ({r2:.4f}) debe ser superior a 0.85 para asegurar confiabilidad predictiva."
        )
        self.assertLess(
            mae, 5.0,
            f"El Error Absoluto Medio ({mae:.2f} min) debe ser inferior al límite de 5 minutos."
        )

    def test_05_inferencia_nuevo_escenario(self):
        """
        PRUEBA 5: Inferencia ante nuevas observaciones operativas.
        Simula una solicitud de predicción con datos de un viaje en hora pico bajo lluvia fuerte
        y accidente vial, comprobando que responda con una etiqueta de congestión válida y un
        tiempo de viaje numérico positivo.
        """
        nuevo_caso = {
            "troncal": "Caracas",
            "distancia_km": 12.0,
            "tipo_dia": "Laboral",
            "hora": 18,
            "franja_horaria": "Pico_Tarde",
            "clima": "Lluvia_Fuerte",
            "afluencia_pasajeros": 2800,
            "incidente_vial": "Accidente_Transito",
            "tiempo_base_minutos": 20.0
        }

        # Ejecutar inferencia
        pred_c, pred_t = predecir_nuevo_escenario(
            self.clf_res["preprocesador"],
            self.clf_res["modelo"],
            self.reg_res["modelo"],
            nuevo_caso
        )

        # Validar dominio de la clase predicha y consistencia temporal
        self.assertIn(
            pred_c, ["Bajo", "Medio", "Alto", "Critico"],
            f"La categoría predicha '{pred_c}' no pertenece a los niveles de congestión definidos."
        )
        self.assertGreater(
            pred_t, 0.0,
            "El tiempo de viaje predicho debe ser estrictamente positivo."
        )


if __name__ == "__main__":
    unittest.main()

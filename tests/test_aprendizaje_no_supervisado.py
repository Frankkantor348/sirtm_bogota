"""
========================================================================================
MÓDULO DE PRUEBAS UNITARIAS: APRENDIZAJE NO SUPERVISADO (SIRTM BOGOTÁ)
========================================================================================
Propósito:
    Validar la estabilidad, convergencia y consistencia matemática de los modelos de
    agrupamiento (Clustering K-Means, Evaluación de k por Silueta/Inercia, y Perfilamiento)
    conforme al Capítulo 16 de Palma Méndez (2008).

Ejecución en consola:
    python -m unittest tests/test_aprendizaje_no_supervisado.py
========================================================================================
"""

import unittest
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from src.aprendizaje_no_supervisado import (
    cargar_y_preparar_datos_clustering,
    evaluar_numero_optimo_k,
    entrenar_kmeans,
    caracterizar_clusters
)


class TestAprendizajeNoSupervisado(unittest.TestCase):
    """Suite de pruebas para validar los componentes de agrupamiento no supervisado."""

    @classmethod
    def setUpClass(cls):
        """Inicialización de datos y ajuste previo de modelos."""
        cls.df, cls.X_scaled, cls.feature_cols = cargar_y_preparar_datos_clustering()
        cls.res_opt = evaluar_numero_optimo_k(cls.X_scaled, k_min=2, k_max=5)
        cls.res_km = entrenar_kmeans(cls.X_scaled, k=3)
        cls.resumen = caracterizar_clusters(cls.df, cls.res_km["etiquetas"], cls.feature_cols)

    def test_01_escalamiento_caracteristicas(self):
        """
        PRUEBA 1: Normalización de datos cuantitativos.
        Verifica que la matriz de características tenga media cercana a 0 (±0.05)
        y desviación estándar unitaria (1.0 ±0.05) para garantizar equidistancia euclidiana.
        """
        media = np.mean(self.X_scaled, axis=0)
        std = np.std(self.X_scaled, axis=0)
        np.testing.assert_allclose(media, 0.0, atol=0.05, err_msg="La media normalizada debe ser ~0.")
        np.testing.assert_allclose(std, 1.0, atol=0.05, err_msg="La desviación estándar normalizada debe ser ~1.")

    def test_02_evaluacion_k_silueta(self):
        """
        PRUEBA 2: Métricas de cohesión y separación (Silueta).
        Verifica que para todos los valores de k evaluados, el coeficiente de silueta sea positivo.
        """
        siluetas = self.res_opt["siluetas"]
        for s in siluetas:
            self.assertGreater(s, 0.20, "El coeficiente de silueta debe ser positivo y superar 0.20.")

    def test_03_convergencia_kmeans(self):
        """
        PRUEBA 3: Convergencia y asignación exhaustiva de clusters K-Means.
        Verifica que cada punto esté asignado exactamente a un cluster en [0, 1, 2]
        y que no existan clusters vacíos.
        """
        etiquetas = self.res_km["etiquetas"]
        self.assertEqual(len(etiquetas), len(self.df))
        clases_unicas = np.unique(etiquetas)
        self.assertEqual(len(clases_unicas), 3, "Deben existir exactamente 3 clusters no vacíos.")

    def test_04_perfilamiento_operativo(self):
        """
        PRUEBA 4: Caracterización y segmentación coherente de los perfiles.
        Verifica que el DataFrame de perfiles contenga los 3 clusters y que la suma
        porcentual sea 100%.
        """
        self.assertEqual(len(self.resumen), 3)
        self.assertAlmostEqual(self.resumen["porcentaje"].sum(), 100.0, delta=0.5)
        self.assertIn("perfil_operativo", self.resumen.columns)


if __name__ == "__main__":
    unittest.main()

"""
Módulo de Pruebas Unitarias para el Sistema Inteligente de Rutas TransMilenio.
Ejecución: python -m unittest tests/test_rutas.py
"""

import unittest
from src.base_conocimiento import BaseConocimiento
from src.motor_inferencia import MotorInferencia
from src.busqueda_astar import BusquedaAStar


class TestSIRTMBogota(unittest.TestCase):
    """Conjunto de 8 pruebas unitarias requeridas para validar la base, motor y A*."""

    def setUp(self):
        """Inicializa las instancias principales antes de cada prueba."""
        self.bc = BaseConocimiento()
        self.motor = MotorInferencia(self.bc)
        self.astar = BusquedaAStar(self.bc, self.motor)

    def test_01_cargar_estaciones(self):
        """Prueba 1: Base de conocimiento carga 10 estaciones únicas correctamente."""
        estaciones_unicas = self.bc.listar_estaciones()
        self.assertEqual(len(estaciones_unicas), 10)
        self.assertIn("Portal Usme", estaciones_unicas)
        self.assertIn("Portal Norte", estaciones_unicas)
        self.assertIn("Portal Suba", estaciones_unicas)
        self.assertIn("Calle 72", estaciones_unicas)
        self.assertIn("Calle 100", estaciones_unicas)

    def test_02_obtener_vecinos(self):
        """Prueba 2: obtener_vecinos retorna vecinos válidos para Portal Usme."""
        vecinos = self.bc.obtener_vecinos("Portal Usme")
        destinos = [v[0] for v in vecinos]
        self.assertIn("Danubio", destinos)
        self.assertIn("Marruecos", destinos)

    def test_03_aplicar_bidireccionalidad(self):
        """Prueba 3: Motor de inferencia aplica la regla de bidireccionalidad."""
        conexiones = self.motor.obtener_conexiones_completas()
        # Verificar que la conexión inversa Danubio -> Portal Usme fue inferida
        tiene_inversa = any(
            c.origen == "Danubio" and c.destino == "Portal Usme" for c in conexiones
        )
        self.assertTrue(tiene_inversa)

    def test_04_detectar_transbordos(self):
        """Prueba 4: Motor de inferencia detecta transbordos en Calle 72."""
        transbordos = self.motor.aplicar_regla_estacion_compartida()
        transbordo_c72 = any(t["estacion"] == "Calle 72" for t in transbordos)
        self.assertTrue(transbordo_c72)

    def test_05_ruta_usme_norte(self):
        """Prueba 5: Encuentra ruta Portal Usme -> Portal Norte con transbordo en Calle 72."""
        resultado = self.astar.encontrar_ruta("Portal Usme", "Portal Norte")
        self.assertIsNotNone(resultado)
        ruta, tiempo, transbordos, lineas = resultado
        self.assertIn("Portal Usme", ruta)
        self.assertIn("Calle 72", ruta)
        self.assertIn("Portal Norte", ruta)
        self.assertEqual(transbordos, 1)
        self.assertEqual(tiempo, 53)  # 5+8+12 + 5(transbordo) + 6+7+10 = 53 min

    def test_06_ruta_suba_norte(self):
        """Prueba 6: Encuentra ruta Portal Suba -> Portal Norte con transbordo en Calle 100."""
        resultado = self.astar.encontrar_ruta("Portal Suba", "Portal Norte")
        self.assertIsNotNone(resultado)
        ruta, tiempo, transbordos, lineas = resultado
        self.assertIn("Portal Suba", ruta)
        self.assertIn("Calle 100", ruta)
        self.assertIn("Portal Norte", ruta)
        self.assertEqual(transbordos, 1)
        self.assertEqual(tiempo, 32)  # 9+8 + 5(transbordo) + 10 = 32 min

    def test_07_estacion_inexistente(self):
        """Prueba 7: Se retorna None si no hay ruta o la estación no existe."""
        resultado = self.astar.encontrar_ruta("Estacion Fantasma", "Portal Norte")
        self.assertIsNone(resultado)
        resultado2 = self.astar.encontrar_ruta("Portal Usme", "Estacion Inexistente")
        self.assertIsNone(resultado2)

    def test_08_heuristica_admisible(self):
        """Prueba 8: La heurística es admisible (h(n) <= h*(n) nunca sobreestima el costo real)."""
        estaciones = self.bc.listar_estaciones()
        for orig in estaciones:
            for dest in estaciones:
                h_val = self.astar.heuristica(orig, dest)
                res = self.astar.encontrar_ruta(orig, dest)
                if res is not None:
                    costo_real = res[1]
                    self.assertLessEqual(
                        h_val,
                        costo_real,
                        f"La heurística {h_val} sobreestimó el costo real {costo_real} entre {orig} y {dest}",
                    )


if __name__ == "__main__":
    unittest.main()

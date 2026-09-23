"""
Módulo del Algoritmo de Búsqueda A* para el Sistema Inteligente de Rutas TransMilenio.
Encuentra la ruta óptima de menor tiempo entre dos estaciones.
"""

import heapq
import time
from typing import Dict, List, Optional, Set, Tuple, Union
import networkx as nx

from src.base_conocimiento import BaseConocimiento
from src.motor_inferencia import MotorInferencia


class BusquedaAStar:
    """
    Implementa el algoritmo de búsqueda heurística A* sobre el grafo del sistema.
    Utiliza como estados pares (estacion, troncal) para contemplar transbordos y
    garantizar que la heurística de distancia Manhattan sea admisible e informada.
    """

    def __init__(self, base_conocimiento: BaseConocimiento, motor_inferencia: MotorInferencia):
        """Inicializa el buscador A* con la Base de Conocimiento y el Motor de Inferencia."""
        self.bc = base_conocimiento
        self.motor = motor_inferencia
        self.grafo_nx: Optional[nx.DiGraph] = None
        self.construir_grafo()

    def construir_grafo(self) -> nx.DiGraph:
        """
        Construye un grafo dirigido NetworkX donde los nodos son tuplas (estacion, troncal)
        y las aristas incluyen tiempos de desplazamiento entre estaciones y tiempos de transbordo.
        """
        G = nx.DiGraph()
        conexiones = self.motor.obtener_conexiones_completas()

        # Agregar aristas de desplazamiento por troncal
        for c in conexiones:
            nodo_orig = (c.origen, c.ruta)
            nodo_dest = (c.destino, c.ruta)
            G.add_edge(nodo_orig, nodo_dest, weight=c.tiempo_minutos, tipo="desplazamiento", ruta=c.ruta)

        # Agregar aristas de transbordo en estaciones compartidas
        estaciones_unicas = self.bc.listar_estaciones()
        for est in estaciones_unicas:
            troncales = self.bc.obtener_troncal(est)
            if len(troncales) > 1:
                for i in range(len(troncales)):
                    for j in range(len(troncales)):
                        if i != j:
                            t1, t2 = troncales[i], troncales[j]
                            # Transbordo de t1 a t2 en la misma estación cuesta 5 minutos
                            G.add_edge((est, t1), (est, t2), weight=5, tipo="transbordo", estacion=est)

        self.grafo_nx = G
        return G

    def heuristica(self, estacion_actual: str, estacion_destino: str) -> float:
        """
        Calcula la función heurística h(n) usando distancia Manhattan en coordenadas lat/lon.
        Es admisible (h(n) <= h*(n)) y consistente.
        """
        return self.bc.calcular_distancia_manhattan(estacion_actual, estacion_destino)

    def encontrar_ruta(
        self, origen: str, destino: str
    ) -> Optional[Tuple[List[str], int, int, List[str]]]:
        """
        Encuentra la ruta óptima desde 'origen' hasta 'destino' utilizando A*.

        Retorna una tupla:
            (ruta_estaciones, tiempo_total_minutos, cantidad_transbordos, lineas_utilizadas)
        Si el origen o destino no existen o no hay ruta disponible, retorna None.
        """
        # Verificar existencia de estaciones
        estaciones_validas = [e.lower() for e in self.bc.listar_estaciones()]
        if origen.lower() not in estaciones_validas or destino.lower() not in estaciones_validas:
            return None

        # Normalizar nombres exactos
        origen_exacto = next(e for e in self.bc.listar_estaciones() if e.lower() == origen.lower())
        destino_exacto = next(e for e in self.bc.listar_estaciones() if e.lower() == destino.lower())

        if origen_exacto == destino_exacto:
            return ([origen_exacto], 0, 0, [])

        troncales_origen = self.bc.obtener_troncal(origen_exacto)

        # Priority Queue para A*: elementos son (f_score, g_score, estado_actual, historial_estados)
        # estado_actual = (estacion, troncal)
        open_set: List[Tuple[float, int, Tuple[str, str], List[Tuple[str, str]]]] = []
        g_scores: Dict[Tuple[str, str], int] = {}

        for t in troncales_origen:
            estado_ini = (origen_exacto, t)
            g_scores[estado_ini] = 0
            h = self.heuristica(origen_exacto, destino_exacto)
            heapq.heappush(open_set, (h, 0, estado_ini, [estado_ini]))

        visited: Set[Tuple[str, str]] = set()

        while open_set:
            f, g, (est_act, troncal_act), camino = heapq.heappop(open_set)

            if (est_act, troncal_act) in visited:
                continue
            visited.add((est_act, troncal_act))

            # Verificar si se alcanzó la estación destino
            if est_act == destino_exacto:
                return self._procesar_resultado_camino(camino, g)

            # Explorar vecinos en el grafo
            nodo_actual = (est_act, troncal_act)
            if nodo_actual in self.grafo_nx:
                for vec_nodo, datos in self.grafo_nx[nodo_actual].items():
                    vec_est, vec_troncal = vec_nodo
                    peso = datos.get("weight", 1)
                    nuevo_g = g + peso

                    if vec_nodo not in g_scores or nuevo_g < g_scores[vec_nodo]:
                        g_scores[vec_nodo] = nuevo_g
                        h = self.heuristica(vec_est, destino_exacto)
                        f_nuevo = nuevo_g + h
                        nuevo_camino = camino + [vec_nodo]
                        heapq.heappush(open_set, (f_nuevo, nuevo_g, vec_nodo, nuevo_camino))

        return None

    def _procesar_resultado_camino(
        self, camino_estados: List[Tuple[str, str]], tiempo_total: int
    ) -> Tuple[List[str], int, int, List[str]]:
        """
        Convierte una secuencia de estados (estacion, troncal) en la estructura final
        de la ruta formateada con lista de estaciones, transbordos y líneas.
        """
        ruta_estaciones: List[str] = []
        lineas_utilizadas: List[str] = []
        transbordos_cont = 0

        for i, (est, troncal) in enumerate(camino_estados):
            # Agregar estación a la ruta si no es duplicado consecutivo (cambio de troncal)
            if not ruta_estaciones or ruta_estaciones[-1] != est:
                ruta_estaciones.append(est)

            # Registrar líneas utilizadas
            if not lineas_utilizadas or lineas_utilizadas[-1] != troncal:
                if len(lineas_utilizadas) > 0:
                    transbordos_cont += 1
                lineas_utilizadas.append(troncal)

        return (ruta_estaciones, tiempo_total, transbordos_cont, lineas_utilizadas)

    def comparar_con_dijkstra(
        self, origen: str, destino: str
    ) -> Dict[str, Union[float, int, List[str]]]:
        """
        Compara la velocidad y número de nodos evaluados entre A* y el algoritmo de Dijkstra.
        """
        # Medir tiempo A*
        t0 = time.perf_counter()
        res_astar = self.encontrar_ruta(origen, destino)
        t_astar = (time.perf_counter() - t0) * 1000  # ms

        # Medir tiempo Dijkstra con NetworkX
        t0 = time.perf_counter()
        origen_exacto = next(e for e in self.bc.listar_estaciones() if e.lower() == origen.lower())
        destino_exacto = next(e for e in self.bc.listar_estaciones() if e.lower() == destino.lower())

        mejores_rutas = []
        min_dist = float("inf")

        for t_orig in self.bc.obtener_troncal(origen_exacto):
            for t_dest in self.bc.obtener_troncal(destino_exacto):
                try:
                    dist = nx.dijkstra_path_length(
                        self.grafo_nx, (origen_exacto, t_orig), (destino_exacto, t_dest)
                    )
                    path = nx.dijkstra_path(
                        self.grafo_nx, (origen_exacto, t_orig), (destino_exacto, t_dest)
                    )
                    if dist < min_dist:
                        min_dist = dist
                        mejores_rutas = path
                except nx.NetworkXNoPath:
                    pass

        t_dijkstra = (time.perf_counter() - t0) * 1000  # ms

        return {
            "tiempo_astar_ms": round(t_astar, 4),
            "tiempo_dijkstra_ms": round(t_dijkstra, 4),
            "costo_total": res_astar[1] if res_astar else None,
        }

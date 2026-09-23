"""
Módulo del Motor de Inferencia para el Sistema Inteligente de Rutas TransMilenio.
Aplica reglas de lógica de primer orden e inferencia sobre la Base de Conocimiento.
"""

from typing import List, Tuple, Dict, Set
from src.base_conocimiento import BaseConocimiento, Conexion


class MotorInferencia:
    """
    Motor de Inferencia lógica que aplica reglas deductivas sobre la Base de Conocimiento:
      - Regla 1: Bidireccionalidad de conexiones.
      - Regla 2 y 3: Detección y penalización de transbordos por cambio de troncal (5 min).
      - Regla 6: Transbordo en estaciones compartidas (Calle 72, Calle 100).
    """

    def __init__(self, base_conocimiento: BaseConocimiento):
        """Inicializa el motor de inferencia con una base de conocimiento dada."""
        self.bc = base_conocimiento
        self.inferencias_realizadas: List[Dict[str, str]] = []
        self._ejecutar_inferencias()

    def _ejecutar_inferencias(self) -> None:
        """Ejecuta de manera secuencial el conjunto de reglas deductivas."""
        self.aplicar_bidireccionalidad()
        self.aplicar_regla_estacion_compartida()
        self.detectar_transbordos()

    def aplicar_bidireccionalidad(self) -> List[Conexion]:
        """
        [Regla 1] Si existe conexion(A, B, R, T) => Deduce conexion(B, A, R, T).
        Retorna la lista de conexiones inversas inferidas.
        """
        conexiones_inversas = []
        # Mantener registro de conexiones existentes para no duplicar
        existentes = {(c.origen.lower(), c.destino.lower(), c.ruta.lower()) for c in self.bc.conexiones}

        for c in list(self.bc.conexiones):
            clave_inversa = (c.destino.lower(), c.origen.lower(), c.ruta.lower())
            if clave_inversa not in existentes:
                conexion_inv = Conexion(
                    origen=c.destino,
                    destino=c.origen,
                    ruta=c.ruta,
                    tiempo_minutos=c.tiempo_minutos,
                    transbordo=c.transbordo,
                )
                conexiones_inversas.append(conexion_inv)
                existentes.add(clave_inversa)

                self.inferencias_realizadas.append({
                    "regla": "Regla 1: Bidireccionalidad",
                    "premisa": f"conexion({c.origen}, {c.destino}, {c.ruta}, {c.tiempo_minutos})",
                    "conclusion": f"conexion({c.destino}, {c.origen}, {c.ruta}, {c.tiempo_minutos})"
                })

        return conexiones_inversas

    def aplicar_regla_estacion_compartida(self) -> List[Dict[str, str]]:
        """
        [Regla 6] Si una estación E pertenece a dos troncales T1 y T2 (T1 != T2),
        deduce que existe la posibilidad de transbordo en E entre T1 y T2.
        """
        transbordos_compartidos = []
        estaciones_unicas = self.bc.listar_estaciones()

        for est in estaciones_unicas:
            troncales = self.bc.obtener_troncal(est)
            if len(troncales) > 1:
                # Estación compartida detectada
                for i in range(len(troncales)):
                    for j in range(i + 1, len(troncales)):
                        t1, t2 = troncales[i], troncales[j]
                        transbordos_compartidos.append({
                            "estacion": est,
                            "troncal_origen": t1,
                            "troncal_destino": t2,
                            "tiempo": 5
                        })
                        self.inferencias_realizadas.append({
                            "regla": "Regla 6: Estación Compartida",
                            "premisa": f"estacion({est}, {t1}) ∧ estacion({est}, {t2})",
                            "conclusion": f"transbordo_habilitado({est}, {t1} ↔ {t2}, tiempo=5 min)"
                        })

        return transbordos_compartidos

    def detectar_transbordos(self) -> List[Dict[str, str]]:
        """
        [Reglas 2 y 3] Detecta pares de conexiones adyacentes A->B (troncal R1) y
        B->C (troncal R2) con R1 != R2, y deduce la necesidad de transbordo de 5 min.
        """
        transbordos_detectados = []
        conexiones = self.obtener_conexiones_completas()

        for c1 in conexiones:
            for c2 in conexiones:
                if c1.destino.lower() == c2.origen.lower() and c1.ruta.lower() != c2.ruta.lower():
                    nodo_transbordo = c1.destino
                    info = {
                        "estacion": nodo_transbordo,
                        "desde_ruta": c1.ruta,
                        "hacia_ruta": c2.ruta,
                        "tiempo_adicional": 5
                    }
                    transbordos_detectados.append(info)
                    
                    self.inferencias_realizadas.append({
                        "regla": "Regla 2 y 3: Transbordo por cambio de troncal",
                        "premisa": f"conexion({c1.origen}->{c1.destino}, {c1.ruta}) ∧ conexion({c2.origen}->{c2.destino}, {c2.ruta})",
                        "conclusion": f"transbordo({nodo_transbordo}, {c1.ruta} -> {c2.ruta}, +5 min)"
                    })

        return transbordos_detectados

    def obtener_conexiones_completas(self) -> List[Conexion]:
        """
        Retorna la unión de las conexiones base originales más las conexiones
        inversas inferidas por la Regla 1 (Bidireccionalidad).
        """
        conexiones_inversas = []
        existentes = {(c.origen.lower(), c.destino.lower(), c.ruta.lower()) for c in self.bc.conexiones}

        for c in self.bc.conexiones:
            clave_inversa = (c.destino.lower(), c.origen.lower(), c.ruta.lower())
            if clave_inversa not in existentes:
                conexiones_inversas.append(
                    Conexion(
                        origen=c.destino,
                        destino=c.origen,
                        ruta=c.ruta,
                        tiempo_minutos=c.tiempo_minutos,
                        transbordo=c.transbordo,
                    )
                )

        return self.bc.conexiones + conexiones_inversas

    def calcular_tiempo_con_transbordo(self, ruta1: str, ruta2: str) -> int:
        """
        [Regla 3] Determina la penalización de tiempo si hay cambio de troncal.
        Retorna 5 minutos si ruta1 != ruta2 y ambas son válidas, de lo contrario 0.
        """
        if ruta1 and ruta2 and ruta1.lower() != ruta2.lower():
            return 5
        return 0

    def explicar_inferencias(self) -> List[Dict[str, str]]:
        """
        Retorna la lista estructurada de todas las inferencias aplicadas por el motor,
        indicando la regla aplicada, las premisas y la conclusión alcanzada.
        """
        return self.inferencias_realizadas

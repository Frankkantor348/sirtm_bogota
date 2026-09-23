"""
Módulo de la Base de Conocimiento para el Sistema Inteligente de Rutas TransMilenio.
Carga y representa los hechos (estaciones, conexiones y transbordos) del sistema.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple, Union, Optional


@dataclass
class Estacion:
    """Representa una estación del sistema TransMilenio."""
    nombre: str
    troncal: str
    latitud: float
    longitud: float


@dataclass
class Conexion:
    """Representa una conexión directa entre dos estaciones."""
    origen: str
    destino: str
    ruta: str
    tiempo_minutos: int
    transbordo: bool = False


class BaseConocimiento:
    """
    Gestiona la base de conocimiento con hechos reales de TransMilenio.
    Carga los hechos desde hechos.txt y proporciona métodos para consultar
    estaciones, conexiones, vecinos y calcular la heurística Manhattan.
    """

    def __init__(self, ruta_hechos: Optional[Union[str, Path]] = None):
        """
        Inicializa la base de conocimiento. Si no se provee ruta_hechos,
        intenta cargar desde el archivo predeterminado conocimiento/hechos.txt
        o genera la base por defecto.
        """
        self.estaciones: List[Estacion] = []
        self.conexiones: List[Conexion] = []
        self.transbordos_conocidos: List[Tuple[str, str, str, int]] = []

        if ruta_hechos is None:
            # Buscar el archivo hecho.txt relativo al directorio actual o del proyecto
            posible_ruta = Path(__file__).parent.parent / "conocimiento" / "hechos.txt"
            if posible_ruta.exists():
                ruta_hechos = posible_ruta

        if ruta_hechos and Path(ruta_hechos).exists():
            self._cargar_desde_archivo(Path(ruta_hechos))
        else:
            self._cargar_hechos_predeterminados()

    def _cargar_desde_archivo(self, archivo: Path) -> None:
        """Lee y parsea el archivo de hechos en formato Prolog/texto."""
        with open(archivo, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea or linea.startswith("%"):
                    continue

                if linea.startswith("estacion("):
                    # Formato: estacion(Nombre, Troncal, Latitud, Longitud).
                    contenido = linea[len("estacion(") : -2]
                    partes = [p.strip() for p in contenido.split(",")]
                    if len(partes) == 4:
                        nombre, troncal, lat, lon = partes
                        self.estaciones.append(
                            Estacion(
                                nombre=nombre,
                                troncal=troncal,
                                latitud=float(lat),
                                longitud=float(lon),
                            )
                        )

                elif linea.startswith("conexion("):
                    # Formato: conexion(Origen, Destino, Ruta, Tiempo).
                    contenido = linea[len("conexion(") : -2]
                    partes = [p.strip() for p in contenido.split(",")]
                    if len(partes) == 4:
                        origen, destino, ruta, tiempo = partes
                        self.conexiones.append(
                            Conexion(
                                origen=origen,
                                destino=destino,
                                ruta=ruta,
                                tiempo_minutos=int(tiempo),
                            )
                        )

                elif linea.startswith("transbordo("):
                    # Formato: transbordo(Estacion, Troncal1, Troncal2, Tiempo).
                    contenido = linea[len("transbordo(") : -2]
                    partes = [p.strip() for p in contenido.split(",")]
                    if len(partes) == 4:
                        estacion, t1, t2, tiempo = partes
                        self.transbordos_conocidos.append(
                            (estacion, t1, t2, int(tiempo))
                        )

    def _cargar_hechos_predeterminados(self) -> None:
        """Carga los hechos base definidos en los requerimientos del proyecto."""
        datos_estaciones = [
            ("Portal Usme", "Caracas", 4.5280, -74.1180),
            ("Danubio", "Caracas", 4.5480, -74.1150),
            ("Museo Nacional", "Caracas", 4.6120, -74.0980),
            ("Calle 72", "Caracas", 4.6580, -74.0620),
            ("Calle 72", "Autonorte", 4.6580, -74.0620),
            ("Heroes", "Autonorte", 4.6750, -74.0580),
            ("Calle 100", "Autonorte", 4.6890, -74.0520),
            ("Calle 100", "Suba", 4.6890, -74.0520),
            ("Portal Norte", "Autonorte", 4.7540, -74.0480),
            ("Portal Suba", "Suba", 4.7420, -74.0940),
            ("Niza", "Suba", 4.6980, -74.0720),
            ("Marruecos", "Alimentadora", 4.5350, -74.1250),
        ]
        for nombre, troncal, lat, lon in datos_estaciones:
            self.estaciones.append(Estacion(nombre, troncal, lat, lon))

        datos_conexiones = [
            ("Portal Usme", "Danubio", "Caracas", 5),
            ("Danubio", "Museo Nacional", "Caracas", 8),
            ("Museo Nacional", "Calle 72", "Caracas", 12),
            ("Calle 72", "Heroes", "Autonorte", 6),
            ("Heroes", "Calle 100", "Autonorte", 7),
            ("Calle 100", "Portal Norte", "Autonorte", 10),
            ("Portal Suba", "Niza", "Suba", 9),
            ("Niza", "Calle 100", "Suba", 8),
            ("Portal Usme", "Marruecos", "Alimentadora", 15),
        ]
        for orig, dest, ruta, t in datos_conexiones:
            self.conexiones.append(Conexion(orig, dest, ruta, t))

        self.transbordos_conocidos = [
            ("Calle 72", "Caracas", "Autonorte", 5),
            ("Calle 100", "Autonorte", "Suba", 5),
        ]

    def listar_estaciones(self) -> List[str]:
        """Retorna la lista de nombres únicos de estaciones disponibles."""
        nombres = []
        for e in self.estaciones:
            if e.nombre not in nombres:
                nombres.append(e.nombre)
        return nombres

    def obtener_troncal(self, nombre_estacion: str) -> List[str]:
        """
        Retorna la lista de troncales a las que pertenece una estación.
        Una estación compartida devolverá múltiples troncales.
        """
        troncales = []
        for e in self.estaciones:
            if e.nombre.lower() == nombre_estacion.lower():
                if e.troncal not in troncales:
                    troncales.append(e.troncal)
        return troncales

    def es_estacion_compartida(self, nombre_estacion: str) -> bool:
        """
        Determina si una estación es compartida entre dos o más troncales
        (ej. Calle 72, Calle 100).
        """
        return len(self.obtener_troncal(nombre_estacion)) > 1

    def obtener_coordenadas(self, nombre_estacion: str) -> Optional[Tuple[float, float]]:
        """Retorna las coordenadas (latitud, longitud) de una estación por su nombre."""
        for e in self.estaciones:
            if e.nombre.lower() == nombre_estacion.lower():
                return (e.latitud, e.longitud)
        return None

    def obtener_vecinos(self, nombre_estacion: str) -> List[Tuple[str, int, str]]:
        """
        Retorna la lista de vecinos directos desde una estación dada en las
        conexiones base. Cada elemento es una tupla (destino, tiempo_minutos, ruta).
        """
        vecinos = []
        nombre_lower = nombre_estacion.lower()
        for c in self.conexiones:
            if c.origen.lower() == nombre_lower:
                vecinos.append((c.destino, c.tiempo_minutos, c.ruta))
        return vecinos

    def calcular_distancia_manhattan(
        self, estacion_a: str, estacion_b: str
    ) -> float:
        """
        Calcula la distancia Manhattan entre las coordenadas geográficas de dos
        estaciones y la convierte a un tiempo estimado en minutos (heurística).

        Heurística h(n) = (|latA - latB| + |lonA - lonB|) * factor_escala
        Garantiza admisible (nunca sobreestima el tiempo real de desplazamiento).
        """
        coords_a = self.obtener_coordenadas(estacion_a)
        coords_b = self.obtener_coordenadas(estacion_b)

        if not coords_a or not coords_b:
            return 0.0

        lat_a, lon_a = coords_a
        lat_b, lon_b = coords_b

        dist_grados = abs(lat_a - lat_b) + abs(lon_a - lon_b)

        # Factor de escala: 80 minutos por grado de distancia geográfica Manhattan.
        # Esto produce estimaciones optimistas e infravaloradas (admisibles).
        # Ejemplo: Usme a Portal Norte ~0.296 grados => 23.68 min (Tiempo real: 53 min).
        FACTOR_ESCALA_MINUTOS = 80.0
        return dist_grados * FACTOR_ESCALA_MINUTOS

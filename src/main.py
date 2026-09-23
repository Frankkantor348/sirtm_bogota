"""
Punto de entrada principal para la aplicación SIRTM Bogotá.
Proporciona un menú interactivo en consola y soporte para ejecución con CLI.
"""

import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Optional

# Asegurar que la salida en consola Windows soporte UTF-8 (emojis y caracteres especiales)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Asegurar que el directorio raíz del proyecto esté en sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import networkx as nx

from src.base_conocimiento import BaseConocimiento
from src.motor_inferencia import MotorInferencia
from src.busqueda_astar import BusquedaAStar


# Códigos de color ANSI para consola
COLOR_TITULO = "\033[1;36m"
COLOR_EXITO = "\033[1;32m"
COLOR_ALERTA = "\033[1;33m"
COLOR_INFO = "\033[1;34m"
COLOR_TRANSBORDO = "\033[1;35m"
COLOR_RESET = "\033[0m"
COLOR_NEGRILLA = "\033[1m"


def imprimir_encabezado():
    """Imprime el banner del sistema."""
    print(f"{COLOR_TITULO}")
    print("=" * 70)
    print("   SISTEMA INTELIGENTE DE RUTAS TRANSMILENIO (SIRTM BOGOTÁ)   ")
    print("     Razonamiento Lógico e Inferencia con Algoritmo A*        ")
    print("=" * 70)
    print(f"{COLOR_RESET}")


def mostrar_estaciones(bc: BaseConocimiento):
    """Muestra la lista de estaciones disponibles numeradas con su troncal."""
    estaciones = bc.listar_estaciones()
    print(f"{COLOR_NEGRILLA}ESTACIONES DISPONIBLES EN LA RED:{COLOR_RESET}")
    print("-" * 50)
    for idx, est in enumerate(estaciones, 1):
        troncales = ", ".join(bc.obtener_troncal(est))
        es_comp = " [Compartida]" if bc.es_estacion_compartida(est) else ""
        print(f"  {idx:2d}. {est:<20} ({COLOR_INFO}{troncales}{COLOR_RESET}){es_comp}")
    print("-" * 50)


def mostrar_explicacion_inferencias(motor: MotorInferencia):
    """Muestra el reporte detallado de las inferencias lógicas aplicadas."""
    print(f"\n{COLOR_TITULO}--- EXPLICACIÓN DE INFERENCIAS LÓGICAS APLICADAS ---{COLOR_RESET}")
    inferencias = motor.explicar_inferencias()
    for idx, inf in enumerate(inferencias, 1):
        print(f"\n{COLOR_NEGRILLA}[Inferencia #{idx}]{COLOR_RESET}")
        print(f"  📌 {COLOR_INFO}Regla:{COLOR_RESET} {inf['regla']}")
        print(f"  🔹 {COLOR_ALERTA}Premisa:{COLOR_RESET} {inf['premisa']}")
        print(f"  💡 {COLOR_EXITO}Conclusión:{COLOR_RESET} {inf['conclusion']}")
    print("-" * 70)


def mostrar_ruta_detallada(
    origen: str,
    destino: str,
    resultado: Tuple[List[str], int, int, List[str]],
    bc: BaseConocimiento,
    motor: MotorInferencia,
    astar: BusquedaAStar,
):
    """Formatea y muestra la ruta calculada paso a paso."""
    ruta_estaciones, tiempo_total, transbordos, lineas_usadas = resultado

    print(f"\n{COLOR_EXITO}=== RUTA OPTIMA ENCONTRADA ==={COLOR_RESET}")
    print(f"📍 {COLOR_NEGRILLA}Origen:{COLOR_RESET} {origen}")
    print(f"🏁 {COLOR_NEGRILLA}Destino:{COLOR_RESET} {destino}")
    print(f"⏱️  {COLOR_NEGRILLA}Tiempo estimado total:{COLOR_RESET} {tiempo_total} minutos")
    print(f"🔄 {COLOR_NEGRILLA}Transbordos requeridos:{COLOR_RESET} {transbordos}")
    print(f"🚌 {COLOR_NEGRILLA}Troncales utilizadas:{COLOR_RESET} {' ➔ '.join(lineas_usadas)}")
    print("-" * 70)

    print(f"{COLOR_NEGRILLA}DETALLE DEL RECORRIDO PASO A PASO:{COLOR_RESET}\n")

    conexiones_completas = motor.obtener_conexiones_completas()

    troncal_anterior = None
    for i in range(len(ruta_estaciones) - 1):
        actual = ruta_estaciones[i]
        siguiente = ruta_estaciones[i + 1]

        tiempo_step = 0
        troncal_step = ""

        # Buscar la conexión correspondiente entre actual y siguiente
        for c in conexiones_completas:
            if c.origen.lower() == actual.lower() and c.destino.lower() == siguiente.lower():
                tiempo_step = c.tiempo_minutos
                troncal_step = c.ruta
                break

        # Verificar si hubo transbordo antes de abordar este tramo
        if troncal_anterior is not None and troncal_step.lower() != troncal_anterior.lower():
            print(
                f"   {COLOR_TRANSBORDO}🔄 [TRANSBORDO EN {actual.upper()}] "
                f"Cambio de Troncal {troncal_anterior} ➔ {troncal_step} (+5 min){COLOR_RESET}"
            )

        print(f"  [{i+1}] {COLOR_INFO}{actual}{COLOR_RESET} ➔ {COLOR_INFO}{siguiente}{COLOR_RESET}")
        print(f"      Línea: {COLOR_NEGRILLA}{troncal_step}{COLOR_RESET} | Tiempo tramo: {tiempo_step} min")

        troncal_anterior = troncal_step

    print(f"\n{COLOR_EXITO}✔ Llegada a la estación destino: {destino}{COLOR_RESET}")
    print("=" * 70)


def mostrar_todas_las_rutas(origen: str, destino: str, astar: BusquedaAStar, bc: BaseConocimiento):
    """Muestra todas las rutas alternativas posibles entre el origen y el destino."""
    print(f"\n{COLOR_TITULO}--- TODAS LAS RUTAS POSIBLES ENTRE '{origen}' Y '{destino}' ---{COLOR_RESET}")

    origen_exacto = next((e for e in bc.listar_estaciones() if e.lower() == origen.lower()), None)
    destino_exacto = next((e for e in bc.listar_estaciones() if e.lower() == destino.lower()), None)

    if not origen_exacto or not destino_exacto:
        print(f"{COLOR_ALERTA}Estación no encontrada.{COLOR_RESET}")
        return

    G = astar.grafo_nx
    rutas_encontradas = []

    for t_orig in bc.obtener_troncal(origen_exacto):
        for t_dest in bc.obtener_troncal(destino_exacto):
            src = (origen_exacto, t_orig)
            tgt = (destino_exacto, t_dest)
            if src in G and tgt in G:
                try:
                    for path in nx.all_shortest_paths(G, src, tgt, weight="weight"):
                        dist = nx.path_weight(G, path, weight="weight")
                        res = astar._procesar_resultado_camino(path, dist)
                        if res not in rutas_encontradas:
                            rutas_encontradas.append(res)
                except nx.NetworkXNoPath:
                    pass

    if not rutas_encontradas:
        print(f"No se encontraron rutas alternativas.")
        return

    for idx, (estaciones, tiempo, transbordos, lineas) in enumerate(rutas_encontradas, 1):
        print(f"\n{COLOR_NEGRILLA}Opción #{idx}:{COLOR_RESET}")
        print(f"  • Ruta: {' ➔ '.join(estaciones)}")
        print(f"  • Tiempo: {tiempo} min | Transbordos: {transbordos} | Troncales: {', '.join(lineas)}")

    print("-" * 70)


def modo_interactivo(bc: BaseConocimiento, motor: MotorInferencia, astar: BusquedaAStar):
    """Ejecuta el menú interactivo en la consola."""
    imprimir_encabezado()
    estaciones = bc.listar_estaciones()
    mostrar_estaciones(bc)

    def obtener_estacion_input(mensaje: str) -> str:
        while True:
            val = input(f"{COLOR_NEGRILLA}{mensaje}:{COLOR_RESET} ").strip()
            if val.isdigit():
                idx = int(val)
                if 1 <= idx <= len(estaciones):
                    return estaciones[idx - 1]
            # Buscar por coincidencia de nombre
            for e in estaciones:
                if e.lower() == val.lower():
                    return e
            print(f"{COLOR_ALERTA}Entrada inválida. Ingrese el número (1-{len(estaciones)}) o el nombre de la estación.{COLOR_RESET}")

    origen = obtener_estacion_input("Seleccione número o nombre de la ESTACIÓN DE ORIGEN")
    destino = obtener_estacion_input("Seleccione número o nombre de la ESTACIÓN DE DESTINO")

    print(f"\n🔎 Buscando la mejor ruta desde '{origen}' hasta '{destino}'...")
    resultado = astar.encontrar_ruta(origen, destino)

    if resultado:
        mostrar_ruta_detallada(origen, destino, resultado, bc, motor, astar)
    else:
        print(f"\n{COLOR_ALERTA}No se encontró ninguna ruta entre {origen} y {destino}.{COLOR_RESET}")


def main():
    parser = argparse.ArgumentParser(
        description="Sistema Inteligente de Rutas TransMilenio (SIRTM Bogotá)"
    )
    parser.add_argument("origen", nargs="?", type=str, help="Estación de origen")
    parser.add_argument("destino", nargs="?", type=str, help="Estación de destino")
    parser.add_argument("--explicar", action="store_true", help="Muestra las inferencias lógicas aplicadas")
    parser.add_argument("--todas", action="store_true", help="Muestra todas las rutas posibles alternativas")

    args = parser.parse_args()

    bc = BaseConocimiento()
    motor = MotorInferencia(bc)
    astar = BusquedaAStar(bc, motor)

    if args.explicar:
        mostrar_explicacion_inferencias(motor)

    if args.origen and args.destino:
        imprimir_encabezado()
        resultado = astar.encontrar_ruta(args.origen, args.destino)
        if resultado:
            mostrar_ruta_detallada(args.origen, args.destino, resultado, bc, motor, astar)
            if args.todas:
                mostrar_todas_las_rutas(args.origen, args.destino, astar, bc)
        else:
            print(f"{COLOR_ALERTA}Error: No se encontró ruta entre '{args.origen}' y '{args.destino}'. Verifique que las estaciones existan.{COLOR_RESET}")
    else:
        modo_interactivo(bc, motor, astar)


if __name__ == "__main__":
    main()

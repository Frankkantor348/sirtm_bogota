# Sistema Inteligente de Rutas TransMilenio (SIRTM Bogotá)

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![NetworkX 3.2.1](https://img.shields.io/badge/networkx-3.2.1-green.svg)](https://networkx.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Un sistema inteligente basado en conocimiento, inferencia lógica de primer orden y algoritmo de búsqueda heurística $A^*$ para determinar la ruta óptima de menor tiempo dentro de una red representativa del sistema de transporte masivo TransMilenio en Bogotá.

---

## 🎯 Objetivo Académico

Proyecto desarrollado para la asignatura **Inteligencia Artificial Avanzada**. Permite aplicar de forma práctica:
1. **Representación del Conocimiento:** Hechos en lógica formal (Prolog-style).
2. **Motor de Inferencia Deductivo:** Aplicación de reglas lógicas de bidireccionalidad, estaciones compartidas y penalización de transbordos.
3. **Búsqueda Heurística Informada ($A^*$):** Algoritmo de exploración de grafos optimizado mediante la distancia Manhattan geográfica admisible sobre las coordenadas reales del sistema.

---

## 🗺️ Alcance del Sistema Modelado

El sistema modela **10 estaciones únicas**, **3 troncales principales** y **1 ruta alimentadora**:

### Estaciones y Coordenadas Reales:
* **Troncal Caracas (Norte-Sur):**
  * `Portal Usme` (4.5280, -74.1180)
  * `Danubio` (4.5480, -74.1150)
  * `Museo Nacional` (4.6120, -74.0980)
  * `Calle 72` (4.6580, -74.0620) *(Estación compartida)*
* **Troncal Autonorte (Norte):**
  * `Calle 72` (4.6580, -74.0620) *(Estación compartida)*
  * `Héroes` (4.6750, -74.0580)
  * `Calle 100` (4.6890, -74.0520) *(Estación compartida)*
  * `Portal Norte` (4.7540, -74.0480)
* **Troncal Suba (Occidente):**
  * `Portal Suba` (4.7420, -74.0940)
  * `Niza` (4.6980, -74.0720)
  * `Calle 100` (4.6890, -74.0520) *(Estación compartida)*
* **Ruta Alimentadora:**
  * `Portal Usme` $\rightarrow$ `Marruecos` (4.5350, -74.1250)

---

## 📐 Diagrama ASCII del Sistema

```text
    [Portal Suba] (Suba)
         |  (9 min)
      [Niza]
         |  (8 min)
   +-----+-----+ [Calle 100] (Transbordo Autonorte ↔ Suba, 5 min)
   |           |
   | (8 min)   | (10 min)
   |           v
   |     [Portal Norte] (Autonorte)
   |
   | (7 min)
[Héroes]
   | (6 min)
   +-----------+ [Calle 72] (Transbordo Caracas ↔ Autonorte, 5 min)
               |
               | (12 min)
        [Museo Nacional] (Caracas)
               | (8 min)
           [Danubio]
               | (5 min)
         [Portal Usme] <====(Alimentadora, 15 min)===> [Marruecos]
```

---

## 🛠️ Requisitos Previos e Instalación

* **Python 3.9** o superior.
* Dependencia externa: `networkx==3.2.1`.

### Pasos de Instalación:

1. **Clonar o descargar el repositorio:**
   ```bash
   git clone https://github.com/Frankkantor348/sirtm_bogota.git
   cd sirtm_bogota
   ```

2. **Crear y activar entorno virtual (Recomendado):**
   ```bash
   # En Windows:
   python -m venv venv
   venv\Scripts\activate

   # En Linux/macOS:
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Instrucciones de Ejecución

### 1. Modo Interactivo (Menú en Consola)
Permite seleccionar las estaciones de origen y destino mediante un menú numerado:
```bash
python src/main.py
```

### 2. Modo por Línea de Comandos (CLI)
Pasa el origen y destino directamente como argumentos:
```bash
python src/main.py "Portal Usme" "Portal Norte"
python src/main.py "Portal Suba" "Portal Norte"
```

### 3. Modo Explicación de Inferencias (`--explicar`)
Muestra el detalle de todas las reglas lógicas que aplicó el motor de inferencia:
```bash
python src/main.py "Portal Usme" "Portal Norte" --explicar
```

### 4. Modo Mostrar Todas las Rutas (`--todas`)
Muestra rutas alternativas y comparativas entre dos estaciones:
```bash
python src/main.py "Portal Usme" "Portal Norte" --todas
```

---

## 🧪 Pruebas Unitarias

El proyecto incluye **8 pruebas unitarias** que verifican la carga de datos, la inferencia bidireccional, los transbordos, los caminos óptimos y la admisibilidad de la heurística.

Para ejecutar la suite de pruebas:
```bash
python -m unittest tests/test_rutas.py
```

### Resultados Esperados de las Pruebas:
```text
........
----------------------------------------------------------------------
Ran 8 tests in 0.036s

OK
```

---

## 🧠 Explicación Técnica

### 1. Hechos (`conocimiento/hechos.txt`)
Declaración formal de estaciones, coordenadas geográficas, tiempos de viaje entre estaciones y transbordos directos conocidos.

### 2. Reglas Lógicas (`conocimiento/reglas.txt`)
* **Regla 1 (Bidireccionalidad):** $conexion(A, B, R, T) \Rightarrow conexion(B, A, R, T)$.
* **Regla 2 y 3 (Transbordo y Penalización):** Si se cambia de troncal $R_1 \neq R_2$, se adiciona un costo de $5\text{ min}$.
* **Regla 4 (Ruta más rápida):** Minimización de la función de costo total $f(n) = g(n) + h(n)$.
* **Regla 5 (Preferencia directa):** Ante tiempos iguales, se escoge el camino con menor cantidad de transbordos.
* **Regla 6 (Estaciones Compartidas):** Permite el transbordo físico en estaciones como `Calle 72` y `Calle 100` sin cambiar de ubicación geográfica.

### 3. Algoritmo $A^*$ y Heurística Manhattan
* **Función de Evaluación:** $f(n) = g(n) + h(n)$
  * $g(n)$: Tiempo real acumulado de viaje en minutos (incluyendo penalizaciones por transbordo).
  * $h(n)$: Distancia Manhattan geográfica sobre coordenadas: $h(n) = (|\Delta\text{lat}| + |\Delta\text{lon}|) \times 80$.
* **Admisibilidad:** Se garantiza $h(n) \le h^*(n)$ para todo par de estaciones, asegurando que el algoritmo siempre encuentra la ruta óptima global sin sobreestimar el tiempo.

---

---

## 🤖 Actividad 5: Métodos Supervisados (Árboles y Reglas de Decisión)

Conforme al **Capítulo 17 de Palma Méndez (2008)** (*Aprendizaje de árboles y reglas de decisión*), el sistema incorpora modelos predictivos supervisados basados en árboles de decisión y extracción automática de reglas lógicas de producción (`IF ... THEN ...`).

### 📊 Dataset SIRTM Bogotá (`datos/dataset_viajes_transmilenio.csv`)
* **Muestra:** 2,500 observaciones calibradas con variables reales de movilidad y clima de Bogotá.
* **Variables Predictoras:** Troncal, Distancia (km), Tipo de Día (Laboral / Fin de Semana), Hora, Franja Horaria (Pico / Valle), Clima (Despejado, Lluvia Ligera, Lluvia Fuerte), Afluencia de Pasajeros, Incidente Vial, Tiempo Base.
* **Variable Objetivo de Clasificación:** `Nivel_Congestion` (`Bajo`, `Medio`, `Alto`, `Critico`).
* **Variable Objetivo de Regresión:** `Tiempo_Real_Minutos` (Tiempo efectivo observado de viaje).

### 📈 Métricas de Rendimiento Obtenidas:
* **Clasificador (DecisionTreeClassifier):**
  * Exactitud (Accuracy): **76.60%**
  * F1-Score Ponderado: **75.88%**
  * Validación Cruzada (5-Fold Stratified CV): **77.44% (± 2.56%)**
  * Total de Reglas de Decisión Extraídas: **27 reglas inductivas**
* **Regresor (DecisionTreeRegressor):**
  * Coeficiente de Determinación ($R^2$): **0.9453**
  * Error Absoluto Medio (MAE): **2.37 minutos**
  * RMSE: **3.59 minutos**

### 🚀 Comandos de Ejecución de Machine Learning:
```bash
# 1. Generar / regenerar el dataset calibrado
python src/generar_dataset.py

# 2. Entrenar modelos supervisados (Árboles y Reglas de Decisión)
python src/aprendizaje_supervisado.py
python src/main.py --ml

# 3. Entrenar modelos no supervisados (K-Means, Codo, Silueta y PCA)
python src/aprendizaje_no_supervisado.py
python src/main.py --clustering

# 4. Correr la suite completa de pruebas unitarias (17 tests)
python -m unittest discover tests
```

---

## 🔍 Actividad: Métodos No Supervisados (Técnicas de Agrupamiento)

Conforme al **Capítulo 16 de Palma Méndez (2008)** (*Técnicas de agrupamiento*), el sistema incorpora modelos no supervisados para descubrir patrones latentes de operación y vulnerabilidad:
* **Algoritmo Particional:** K-Means con inicialización $k\text{-means++}$.
* **Selección de $k$ Óptimo:** Método del Codo (Elbow Method) y Coeficiente de Silueta evaluados entre $k=2$ y $k=7$ ($k=3$ seleccionado).
* **Perfiles Descubiertos:**
  * **Cluster 1 (47.2%):** Flujo Libre en Horas Valle (Retraso medio: 3.1 min | Afluencia: 1,197 pas/hr).
  * **Cluster 2 (25.4%):** Demanda Alta / Tráfico Controlado (Retraso medio: 6.7 min | Afluencia: 2,634 pas/hr).
  * **Cluster 0 (27.4%):** Vulnerabilidad Crítica por Contingencias (Retraso medio: 13.8 min | Afluencia: 1,836 pas/hr).
* **Visualización:** Proyección 2D mediante PCA con centroides y dendrograma jerárquico aglomerativo (Ward).

---

## 📁 Estructura del Proyecto

```text
sirtm_bogota/
├── .gitignore
├── README.md
├── requirements.txt
├── conocimiento/
│   ├── hechos.txt
│   └── reglas.txt
├── datos/
│   ├── dataset_viajes_transmilenio.csv
│   ├── arbol_decision.png
│   ├── matriz_confusion.png
│   ├── metricas_modelo.json
│   ├── reglas_decision.txt
│   ├── clustering_kmeans.png
│   ├── metodo_codo_silueta.png
│   ├── dendrograma.png
│   ├── clusters_resumen.csv
│   └── metricas_no_supervisado.json
├── src/
│   ├── __init__.py
│   ├── base_conocimiento.py
│   ├── motor_inferencia.py
│   ├── busqueda_astar.py
│   ├── generar_dataset.py
│   ├── aprendizaje_supervisado.py
│   ├── aprendizaje_no_supervisado.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_rutas.py
│   ├── test_aprendizaje_supervisado.py
│   └── test_aprendizaje_no_supervisado.py
```

---

## 👥 Integrantes del Equipo

* **Estudiante 1:** Franklin Gutiérrez (Código: [Código Estudiante])
* **Estudiante 2:** Mary González (Código: [Código Estudiante])

---

## 📹 Enlaces y Entregables

* **Repositorio Git:** [https://github.com/Frankkantor348/sirtm_bogota](https://github.com/Frankkantor348/sirtm_bogota)
* **Video Demostrativo (Máx. 10 minutos):** [Inserte aquí el link de YouTube / Loom / Drive]

---

## 💻 Comandos de Ejecución y Pruebas

Para la ejecución y validación del proyecto se utilizaron diferentes comandos desde la terminal. Para ejecutar el sistema y calcular rutas óptimas entre las estaciones, se utilizaron los siguientes comandos:

```bash
python src/main.py "Portal Usme" "Portal Norte"
python src/main.py "Portal Suba" "Portal Norte"
```

Estos comandos permiten probar el funcionamiento del sistema con diferentes estaciones de origen y destino, utilizando el algoritmo **A*** para determinar la ruta óptima.

Para verificar el correcto funcionamiento del proyecto mediante pruebas unitarias, se utilizaron los siguientes comandos:

```bash
python -m unittest tests/test_rutas.py
python -m unittest discover -s tests
```

El primer comando ejecuta directamente las pruebas definidas en `test_rutas.py`, mientras que el segundo utiliza el sistema de descubrimiento automático de `unittest` para localizar y ejecutar las pruebas disponibles dentro de la carpeta `tests`.

Finalmente, para realizar una comparación entre los algoritmos **A*** y **Dijkstra**, se utilizó el siguiente comando:

```bash
python -c "from src.base_conocimiento import BaseConocimiento; from src.motor_inferencia import MotorInferencia; from src.busqueda_astar import BusquedaAStar; bc=BaseConocimiento(); m=MotorInferencia(bc); a=BusquedaAStar(bc, m); print(a.comparar_con_dijkstra('Portal Usme', 'Portal Norte'))"
```

Este comando permite comparar los resultados obtenidos por **A*** y **Dijkstra** para la ruta entre `Portal Usme` y `Portal Norte`, con el objetivo de analizar el comportamiento de ambos algoritmos en el cálculo de rutas dentro de la red modelada.

---

## 📄 Licencia

Este proyecto fue desarrollado exclusivamente con fines académicos para la materia de Inteligencia Artificial Avanzada. Bajo licencia [MIT](LICENSE).


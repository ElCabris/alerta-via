# Sistema de Predicción de Riesgo de Hurtos - Medellín

## Descripción

Este sistema utiliza datos históricos de hurtos en Medellín para predecir el riesgo de hurto en rutas específicas. Está diseñado para funcionar con datos solo positivos (ocurrencias de hurto) sin necesidad de casos negativos explícitos.

## Características Principales

- **Análisis Espacial**: Utiliza una cuadrícula de 500m x 500m para dividir Medellín en celdas
- **Clustering de Zonas**: Agrupa zonas similares usando K-Means con características espaciales y temporales
- **Scoring de Riesgo**: Calcula scores de riesgo basados en múltiples factores:
  - Frecuencia de hurtos (40% del peso)
  - Densidad de hurtos (25% del peso)
  - Concentración temporal (20% del peso)
  - Recencia de actividad (15% del peso)
- **Predicción de Rutas**: Analiza rutas completas y proporciona recomendaciones
- **API REST**: Endpoints para consultas en tiempo real

## Estructura del Proyecto

```
ml_service/
├── analisis_inicial/
│   ├── modeloML.ipynb          # Notebook principal con análisis
│   ├── dataset_limpio.csv      # Dataset limpio de hurtos
│   ├── cuadricula_medellin_500m.csv  # Cuadrícula espacial
│   ├── hurtos_con_celda.csv    # Hurtos asignados a celdas
│   ├── resumen_hurtos_por_celda.csv  # Resumen con scores de riesgo
│   └── mapa_calor_hurtos.png   # Visualización de resultados
├── predictor_riesgo.py         # Sistema de predicción
└── README.md                  # Este archivo
```

## Uso del Sistema

### 1. Análisis de Datos

Ejecuta el notebook `modeloML.ipynb` para:
- Cargar y limpiar datos de hurtos
- Crear cuadrícula espacial
- Asignar hurtos a celdas
- Calcular scores de riesgo
- Generar visualizaciones

### 2. API REST

El sistema incluye una API REST con los siguientes endpoints:

#### Consultar riesgo de una coordenada
```http
GET /riesgo?lat=6.25&lon=-75.57
```

#### Analizar riesgo de una ruta
```http
POST /ruta
Content-Type: application/json

{
    "puntos_ruta": [
        {"lat": 6.2442, "lon": -75.5812},
        {"lat": 6.2500, "lon": -75.5750},
        {"lat": 6.2550, "lon": -75.5700}
    ],
    "hora_consulta": 22,
    "dia_semana": 5
}
```

#### Obtener información de una celda
```http
GET /celda?lat=6.25&lon=-75.57
```

#### Obtener información de un cluster
```http
GET /cluster/{cluster_id}
```

#### Estadísticas generales
```http
GET /stats
```

### 3. Uso Programático

```python
from predictor_riesgo import crear_predictor

# Crear predictor
predictor = crear_predictor("resumen_hurtos_por_celda.csv")

# Analizar ruta
ruta = [(6.2442, -75.5812), (6.2500, -75.5750), (6.2550, -75.5700)]
resultado = predictor.calcular_riesgo_ruta(ruta, hora_consulta=22)

print(f"Riesgo general: {resultado['riesgo_general']}")
print(f"Score promedio: {resultado['score_promedio']}")
print(f"Recomendaciones: {resultado['recomendaciones']}")
```

## Metodología

### 1. Cuadrícula Espacial
- División de Medellín en celdas de 500m x 500m
- Asignación de hurtos a celdas basada en coordenadas
- Cálculo de métricas por celda

### 2. Clustering Espacial
- **K-Means**: Agrupa zonas con características similares
- **Características**: Ubicación, hurtos, densidad, patrones temporales
- **Optimización**: Silhouette score para determinar número óptimo de clusters
- **Análisis**: Identifica patrones geográficos de riesgo

### 3. Scoring de Riesgo
El score se calcula considerando:

- **Frecuencia (40%)**: Total de hurtos históricos en la celda
- **Densidad (25%)**: Hurtos por km²
- **Concentración Temporal (20%)**: Desviación estándar de horas de hurto
- **Recencia (15%)**: Duración de actividad delictiva

### 4. Clasificación de Riesgo
- **MUY_BAJO**: Score < 20
- **BAJO**: Score 20-39
- **MEDIO**: Score 40-59
- **ALTO**: Score 60-79
- **MUY_ALTO**: Score ≥ 80

## Datos de Entrada

El sistema requiere un dataset con las siguientes columnas:
- `latitud`, `longitud`: Coordenadas del hurto
- `hour`, `dayofweek`: Información temporal
- `edad`, `modalidad`, `lugar`: Características del hurto
- `year`, `month`, `day`: Fecha del hurto

## Limitaciones

1. **Sesgo de Reporte**: Solo considera hurtos reportados
2. **Ausencia de Casos Negativos**: No hay datos explícitos de "no-hurto"
3. **Dependencia Histórica**: Basado en patrones pasados
4. **Resolución Espacial**: Limitado a celdas de 500m

## Mejoras Futuras

1. **Integración de Datos Externos**: Población, tráfico, iluminación
2. **Modelos de Aprendizaje Automático**: Clustering, redes neuronales
3. **Predicción Temporal**: Series de tiempo para tendencias
4. **Validación Cruzada**: Métricas de rendimiento del modelo

## Dependencias

```python
pandas>=1.3.0
numpy>=1.21.0
scikit-learn>=1.0.0
matplotlib>=3.5.0
seaborn>=0.11.0
fastapi>=0.68.0
uvicorn>=0.15.0
```

## Instalación

```bash
pip install pandas numpy scikit-learn matplotlib seaborn fastapi uvicorn
```

## Ejecución

```bash
# Ejecutar API
cd backend
python app.py

# El servidor estará disponible en http://localhost:8000
```

## Contacto

Sistema desarrollado para Alerta Vial - Medellín

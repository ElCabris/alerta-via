# Modelo de Densidad/Hotspots - Guía de Uso

## Descripción

Este es el nuevo modelo de predicción de riesgo de hurto basado en **Modelado por Densidad/Hotspots** usando Kernel Density Estimation (KDE). Este modelo reemplaza el enfoque anterior de XGBoost/LightGBM y ofrece ventajas significativas:

- ✅ No requiere pseudo-ausencias ni balanceo de clases
- ✅ Implementación rápida (días, no semanas)
- ✅ Consulta O(1) por tile - muy eficiente
- ✅ Hotspots claros para visualización
- ✅ Fácil de explicar a stakeholders
- ✅ Más estable ante cambios en los datos

## Instalación de Dependencias

Asegúrate de tener todas las dependencias instaladas:

```bash
cd backend
pip install -r requirements.txt
```

El nuevo modelo requiere `scipy` que ya está incluido en `requirements.txt`.

## Entrenamiento del Modelo

### Paso 1: Preparar los Datos

Asegúrate de tener el archivo `dataset_postprocess.csv` en el directorio `modelo_ML/` con las siguientes columnas:
- `latitud`, `longitud`: Coordenadas geográficas
- `hour`: Hora del día (0-23)
- `dayofweek`: Día de la semana (0=Lunes, 6=Domingo)
- `is_weekend`: (opcional, se calcula automáticamente si no existe)

### Paso 2: Entrenar el Modelo

```bash
cd modelo_ML
python train_density_model.py
```

Este script:
1. Carga los datos históricos
2. Crea una grilla espacial (~500m de resolución)
3. Segmenta los datos por periodo temporal (weekday/weekend + morning/afternoon/evening/night)
4. Calcula heatmaps usando KDE para cada segmento
5. Guarda el modelo en `../backend/models/density_hotspot_model.pkl`
6. Guarda estadísticas en `../backend/models/density_model_stats.json`

### Paso 3: Verificar el Modelo

El script mostrará información sobre:
- Límites geográficos
- Tamaño de la grilla
- Número de registros por periodo
- Prueba de predicción

## Uso en Producción

### Iniciar el Backend

El backend automáticamente detecta y carga el modelo de densidad si está disponible:

```bash
cd backend
python run_server.py
```

O con uvicorn directamente:

```bash
cd backend
uvicorn app.main:app --reload
```

### Verificar que el Modelo Esté Cargado

```bash
curl http://localhost:8000/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "density_model_loaded": true,
  "legacy_model_loaded": false,
  "scaler_loaded": false
}
```

### Obtener Información del Modelo

```bash
curl http://localhost:8000/model/info
```

Esto mostrará información sobre el modelo cargado, incluyendo:
- Tipo de modelo
- Resolución de grilla
- Número de heatmaps
- Estadísticas

## API Endpoints

La API mantiene la misma interfaz que antes, por lo que el frontend no requiere cambios:

### Predicción para una Ruta

```bash
POST /predict/route
Content-Type: application/json

{
  "puntos": [
    {"latitud": 6.2442, "longitud": -75.5812},
    {"latitud": 6.2450, "longitud": -75.5820}
  ],
  "fecha_hora": "2024-01-15T14:30:00"
}
```

### Predicción para un Punto

```bash
POST /predict/point
Content-Type: application/json

{
  "latitud": 6.2442,
  "longitud": -75.5812,
  "fecha_hora": "2024-01-15T14:30:00"
}
```

## Segmentación Temporal

El modelo segmenta automáticamente por:

- **Día de semana**: Weekday (Lunes-Viernes) vs Weekend (Sábado-Domingo)
- **Periodo del día**:
  - Morning: 6:00 - 12:00
  - Afternoon: 12:00 - 18:00
  - Evening: 18:00 - 24:00
  - Night: 0:00 - 6:00

Esto resulta en 8 heatmaps temporales + 1 global.

## Compatibilidad

El backend mantiene compatibilidad con el modelo anterior (legacy):
- Si el modelo de densidad está disponible, lo usa
- Si no, intenta cargar el modelo legacy (XGBoost/LightGBM)
- Si ninguno está disponible, muestra un error

## Estructura de Archivos

```
modelo_ML/
├── train_density_model.py          # Script de entrenamiento
├── dataset_postprocess.csv         # Datos de entrenamiento
└── ANALISIS_MODELO_DENSIDAD.md     # Documentación técnica

backend/
├── app/
│   ├── main.py                     # API (actualizada)
│   └── density_model.py            # Clase del modelo
└── models/
    ├── density_hotspot_model.pkl   # Modelo serializado
    └── density_model_stats.json    # Estadísticas
```

## Troubleshooting

### Error: "Modelo no disponible"

1. Verifica que el archivo `density_hotspot_model.pkl` existe en `backend/models/`
2. Ejecuta `train_density_model.py` para generar el modelo
3. Verifica que el backend tenga permisos para leer el archivo

### Error: "ImportError: cannot import name DensityHotspotModel"

1. Verifica que `backend/app/density_model.py` existe
2. Verifica que `scipy` está instalado: `pip install scipy`

### El modelo no usa la segmentación temporal

Verifica que estás pasando `fecha_hora` en el request. Si no se proporciona, se usa la hora actual.

## Próximos Pasos

1. **Segmentación Espacial**: Agregar heatmaps por comuna/barrio
2. **Optimización**: Usar grillas hexagonales (H3) en lugar de cuadrículas
3. **Visualización**: Generar mapas de calor automáticamente
4. **Actualización Incremental**: Actualizar heatmaps sin reentrenar todo

## Referencias

- Ver `ANALISIS_MODELO_DENSIDAD.md` para documentación técnica completa
- Ver `ANALISIS_MODELO.md` para comparación con el modelo anterior


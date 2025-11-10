# Análisis del Modelo de Densidad/Hotspots

## Resumen Ejecutivo

Este documento describe el nuevo modelo de predicción de riesgo de hurto basado en **Modelado por Densidad/Hotspots** usando Kernel Density Estimation (KDE). Este modelo reemplaza el enfoque anterior de XGBoost/LightGBM con pseudo-ausencias.

## Arquitectura del Modelo

### Enfoque: Modelado por Densidad/Hotspots

El modelo utiliza **Kernel Density Estimation (KDE)** para calcular la densidad de eventos históricos de hurto en el espacio geográfico, segmentado por variables temporales y espaciales.

### Ventajas del Nuevo Enfoque

1. **Implementación Rápida**
   - No requiere pseudo-ausencias ni balanceo de clases
   - KDE es directo y eficiente
   - Resultados en días, no semanas

2. **Escalabilidad y Producción**
   - Precomputar tiles/heatmaps por periodo (hora/día/semana) es eficiente
   - Consulta O(1) por tile
   - Bajo costo computacional en scoring de rutas

3. **Interpretabilidad**
   - Hotspots claros para visualización
   - Fácil de explicar a stakeholders
   - Mapas de calor intuitivos

4. **Aprovecha los Datos**
   - Con ~284K presencias, la densidad es robusta
   - Variables temporales (hora, día, fin de semana) permiten segmentar por periodo
   - Variables espaciales (barrio, comuna) permiten agregación geográfica

5. **Menos Riesgo Técnico**
   - No depende de la calidad de las pseudo-ausencias
   - Menos hiperparámetros que ajustar
   - Más estable ante cambios en los datos

## Estructura del Modelo

### Componentes Principales

1. **Grilla Espacial**
   - Resolución: 0.0045 grados (~500m)
   - Cubre todo el área de Medellín
   - Puntos precomputados para consulta rápida

2. **Heatmaps por Periodo**
   - Segmentación temporal:
     - **Día de semana**: Weekday vs Weekend
     - **Periodo del día**: Morning (6-12h), Afternoon (12-18h), Evening (18-24h), Night (0-6h)
   - Total: 8 heatmaps temporales + 1 global

3. **Kernel Density Estimation**
   - Método: Gaussian KDE
   - Ancho de banda: Método de Scott (automático)
   - Fallback: Densidad basada en distancia inversa si KDE falla

### Segmentación Temporal

El modelo segmenta los datos en los siguientes períodos:

- **Weekday Morning** (Lunes-Viernes, 6-12h)
- **Weekday Afternoon** (Lunes-Viernes, 12-18h)
- **Weekday Evening** (Lunes-Viernes, 18-24h)
- **Weekday Night** (Lunes-Viernes, 0-6h)
- **Weekend Morning** (Sábado-Domingo, 6-12h)
- **Weekend Afternoon** (Sábado-Domingo, 12-18h)
- **Weekend Evening** (Sábado-Domingo, 18-24h)
- **Weekend Night** (Sábado-Domingo, 0-6h)
- **Global** (Todos los datos)

### Segmentación Espacial (Futuro)

El modelo está preparado para agregar segmentación espacial:
- Por comuna
- Por barrio

Esto permite heatmaps más específicos para áreas geográficas particulares.

## Flujo de Predicción

### Entrenamiento

1. **Cargar datos históricos** de hurtos
2. **Crear grilla espacial** con resolución fija
3. **Segmentar datos** por periodo temporal
4. **Calcular KDE** para cada segmento
5. **Precomputar heatmaps** en la grilla
6. **Guardar modelo** con todos los heatmaps

### Predicción

1. **Recibir coordenadas** (lat, lon) y parámetros temporales (hora, día)
2. **Determinar periodo** (weekday/weekend + morning/afternoon/evening/night)
3. **Encontrar punto de grilla más cercano** (O(1) con búsqueda espacial)
4. **Consultar densidad** del heatmap correspondiente
5. **Normalizar** a escala 0-1
6. **Retornar probabilidad** de riesgo

## Archivos del Modelo

### Entrenamiento
- **`train_density_model.py`**: Script principal de entrenamiento
- **`DensityHotspotModel`**: Clase que implementa el modelo

### Producción
- **`backend/app/density_model.py`**: Wrapper para cargar y usar el modelo
- **`backend/app/main.py`**: API actualizada para usar el nuevo modelo
- **`backend/models/density_hotspot_model.pkl`**: Modelo serializado
- **`backend/models/density_model_stats.json`**: Estadísticas del modelo

## Uso del Modelo

### Entrenar el Modelo

```bash
cd modelo_ML
python train_density_model.py
```

Esto generará:
- `../backend/models/density_hotspot_model.pkl`
- `../backend/models/density_model_stats.json`

### Usar en Producción

El backend automáticamente carga el modelo de densidad si está disponible. La API mantiene la misma interfaz, por lo que el frontend no requiere cambios.

### Endpoints

Los endpoints siguen siendo los mismos:
- `POST /predict/route`: Predice para una ruta completa
- `POST /predict/point`: Predice para un punto único
- `GET /model/info`: Información sobre el modelo cargado
- `GET /health`: Estado del sistema

## Comparación con Modelo Anterior

| Aspecto | Modelo Anterior (XGBoost/LightGBM) | Modelo Nuevo (Density/Hotspots) |
|---------|-----------------------------------|--------------------------------|
| **Entrenamiento** | Requiere pseudo-ausencias | Solo usa datos reales |
| **Balanceo** | Necesario | No necesario |
| **Features** | 47 features complejas | Solo coordenadas + tiempo |
| **Hiperparámetros** | Muchos (depth, learning_rate, etc.) | Pocos (bandwidth, grid_resolution) |
| **Interpretabilidad** | Media (feature importance) | Alta (mapas de calor) |
| **Velocidad de predicción** | Media (feature engineering) | Alta (consulta directa) |
| **Escalabilidad** | Media | Alta (precomputación) |
| **Estabilidad** | Depende de pseudo-ausencias | Más estable |

## Métricas y Evaluación

El modelo de densidad no requiere métricas tradicionales de clasificación (AUC, precision, recall) ya que no es un modelo de clasificación binaria. En su lugar, se evalúa:

1. **Cobertura geográfica**: ¿El modelo cubre todas las áreas relevantes?
2. **Segmentación temporal**: ¿Los heatmaps reflejan patrones temporales reales?
3. **Distribución de densidades**: ¿La distribución es razonable?
4. **Validación cualitativa**: ¿Los hotspots coinciden con conocimiento de dominio?

## Mejoras Futuras

1. **Segmentación Espacial**
   - Agregar heatmaps por comuna
   - Agregar heatmaps por barrio

2. **Optimización de Grilla**
   - Usar grillas hexagonales (H3) en lugar de cuadrículas
   - Ajustar resolución dinámicamente por densidad

3. **Temporalidad Avanzada**
   - Segmentación por mes/estación
   - Patrones estacionales

4. **Visualización**
   - Generar mapas de calor automáticamente
   - Dashboard de hotspots

5. **Actualización Incremental**
   - Actualizar heatmaps sin reentrenar todo
   - Ventanas deslizantes temporales

## Conclusión

El modelo de densidad/hotspots ofrece una alternativa más simple, interpretable y escalable al modelo anterior. Es especialmente adecuado para:

- Visualización de hotspots
- Scoring rápido de rutas
- Explicabilidad a stakeholders
- Implementación rápida
- Menor complejidad técnica

El modelo está listo para producción y mantiene compatibilidad con la API existente.


# Guía Paso a Paso: Sistema de Predicción de Hurtos en Medellín

## 📋 Índice
1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Paso 1: Preparación del Entorno](#paso-1-preparación-del-entorno)
4. [Paso 2: Entrenamiento del Modelo de Densidad](#paso-2-entrenamiento-del-modelo-de-densidad)
5. [Paso 3: Configuración del Backend API](#paso-3-configuración-del-backend-api)
6. [Paso 4: Endpoints de la API](#paso-4-endpoints-de-la-api)
7. [Paso 5: Integración con Frontend](#paso-5-integración-con-frontend)
8. [Paso 6: Pruebas y Validación](#paso-6-pruebas-y-validación)

---

## 🎯 Descripción del Proyecto

Este proyecto implementa un sistema de Machine Learning para predecir la probabilidad de hurto en diferentes zonas de Medellín basándose en:
- Ubicación geográfica (latitud, longitud)
- Características demográficas (edad, sexo, estado civil)
- Medio de transporte
- Variables temporales (hora, día, mes, año)
- Contexto del lugar (barrio, comuna)

**Enfoque utilizado**: Modelado por Densidad/Hotspots usando Kernel Density Estimation (KDE). Este modelo no requiere pseudo-ausencias y es más eficiente y estable.

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐
│   Frontend      │  (Angular - Interfaz de usuario)
│   (Angular)     │
└────────┬────────┘
         │ HTTP REST
         │
┌────────▼────────┐
│   Backend API   │  (FastAPI - Servidor REST)
│   (FastAPI)     │
└────────┬────────┘
         │
┌────────▼────────┐
│  Modelo ML      │  (Density/Hotspots - KDE)
│  (joblib)       │
└─────────────────┘
```

---

## 📦 Paso 1: Preparación del Entorno

### 1.1 Instalar Dependencias del Backend

```bash
cd backend
pip install -r requirements.txt
```

### 1.2 Verificar Estructura de Archivos

Asegúrate de tener la siguiente estructura:

```
ALERTA VIA MACHINE LEARNING/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── models/          # Se creará automáticamente
│   │   ├── density_hotspot_model.pkl
│   │   └── density_model_stats.json
│   └── requirements.txt
├── modelo_ML/
│   ├── dataset_postprocess.csv
│   ├── train_density_model.py
│   └── README_DENSIDAD.md
└── frontend/
    └── (tu aplicación Angular existente)
```

---

## 🤖 Paso 2: Entrenamiento del Modelo de Densidad

### 2.1 Entrenar el Modelo

Ejecuta el script de entrenamiento:

```bash
cd modelo_ML
python train_density_model.py
```

Este script:
1. ✅ Carga el dataset de hurtos
2. ✅ Crea una grilla espacial (~500m de resolución)
3. ✅ Segmenta los datos por periodo temporal (weekday/weekend + morning/afternoon/evening/night)
4. ✅ Calcula heatmaps usando KDE para cada segmento
5. ✅ Guarda el modelo en `backend/models/density_hotspot_model.pkl`
6. ✅ Guarda estadísticas en `backend/models/density_model_stats.json`

### 2.2 Salidas del Entrenamiento

Después del entrenamiento, tendrás:

- `backend/models/density_hotspot_model.pkl` - Modelo de densidad entrenado
- `backend/models/density_model_stats.json` - Estadísticas del modelo

### 2.3 Ventajas del Modelo de Densidad

- ✅ No requiere pseudo-ausencias
- ✅ Consulta O(1) por tile - muy eficiente
- ✅ Hotspots claros para visualización
- ✅ Más estable ante cambios en los datos
- ✅ Fácil de explicar a stakeholders

### 2.4 Segmentación Temporal

El modelo segmenta automáticamente por:
- **Día de semana**: Weekday (Lunes-Viernes) vs Weekend (Sábado-Domingo)
- **Periodo del día**:
  - Morning: 6:00 - 12:00
  - Afternoon: 12:00 - 18:00
  - Evening: 18:00 - 24:00
  - Night: 0:00 - 6:00

Esto resulta en 8 heatmaps temporales + 1 global.

---

## 🚀 Paso 3: Configuración del Backend API

### 3.1 Iniciar el Servidor

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

El servidor estará disponible en: `http://localhost:8000`

### 3.2 Documentación Interactiva

Una vez iniciado, accede a:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🔌 Paso 4: Endpoints de la API

### 4.1 Endpoints Disponibles

#### **GET /** - Health Check Básico
```bash
curl http://localhost:8000/
```

**Respuesta:**
```json
{
  "message": "API de Predicción de Hurtos Medellín",
  "version": "1.0.0",
  "status": "operativo"
}
```

#### **GET /health** - Estado del Sistema
```bash
curl http://localhost:8000/health
```

**Respuesta:**
```json
{
  "status": "healthy",
  "density_model_loaded": true
}
```

#### **POST /predict/route** - Predicción para Ruta Completa ⭐

**Endpoint principal** para predecir probabilidades en una ruta.

**Request Body:**
```json
{
  "puntos": [
    {"latitud": 6.2442, "longitud": -75.5812},
    {"latitud": 6.2500, "longitud": -75.5800},
    {"latitud": 6.2550, "longitud": -75.5750}
  ],
  "edad": 30,
  "sexo": "Hombre",
  "estado_civil": "Soltero(a)",
  "medio_transporte": "Caminata",
  "fecha_hora": "2024-01-15T14:30:00"
}
```

**Respuesta:**
```json
{
  "puntos": [
    {
      "latitud": 6.2442,
      "longitud": -75.5812,
      "probabilidad": 0.65,
      "riesgo": "medio"
    },
    {
      "latitud": 6.2500,
      "longitud": -75.5800,
      "probabilidad": 0.82,
      "riesgo": "alto"
    },
    {
      "latitud": 6.2550,
      "longitud": -75.5750,
      "probabilidad": 0.35,
      "riesgo": "bajo"
    }
  ],
  "probabilidad_promedio": 0.6067,
  "riesgo_alto_count": 1,
  "riesgo_medio_count": 1,
  "riesgo_bajo_count": 1
}
```

**Niveles de Riesgo:**
- **Alto**: probabilidad > 0.7
- **Medio**: probabilidad entre 0.4 y 0.7
- **Bajo**: probabilidad < 0.4

#### **POST /predict/point** - Predicción para un Solo Punto

**Request Body:**
```json
{
  "latitud": 6.2442,
  "longitud": -75.5812,
  "edad": 30,
  "sexo": "Hombre",
  "estado_civil": "Soltero(a)",
  "medio_transporte": "Caminata",
  "fecha_hora": "2024-01-15T14:30:00"
}
```

**Respuesta:**
```json
{
  "latitud": 6.2442,
  "longitud": -75.5812,
  "probabilidad": 0.65,
  "riesgo": "medio"
}
```

#### **GET /model/info** - Información del Modelo

```bash
curl http://localhost:8000/model/info
```

**Respuesta:**
```json
{
  "model_type": "DensityHotspotModel",
  "model_version": "2.0",
  "grid_resolution": 500,
  "heatmaps_count": 9,
  "grid_size": 1000,
  "model_loaded": true
}
```

### 4.2 Ejemplos de Uso con cURL

#### Ejemplo 1: Predicción de Ruta
```bash
curl -X POST "http://localhost:8000/predict/route" \
  -H "Content-Type: application/json" \
  -d '{
    "puntos": [
      {"latitud": 6.2442, "longitud": -75.5812},
      {"latitud": 6.2500, "longitud": -75.5800}
    ],
    "edad": 25,
    "sexo": "Mujer",
    "estado_civil": "Soltero(a)",
    "medio_transporte": "Metro"
  }'
```

#### Ejemplo 2: Predicción de Punto Único
```bash
curl -X POST "http://localhost:8000/predict/point" \
  -H "Content-Type: application/json" \
  -d '{
    "latitud": 6.2442,
    "longitud": -75.5812,
    "edad": 30,
    "sexo": "Hombre"
  }'
```

### 4.3 Parámetros Opcionales

Los parámetros demográficos (`edad`, `sexo`, `estado_civil`, `medio_transporte`) son opcionales pero se mantienen en la API para compatibilidad. El modelo de densidad solo usa coordenadas y variables temporales.

- `fecha_hora`: Si no se proporciona, usa la hora actual

---

## 🎨 Paso 5: Integración con Frontend

### 5.1 Servicio Angular para Consumir API

Crea un servicio en Angular para comunicarte con la API:

```typescript
// frontend/src/app/services/prediction.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class PredictionService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  predictRoute(route: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/predict/route`, route);
  }

  predictPoint(point: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/predict/point`, point);
  }
}
```

### 5.2 Componente para Visualizar Rutas

Crea un componente que:
1. Permita al usuario dibujar una ruta en un mapa (usando Leaflet/Google Maps)
2. Envíe los puntos de la ruta al endpoint `/predict/route`
3. Visualice las zonas de riesgo con colores:
   - 🔴 Rojo: Riesgo alto
   - 🟡 Amarillo: Riesgo medio
   - 🟢 Verde: Riesgo bajo

### 5.3 Ejemplo de Componente

```typescript
// frontend/src/app/pages/route-prediction/route-prediction.component.ts
import { Component } from '@angular/core';
import { PredictionService } from '../../services/prediction.service';

@Component({
  selector: 'app-route-prediction',
  templateUrl: './route-prediction.component.html'
})
export class RoutePredictionComponent {
  routePoints: any[] = [];
  predictions: any = null;

  constructor(private predictionService: PredictionService) {}

  async predictRoute() {
    const request = {
      puntos: this.routePoints,
      edad: 30,
      sexo: 'Hombre',
      estado_civil: 'Soltero(a)',
      medio_transporte: 'Caminata'
    };

    this.predictionService.predictRoute(request).subscribe(
      (response) => {
        this.predictions = response;
        this.visualizeOnMap(response.puntos);
      },
      (error) => {
        console.error('Error:', error);
      }
    );
  }

  visualizeOnMap(puntos: any[]) {
    // Lógica para visualizar en mapa
    puntos.forEach(punto => {
      const color = punto.riesgo === 'alto' ? 'red' : 
                   punto.riesgo === 'medio' ? 'yellow' : 'green';
      // Agregar marcador al mapa con el color correspondiente
    });
  }
}
```

---

## ✅ Paso 6: Pruebas y Validación

### 6.1 Pruebas del Modelo

1. **Verificar carga del modelo**: El modelo debe cargarse correctamente al iniciar el backend
2. **Revisar estadísticas**: Consulta `/model/info` para verificar la configuración del modelo
3. **Validar predicciones**: Las probabilidades deben estar en el rango [0, 1]

### 6.2 Pruebas de la API

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Predicción simple
curl -X POST "http://localhost:8000/predict/point" \
  -H "Content-Type: application/json" \
  -d '{"latitud": 6.2442, "longitud": -75.5812}'

# 3. Predicción de ruta
curl -X POST "http://localhost:8000/predict/route" \
  -H "Content-Type: application/json" \
  -d @test_route.json
```

### 6.3 Validación de Integración

1. ✅ Frontend puede conectarse al backend
2. ✅ Las rutas se visualizan correctamente en el mapa
3. ✅ Los colores de riesgo se muestran correctamente
4. ✅ Los tiempos de respuesta son aceptables (< 2 segundos)

---

## 📊 Flujo Completo de Uso

1. **Usuario dibuja ruta** en el frontend (mapa interactivo)
2. **Frontend envía puntos** al endpoint `/predict/route`
3. **Backend procesa cada punto**:
   - Extrae coordenadas y variables temporales
   - Consulta el heatmap correspondiente según el periodo temporal
   - Predice densidad/probabilidad usando interpolación en la grilla
4. **Backend retorna predicciones** para cada punto
5. **Frontend visualiza** la ruta con colores según riesgo:
   - 🔴 Rojo: Riesgo alto (> 0.7)
   - 🟡 Amarillo: Riesgo medio (0.4 - 0.7)
   - 🟢 Verde: Riesgo bajo (< 0.4)

---

## 🔧 Troubleshooting

### Problema: Modelo no encontrado
**Solución**: Ejecuta `train_density_model.py` primero para generar el modelo.

### Problema: Error de CORS
**Solución**: Verifica que el middleware CORS esté configurado en `main.py`.

### Problema: Predicciones muy altas/bajas
**Solución**: 
- Ajusta los umbrales de riesgo si es necesario
- Considera reentrenar con diferentes parámetros de KDE o resolución de grilla

---

## 📈 Mejoras Futuras

1. **Geocodificación Inversa**: Obtener comuna y barrio automáticamente desde coordenadas
2. **Caché de Predicciones**: Cachear predicciones para puntos frecuentes
3. **Optimización de Rutas**: Sugerir rutas alternativas más seguras
4. **Actualización del Modelo**: Pipeline para reentrenar periódicamente
5. **Dashboard de Estadísticas**: Visualización de métricas del modelo

---

## 📝 Notas Importantes

- ⚠️ El modelo predice **densidades/probabilidades**, no certezas. Úsalo como herramienta de apoyo.
- ⚠️ El modelo se entrena con datos históricos. La situación actual puede variar.
- ⚠️ Las probabilidades representan densidad relativa de eventos históricos, no predicciones absolutas.

---

## 📞 Soporte

Para dudas o problemas, revisa:
1. Los logs del servidor (`uvicorn`)
2. La documentación de Swagger (`/docs`)
3. Los gráficos de importancia de features

---

**¡Listo!** Ahora tienes un sistema completo de predicción de hurtos en Medellín. 🎉


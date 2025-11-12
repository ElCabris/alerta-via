"""
API principal para el sistema de predicción de hurtos en Medellín
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
from datetime import datetime, timedelta
import os
import httpx
import pandas as pd
from collections import Counter

app = FastAPI(
    title="Sistema de Predicción de Hurtos Medellín",
    description="API para predecir probabilidades de hurto en rutas de Medellín",
    version="1.0.0"
)

# Configurar CORS para permitir comunicación con el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar el modelo de densidad/hotspots
DENSITY_MODEL_PATH = os.path.join(os.path.dirname(__file__), "../models/density_hotspot_model.pkl")

# Intentar cargar modelo de densidad
try:
    # Intentar import relativo primero, luego absoluto
    try:
        from .density_model import DensityHotspotModel
    except ImportError:
        from app.density_model import DensityHotspotModel
    
    density_model = DensityHotspotModel.load(DENSITY_MODEL_PATH)
    print(f"✅ Modelo de densidad/hotspots cargado exitosamente desde {DENSITY_MODEL_PATH}")
except (FileNotFoundError, ImportError) as e:
    print(f"❌ Modelo de densidad no encontrado en {DENSITY_MODEL_PATH}")
    print(f"   Error: {e}")
    print(f"   Ejecuta train_density_model.py primero para entrenar el modelo.")
    density_model = None


class Point(BaseModel):
    """Punto geográfico con coordenadas"""
    latitud: float
    longitud: float


class RouteRequest(BaseModel):
    """Solicitud de predicción para una ruta"""
    puntos: List[Point]  # Lista de puntos de la ruta
    fecha_hora: Optional[str] = None  # ISO format: "2024-01-15T14:30:00"
    # Si no se proporciona fecha_hora, se usa la hora actual


class PredictionResponse(BaseModel):
    """Respuesta con predicciones de probabilidad de hurto"""
    puntos: List[dict]  # Lista de puntos con sus probabilidades
    probabilidad_promedio: float
    riesgo_alto_count: int  # Número de puntos con riesgo alto (>0.7)
    riesgo_medio_count: int  # Número de puntos con riesgo medio (0.4-0.7)
    riesgo_bajo_count: int  # Número de puntos con riesgo bajo (<0.4)


class SinglePointPrediction(BaseModel):
    """Predicción para un solo punto"""
    latitud: float
    longitud: float
    fecha_hora: Optional[str] = None




@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "API de Predicción de Hurtos Medellín",
        "version": "2.0.0",
        "model_type": "Density/Hotspots (KDE)" if density_model is not None else "No model loaded",
        "status": "operativo" if density_model is not None else "modelo no cargado"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if density_model is not None else "unhealthy",
        "density_model_loaded": density_model is not None
    }


@app.post("/predict/route", response_model=PredictionResponse)
async def predict_route(request: RouteRequest):
    """
    Predice la probabilidad de hurto para una ruta completa
    
    Args:
        request: Objeto RouteRequest con puntos de la ruta y fecha/hora opcional
    
    Returns:
        PredictionResponse con probabilidades para cada punto
    """
    if density_model is None:
        raise HTTPException(
            status_code=503, 
            detail="Modelo no disponible. Ejecuta train_density_model.py primero."
        )
    
    if len(request.puntos) == 0:
        raise HTTPException(status_code=400, detail="La ruta debe contener al menos un punto")
    
    # Parsear fecha y hora
    if request.fecha_hora:
        dt = datetime.fromisoformat(request.fecha_hora.replace('Z', '+00:00'))
    else:
        dt = datetime.now()
    
    hour = dt.hour
    dayofweek = dt.weekday()
    is_weekend = 1 if dt.weekday() >= 5 else 0
    
    predictions = []
    probabilidades = []
    
    for punto in request.puntos:
        probabilidad = density_model.predict_density(
            punto.latitud,
            punto.longitud,
            hour=hour,
            dayofweek=dayofweek,
            is_weekend=is_weekend
        )
        
        predictions.append({
            "latitud": punto.latitud,
            "longitud": punto.longitud,
            "probabilidad": float(probabilidad),
            "riesgo": "alto" if probabilidad > 0.7 else "medio" if probabilidad > 0.4 else "bajo"
        })
        
        probabilidades.append(probabilidad)
    
    # Calcular estadísticas
    prob_promedio = float(np.mean(probabilidades))
    riesgo_alto = sum(1 for p in probabilidades if p > 0.7)
    riesgo_medio = sum(1 for p in probabilidades if 0.4 <= p <= 0.7)
    riesgo_bajo = sum(1 for p in probabilidades if p < 0.4)
    
    return PredictionResponse(
        puntos=predictions,
        probabilidad_promedio=prob_promedio,
        riesgo_alto_count=riesgo_alto,
        riesgo_medio_count=riesgo_medio,
        riesgo_bajo_count=riesgo_bajo
    )


@app.post("/predict/point")
async def predict_single_point(request: SinglePointPrediction):
    """
    Predice la probabilidad de hurto para un solo punto
    
    Args:
        request: Objeto SinglePointPrediction con coordenadas y características
    
    Returns:
        Diccionario con probabilidad y nivel de riesgo
    """
    if density_model is None:
        raise HTTPException(
            status_code=503, 
            detail="Modelo no disponible. Ejecuta train_density_model.py primero."
        )
    
    # Parsear fecha y hora
    if request.fecha_hora:
        dt = datetime.fromisoformat(request.fecha_hora.replace('Z', '+00:00'))
    else:
        dt = datetime.now()
    
    hour = dt.hour
    dayofweek = dt.weekday()
    is_weekend = 1 if dt.weekday() >= 5 else 0
    
    probabilidad = density_model.predict_density(
        request.latitud,
        request.longitud,
        hour=hour,
        dayofweek=dayofweek,
        is_weekend=is_weekend
    )
    
    riesgo = "alto" if probabilidad > 0.7 else "medio" if probabilidad > 0.4 else "bajo"
    
    return {
        "latitud": request.latitud,
        "longitud": request.longitud,
        "probabilidad": float(probabilidad),
        "riesgo": riesgo
    }


@app.get("/model/info")
async def model_info():
    """Información sobre el modelo cargado"""
    if density_model is None:
        raise HTTPException(status_code=503, detail="Modelo no disponible")
    
    return {
        "model_type": "DensityHotspotModel",
        "model_version": "2.0",
        "grid_resolution": density_model.grid_resolution,
        "heatmaps_count": len(density_model.heatmaps),
        "grid_size": len(density_model.grid_points),
        "stats": density_model.stats,
        "model_loaded": True
    }


class RouteRequestOSRM(BaseModel):
    """Solicitud para obtener ruta de OSRM"""
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    profile: Optional[str] = "driving"  # 'driving', 'walking', 'cycling'


class GeocodeRequest(BaseModel):
    """Solicitud para geocodificar una dirección"""
    address: str  # Dirección a geocodificar
    limit: Optional[int] = 5  # Número máximo de resultados similares a retornar


@app.post("/route/osrm")
async def get_route_osrm(request: RouteRequestOSRM):
    """
    Obtiene una ruta real usando OSRM (solo por calles)
    Proxy para evitar problemas de CORS
    """
    try:
        # Construir URL de OSRM API
        coords = f"{request.origin_lng},{request.origin_lat};{request.destination_lng},{request.destination_lat}"
        url = f"https://router.project-osrm.org/route/v1/{request.profile}/{coords}?steps=true&geometries=geojson&overview=full"
        
        # Hacer petición a OSRM
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()
        
        if data.get("code") != "Ok" or not data.get("routes") or len(data["routes"]) == 0:
            raise HTTPException(status_code=404, detail="No se pudo calcular una ruta entre los puntos seleccionados")
        
        # Extraer coordenadas de la ruta
        route = data["routes"][0]
        geometry = route.get("geometry", {})
        
        if geometry.get("type") == "LineString" and geometry.get("coordinates"):
            # Formato GeoJSON: [longitud, latitud]
            coordinates = geometry["coordinates"]
            return {
                "coordinates": coordinates,
                "distance": route.get("distance", 0),
                "duration": route.get("duration", 0)
            }
        
        raise HTTPException(status_code=500, detail="Formato de respuesta de OSRM no reconocido")
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout al obtener ruta de OSRM")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Error al conectar con OSRM: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener ruta: {str(e)}")


@app.post("/geocode")
async def geocode_address(request: GeocodeRequest):
    """
    Geocodifica una dirección a coordenadas usando Nominatim (OpenStreetMap)
    
    Args:
        request: Objeto GeocodeRequest con la dirección a geocodificar
    
    Returns:
        Diccionario con coordenadas (latitud, longitud) y nombre formateado
    """
    try:
        # Construir URL de Nominatim API
        # Agregar "Medellín, Colombia" por defecto para mejorar resultados
        address = request.address.strip()
        if not address.lower().endswith(('medellín', 'medellin', 'colombia')):
            address = f"{address}, Medellín, Colombia"
        
        # URL encode la dirección
        from urllib.parse import quote
        encoded_address = quote(address)
        result_limit = max(1, min(request.limit or 5, 10))
        url = (
            "https://nominatim.openstreetmap.org/search"
            f"?q={encoded_address}"
            "&format=json"
            f"&limit={result_limit}"
            "&addressdetails=1"
        )
        
        # Hacer petición a Nominatim
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, 
                timeout=10.0,
                headers={"User-Agent": "AlertaVia/1.0"}  # Nominatim requiere User-Agent
            )
            response.raise_for_status()
            data = response.json()
        
        if not data or len(data) == 0:
            return {"resultados": []}
        
        resultados = []
        for result in data:
            lat = float(result.get("lat", 0))
            lon = float(result.get("lon", 0))
            display_name = result.get("display_name", request.address)
            result_type = result.get("type")
            importance = result.get("importance")
            
            resultados.append({
                "latitud": lat,
                "longitud": lon,
                "direccion": display_name,
                "direccion_original": request.address,
                "tipo": result_type,
                "importancia": importance
            })
        
        return {"resultados": resultados}
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout al geocodificar la dirección")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Error al conectar con el servicio de geocodificación: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al geocodificar dirección: {str(e)}")


# ============================================
# ENDPOINTS DE ESTADÍSTICAS
# ============================================

# Cargar datos de hurtos para estadísticas
HURTOS_CSV_PATH = os.path.join(os.path.dirname(__file__), "../../modelo_ML/hurtos_a_persona.csv")
hurtos_df = None

def load_hurtos_data():
    """Carga los datos de hurtos para estadísticas"""
    global hurtos_df
    if hurtos_df is None:
        try:
            hurtos_df = pd.read_csv(HURTOS_CSV_PATH)
            # Convertir fecha_hecho a datetime
            hurtos_df['fecha_hecho'] = pd.to_datetime(hurtos_df['fecha_hecho'], errors='coerce')
            # Normalizar fechas: remover timezone si existe para evitar problemas de comparación
            # Verificar si la columna tiene timezone usando el dtype
            if pd.api.types.is_datetime64tz_dtype(hurtos_df['fecha_hecho']):
                # Si tiene timezone, removerlo convirtiendo a UTC primero y luego a naive
                # Convertir a UTC para mantener la hora correcta
                hurtos_df['fecha_hecho'] = hurtos_df['fecha_hecho'].dt.tz_convert('UTC')
                # Remover timezone: convertir los valores a datetime naive
                # Usar .values para obtener los valores como numpy datetime64 y luego convertir a datetime naive
                hurtos_df['fecha_hecho'] = pd.to_datetime(hurtos_df['fecha_hecho'].values)
            # Extraer hora del día
            hurtos_df['hora'] = hurtos_df['fecha_hecho'].dt.hour
            # Extraer día de la semana
            hurtos_df['dia_semana'] = hurtos_df['fecha_hecho'].dt.day_name()
            # Extraer mes
            hurtos_df['mes'] = hurtos_df['fecha_hecho'].dt.month
            # Extraer año
            hurtos_df['año'] = hurtos_df['fecha_hecho'].dt.year
            print(f"✅ Datos de hurtos cargados: {len(hurtos_df)} registros")
        except Exception as e:
            print(f"⚠️ Error cargando datos de hurtos: {e}")
            hurtos_df = pd.DataFrame()  # DataFrame vacío si hay error
    return hurtos_df


@app.get("/statistics/overview")
async def get_statistics_overview():
    """Obtiene estadísticas generales del sistema"""
    df = load_hurtos_data()
    
    if df.empty:
        return {
            "total_incidentes": 0,
            "incidentes_hoy": 0,
            "incidentes_ultimo_mes": 0,
            "zonas_seguras": 0,
            "tendencia": "sin_datos"
        }
    
    # Total de incidentes
    total_incidentes = len(df)
    
    # Incidentes hoy (últimas 24 horas)
    hoy = datetime.now()
    ayer = hoy - timedelta(days=1)
    incidentes_hoy = len(df[df['fecha_hecho'] >= ayer])
    
    # Incidentes último mes
    ultimo_mes = hoy - timedelta(days=30)
    incidentes_ultimo_mes = len(df[df['fecha_hecho'] >= ultimo_mes])
    
    # Zonas seguras (barrios con menos de 10 incidentes)
    barrios_seguros = df['nombre_barrio'].value_counts()
    zonas_seguras = len(barrios_seguros[barrios_seguros < 10])
    
    # Calcular tendencia (comparar último mes con el anterior)
    mes_anterior = ultimo_mes - timedelta(days=30)
    incidentes_mes_anterior = len(df[(df['fecha_hecho'] >= mes_anterior) & (df['fecha_hecho'] < ultimo_mes)])
    
    if incidentes_mes_anterior > 0:
        cambio = ((incidentes_ultimo_mes - incidentes_mes_anterior) / incidentes_mes_anterior) * 100
        tendencia = "subiendo" if cambio > 0 else "bajando" if cambio < 0 else "estable"
    else:
        tendencia = "sin_datos"
    
    return {
        "total_incidentes": total_incidentes,
        "incidentes_hoy": incidentes_hoy,
        "incidentes_ultimo_mes": incidentes_ultimo_mes,
        "zonas_seguras": zonas_seguras,
        "tendencia": tendencia,
        "cambio_porcentual": round(cambio, 2) if incidentes_mes_anterior > 0 else 0
    }


@app.get("/statistics/by-type")
async def get_statistics_by_type():
    """Obtiene estadísticas de incidentes por tipo de bien robado"""
    df = load_hurtos_data()
    
    if df.empty:
        return {"incidents_by_type": []}
    
    # Contar por tipo de bien (columna 'bien')
    # Filtrar "Sin dato" y valores nulos
    df_bien = df[df['bien'].notna() & (df['bien'] != 'Sin dato') & (df['bien'] != 'Sin dato documentos')]
    bien_counts = df_bien['bien'].value_counts().to_dict()
    
    # Mapear bienes a nombres más amigables y agrupar categorías similares
    bien_map = {
        'Celular': 'Hurto de Celular',
        'Computador': 'Hurto de Computador',
        'Elementos computador': 'Hurto de Computador',
        'Peso': 'Hurto de Dinero',
        'Billetera': 'Hurto de Dinero',
        'Tarjeta bancaria': 'Hurto de Dinero',
        'Accesorios prendas de vestir': 'Hurto de Accesorios',
        'Cédula': 'Hurto de Documentos',
        'Bicicleta': 'Hurto de Bicicleta',
        'Motocicleta': 'Hurto de Vehículo',
        'Automóvil': 'Hurto de Vehículo',
        'Moto': 'Hurto de Vehículo'
    }
    
    # Agrupar por categoría
    incidents_by_category = {}
    for bien, count in bien_counts.items():
        # Buscar en el mapa
        categoria = bien_map.get(bien, None)
        
        if categoria:
            # Agrupar en categoría
            if categoria in incidents_by_category:
                incidents_by_category[categoria] += count
            else:
                incidents_by_category[categoria] = count
        else:
            # Si no está en el mapa, usar el nombre original
            categoria = bien
            if categoria in incidents_by_category:
                incidents_by_category[categoria] += count
            else:
                incidents_by_category[categoria] = count
    
    # Convertir a lista
    incidents_by_type = []
    for tipo, count in incidents_by_category.items():
        incidents_by_type.append({
            "type": tipo,
            "count": int(count)
        })
    
    # Ordenar por count descendente
    incidents_by_type.sort(key=lambda x: x['count'], reverse=True)
    
    # Agregar "Otros" si hay más de 6 tipos
    if len(incidents_by_type) > 6:
        otros_count = sum(item['count'] for item in incidents_by_type[6:])
        incidents_by_type = incidents_by_type[:6]
        if otros_count > 0:
            incidents_by_type.append({"type": "Otros", "count": otros_count})
    
    return {"incidents_by_type": incidents_by_type}


@app.get("/statistics/by-time")
async def get_statistics_by_time():
    """Obtiene estadísticas de incidentes por hora del día"""
    df = load_hurtos_data()
    
    if df.empty:
        return {"incidents_by_hour": []}
    
    # Contar por hora
    hora_counts = df['hora'].value_counts().sort_index().to_dict()
    
    incidents_by_hour = []
    for hora in range(24):
        count = hora_counts.get(hora, 0)
        incidents_by_hour.append({
            "hour": hora,
            "count": int(count),
            "label": f"{hora:02d}:00"
        })
    
    return {"incidents_by_hour": incidents_by_hour}


@app.get("/statistics/by-day")
async def get_statistics_by_day():
    """Obtiene estadísticas de incidentes por día de la semana"""
    df = load_hurtos_data()
    
    if df.empty:
        return {"incidents_by_day": []}
    
    # Mapear días en español
    dias_map = {
        'Monday': 'Lunes',
        'Tuesday': 'Martes',
        'Wednesday': 'Miércoles',
        'Thursday': 'Jueves',
        'Friday': 'Viernes',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }
    
    dia_counts = df['dia_semana'].value_counts().to_dict()
    
    # Ordenar por día de la semana
    orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    incidents_by_day = []
    for dia in orden_dias:
        count = dia_counts.get(dia, 0)
        incidents_by_day.append({
            "day": dias_map[dia],
            "day_en": dia,
            "count": int(count)
        })
    
    return {"incidents_by_day": incidents_by_day}


@app.get("/statistics/by-barrio")
async def get_statistics_by_barrio(limit: int = 10):
    """Obtiene estadísticas de incidentes por barrio (top N)"""
    df = load_hurtos_data()
    
    if df.empty:
        return {"incidents_by_barrio": []}
    
    # Contar por barrio
    barrio_counts = df['nombre_barrio'].value_counts().head(limit).to_dict()
    
    incidents_by_barrio = []
    for barrio, count in barrio_counts.items():
        if pd.notna(barrio):  # Filtrar NaN
            incidents_by_barrio.append({
                "barrio": str(barrio),
                "count": int(count)
            })
    
    return {"incidents_by_barrio": incidents_by_barrio}


@app.get("/statistics/timeline")
async def get_statistics_timeline(days: int = 30):
    """Obtiene estadísticas de incidentes en una línea de tiempo"""
    df = load_hurtos_data()
    
    if df.empty:
        return {"timeline": []}
    
    # Filtrar últimos N días
    fecha_limite = datetime.now() - timedelta(days=days)
    df_filtered = df[df['fecha_hecho'] >= fecha_limite].copy()
    
    if df_filtered.empty:
        return {"timeline": []}
    
    # Agrupar por fecha
    df_filtered['fecha'] = df_filtered['fecha_hecho'].dt.date
    fecha_counts = df_filtered['fecha'].value_counts().sort_index().to_dict()
    
    timeline = []
    for fecha, count in fecha_counts.items():
        timeline.append({
            "date": fecha.isoformat(),
            "count": int(count)
        })
    
    return {"timeline": timeline}


@app.get("/statistics/heatmap-data")
async def get_heatmap_data():
    """Obtiene datos para el mapa de calor"""
    df = load_hurtos_data()
    
    if df.empty:
        return {"heatmap_points": []}
    
    # Obtener puntos con coordenadas válidas
    df_valid = df[(df['latitud'].notna()) & (df['longitud'].notna())].copy()
    
    if df_valid.empty:
        return {"heatmap_points": []}
    
    # Agrupar por ubicación usando una grilla para reducir puntos
    grid_size = 0.01  # Aprox 1km
    
    # Crear grilla y agrupar puntos
    df_valid['grid_lat'] = (df_valid['latitud'] // grid_size).astype(int)
    df_valid['grid_lng'] = (df_valid['longitud'] // grid_size).astype(int)
    
    # Agrupar por celda de grilla y contar
    grid_counts = df_valid.groupby(['grid_lat', 'grid_lng']).size().reset_index(name='count')
    
    # Calcular centro de cada celda y obtener coordenadas promedio
    grid_centers = df_valid.groupby(['grid_lat', 'grid_lng']).agg({
        'latitud': 'mean',
        'longitud': 'mean'
    }).reset_index()
    
    # Combinar conteos con centros
    grid_data = grid_counts.merge(grid_centers, on=['grid_lat', 'grid_lng'])
    
    # Normalizar intensidad
    max_count = grid_data['count'].max()
    
    heatmap_points = []
    for _, row in grid_data.iterrows():
        lat = float(row['latitud'])
        lng = float(row['longitud'])
        count = int(row['count'])
        
        # Normalizar intensidad (0-1)
        intensity = min(count / max_count if max_count > 0 else 0, 1.0)
        
        # Clasificar riesgo
        if intensity > 0.7:
            risk = 'alto'
        elif intensity > 0.4:
            risk = 'medio'
        else:
            risk = 'bajo'
        
        heatmap_points.append({
            "lat": lat,
            "lng": lng,
            "intensity": float(intensity),
            "risk": risk,
            "count": count
        })
    
    # Limitar a 500 puntos para rendimiento
    if len(heatmap_points) > 500:
        # Ordenar por intensidad y tomar los más importantes
        heatmap_points.sort(key=lambda x: x['intensity'], reverse=True)
        heatmap_points = heatmap_points[:500]
    
    return {"heatmap_points": heatmap_points}


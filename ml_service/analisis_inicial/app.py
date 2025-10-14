from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import json
from typing import List, Tuple, Optional
import sys
import os

# Agregar el directorio ml_service al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ml_service'))

# Importar el predictor de riesgo
from predictor_riesgo import PredictorRiesgoRutas, crear_predictor

# ============================================
# CONFIGURACIÓN
# ============================================

app = FastAPI(title="API Riesgo de Hurtos Medellín")

# Permitir CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# CARGAR SISTEMA DE PREDICCIÓN
# ============================================

# Inicializar el predictor de riesgo
try:
    predictor = crear_predictor("ml_service/analisis_inicial/resumen_hurtos_por_celda.csv")
    print("✅ Sistema de predicción de riesgo cargado")
except Exception as e:
    print(f"⚠️ Error cargando sistema de predicción: {e}")
    predictor = None

# ============================================
# MODELOS DE DATOS
# ============================================

class Coordenada(BaseModel):
    lat: float
    lon: float

class ConsultaRuta(BaseModel):
    puntos_ruta: List[Coordenada]  # Lista de puntos que forman la ruta
    hora_consulta: Optional[int] = None  # Hora de consulta (0-23)
    dia_semana: Optional[int] = None  # Día de la semana (0-6)

class RespuestaRiesgo(BaseModel):
    riesgo_general: str
    score_promedio: float
    score_maximo: float
    total_segmentos: int
    celdas_unicas: int
    recomendaciones: List[str]
    timestamp: str

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def asignar_color_riesgo(nivel: str) -> str:
    """Asigna color según nivel de riesgo"""
    colores = {
        'MUY_BAJO': '#4CAF50',      # Verde
        'BAJO': '#8BC34A',          # Verde claro
        'MEDIO': '#FFC107',        # Amarillo
        'ALTO': '#FF9800',          # Naranja
        'MUY_ALTO': '#F44336',      # Rojo
        'SIN_DATOS': '#9E9E9E'      # Gris
    }
    return colores.get(nivel, '#9E9E9E')

# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
def home():
    return {
        "mensaje": "API de Riesgo de Hurtos - Medellín",
        "version": "2.0",
        "sistema": "Predicción basada en datos históricos de hurtos",
        "endpoints": {
            "/riesgo": "Consultar riesgo de una coordenada específica",
            "/ruta": "Analizar riesgo de una ruta completa",
            "/celda": "Obtener información detallada de una celda",
            "/stats": "Estadísticas generales del sistema"
        }
    }

@app.get("/riesgo")
def consultar_riesgo(lat: float, lon: float):
    """
    Consulta el riesgo de una coordenada específica
    
    Ejemplo: /riesgo?lat=6.25&lon=-75.57
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Sistema de predicción no disponible")
    
    try:
        info_celda = predictor.obtener_info_celda(lat, lon)
        
        if 'error' in info_celda:
            return {
                "coordenada_consultada": {"lat": lat, "lon": lon},
                "error": info_celda['error'],
                "riesgo_general": "SIN_DATOS",
                "score_riesgo": 0,
                "nivel_riesgo": "SIN_DATOS",
                "color": asignar_color_riesgo("SIN_DATOS")
            }
        
        return {
            "coordenada_consultada": {"lat": lat, "lon": lon},
            "celda_id": info_celda['celda_id'],
            "centro_celda": {
                "lat": info_celda['lat_centro'],
                "lon": info_celda['lon_centro']
            },
            "riesgo_general": info_celda['nivel_riesgo'],
            "score_riesgo": info_celda['score_riesgo'],
            "nivel_riesgo": info_celda['nivel_riesgo'],
            "color": asignar_color_riesgo(info_celda['nivel_riesgo']),
            "total_hurtos": info_celda['total_hurtos'],
            "densidad_hurtos": info_celda['densidad_hurtos'],
            "hora_promedio": info_celda['hora_promedio']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ruta")
def analizar_ruta(consulta: ConsultaRuta):
    """
    Analiza el riesgo de una ruta completa
    
    Body:
    {
        "puntos_ruta": [{"lat": 6.25, "lon": -75.57}, {"lat": 6.27, "lon": -75.56}],
        "hora_consulta": 22,  // Opcional
        "dia_semana": 5  // Opcional
    }
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Sistema de predicción no disponible")
    
    try:
        # Convertir puntos a tuplas
        puntos_ruta = [(p.lat, p.lon) for p in consulta.puntos_ruta]
        
        # Analizar ruta
        resultado = predictor.calcular_riesgo_ruta(
            puntos_ruta, 
            consulta.hora_consulta, 
            consulta.dia_semana
        )
        
        # Agregar información adicional
        resultado['color_general'] = asignar_color_riesgo(resultado['riesgo_general'])
        resultado['puntos_analizados'] = len(consulta.puntos_ruta)
        
        return resultado
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/celda")
def obtener_info_celda(lat: float, lon: float):
    """
    Obtiene información detallada de una celda específica
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Sistema de predicción no disponible")
    
    try:
        info_celda = predictor.obtener_info_celda(lat, lon)
        
        if 'error' in info_celda:
            raise HTTPException(status_code=404, detail=info_celda['error'])
        
        # Agregar color
        info_celda['color'] = asignar_color_riesgo(info_celda['nivel_riesgo'])
        
        return info_celda
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cluster/{cluster_id}")
def obtener_info_cluster(cluster_id: int):
    """
    Obtiene información detallada de un cluster específico
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Sistema de predicción no disponible")
    
    try:
        cluster_info = predictor.obtener_info_cluster(cluster_id)
        
        if 'error' in cluster_info:
            raise HTTPException(status_code=404, detail=cluster_info['error'])
        
        return cluster_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
def estadisticas_generales():
    """Estadísticas generales del sistema"""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Sistema de predicción no disponible")
    
    try:
        stats = predictor.obtener_estadisticas_generales()
        
        if 'error' in stats:
            raise HTTPException(status_code=503, detail=stats['error'])
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# EJECUTAR
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
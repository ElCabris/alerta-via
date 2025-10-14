from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
import h3

# --- Configuración del modelo ---
model = joblib.load("rf_hurto_model.joblib")
scaler = joblib.load("scaler_rf.joblib")

app = FastAPI(title="API Riesgo Hurto Medellín", version="1.0")

GRID_RESOLUTION = 9  # resolución H3 (~120 m)

# --- Modelos de entrada ---
class PointInput(BaseModel):
    lat: float
    lon: float
    hora: int
    dia_semana: int
    edad_promedio: float = 30.0
    sexo_Hombre: float = 0.5
    sexo_Mujer: float = 0.5
    medio_transporte_Caminata: float = 0.3
    arma_medio_Arma_de_fuego: float = 0.1
    is_weekend: int = 0

class RouteInput(BaseModel):
    coords: list[list[float]]
    hora: int
    dia_semana: int

# --- Endpoints ---
@app.get("/")
def home():
    return {"message": "API de Riesgo de Hurto en Medellín - Modelo RF activo"}

@app.post("/riesgo_punto/")
def riesgo_punto(punto: PointInput):
    """Devuelve la probabilidad de hurto para un punto específico."""
    cell_id = h3.latlng_to_cell(punto.lat, punto.lon, GRID_RESOLUTION)

    data = pd.DataFrame([{
        "edad": punto.edad_promedio,
        "sexo_Hombre": punto.sexo_Hombre,
        "sexo_Mujer": punto.sexo_Mujer,
        "medio_transporte_Caminata": punto.medio_transporte_Caminata,
        "arma_medio_Arma de fuego": punto.arma_medio_Arma_de_fuego,
        "hour": punto.hora,
        "dayofweek": punto.dia_semana,
        "is_weekend": punto.is_weekend,
        "cell_lat": punto.lat,
        "cell_lon": punto.lon
    }])

    X_scaled = scaler.transform(data)
    prob = float(model.predict_proba(X_scaled)[:, 1])

    return {
        "cell_id": cell_id,
        "lat": punto.lat,
        "lon": punto.lon,
        "riesgo_hurto": round(prob, 4)
    }

@app.post("/riesgo_ruta/")
def riesgo_ruta(ruta: RouteInput):
    """Recibe una lista de coordenadas y devuelve el riesgo promedio y detalle."""
    results = []

    for lat, lon in ruta.coords:
        cell_id = h3.latlng_to_cell(lat, lon, GRID_RESOLUTION)

        data = pd.DataFrame([{
            "edad": 30.0,
            "sexo_Hombre": 0.5,
            "sexo_Mujer": 0.5,
            "medio_transporte_Caminata": 0.3,
            "arma_medio_Arma de fuego": 0.1,
            "hour": ruta.hora,
            "dayofweek": ruta.dia_semana,
            "is_weekend": int(ruta.dia_semana >= 5),
            "cell_lat": lat,
            "cell_lon": lon
        }])

        X_scaled = scaler.transform(data)
        prob = float(model.predict_proba(X_scaled)[:, 1])

        results.append({
            "cell_id": cell_id,
            "lat": lat,
            "lon": lon,
            "riesgo_hurto": round(prob, 4)
        })

    riesgo_promedio = np.mean([r["riesgo_hurto"] for r in results])

    return {"riesgo_promedio": round(riesgo_promedio, 4), "detalle": results}

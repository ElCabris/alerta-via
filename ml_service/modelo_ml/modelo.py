import joblib
import pandas as pd

# Carga modelo y escalador
model = joblib.load("rf_hurto_model.joblib")
scaler = joblib.load("scaler_rf.joblib")

# Crea algunos puntos de prueba con distintas condiciones
test_points = pd.DataFrame([
    {"edad": 25, "sexo_Hombre": 1, "sexo_Mujer": 0, "medio_transporte_Caminata": 0.8,
     "arma_medio_Arma de fuego": 0.0, "hour": 10, "dayofweek": 2,
     "is_weekend": 0, "cell_lat": 6.2442, "cell_lon": -75.5812},
    
    {"edad": 40, "sexo_Hombre": 0, "sexo_Mujer": 1, "medio_transporte_Caminata": 0.1,
     "arma_medio_Arma de fuego": 0.3, "hour": 23, "dayofweek": 6,
     "is_weekend": 1, "cell_lat": 6.255, "cell_lon": -75.575},
    
    {"edad": 33, "sexo_Hombre": 1, "sexo_Mujer": 0, "medio_transporte_Caminata": 0.5,
     "arma_medio_Arma de fuego": 0.2, "hour": 14, "dayofweek": 4,
     "is_weekend": 0, "cell_lat": 6.248, "cell_lon": -75.579}
])

# Escala los datos con el mismo scaler del modelo
X_scaled = scaler.transform(test_points)

# Predicción y probabilidades
pred = model.predict(X_scaled)
proba = model.predict_proba(X_scaled)

print("Predicciones:", pred)
print("Probabilidades:", proba)

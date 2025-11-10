"""
Clase para cargar y usar el modelo de densidad/hotspots
"""
import joblib
import numpy as np
from scipy.spatial.distance import cdist
from typing import Optional


class DensityHotspotModel:
    """
    Wrapper para el modelo de densidad/hotspots cargado desde archivo
    """
    
    def __init__(self, model_data):
        """
        Inicializa el modelo desde datos cargados
        
        Args:
            model_data: Diccionario con datos del modelo cargado
        """
        self.heatmaps = {k: np.array(v) for k, v in model_data['heatmaps'].items()}
        self.grid_points = np.array(model_data['grid_points'])
        self.lat_range = np.array(model_data['lat_range'])
        self.lon_range = np.array(model_data['lon_range'])
        self.grid_bounds = model_data['grid_bounds']
        self.grid_resolution = model_data['grid_resolution']
        self.stats = model_data.get('stats', {})
    
    def _get_period_key(self, hour, dayofweek, is_weekend, comuna=None, barrio=None):
        """
        Genera clave para segmentación temporal/espacial
        """
        # Segmentación por periodo del día y día de semana
        if is_weekend:
            period = 'weekend'
        else:
            period = 'weekday'
        
        # Segmentación por hora (mañana, tarde, noche, madrugada)
        if 6 <= hour < 12:
            time_period = 'morning'
        elif 12 <= hour < 18:
            time_period = 'afternoon'
        elif 18 <= hour < 24:
            time_period = 'evening'
        else:
            time_period = 'night'
        
        key = f"{period}_{time_period}"
        
        # Agregar segmentación espacial si se proporciona
        if comuna is not None:
            key = f"{key}_comuna_{comuna}"
        if barrio is not None:
            key = f"{key}_barrio_{barrio}"
        
        return key
    
    def predict_density(self, lat, lon, hour=None, dayofweek=None, is_weekend=None, 
                       comuna=None, barrio=None):
        """
        Predice la densidad de riesgo para un punto dado
        
        Args:
            lat, lon: Coordenadas del punto
            hour, dayofweek, is_weekend: Parámetros temporales (opcionales)
            comuna, barrio: Parámetros espaciales (opcionales)
        
        Returns:
            Probabilidad/densidad de riesgo (0-1)
        """
        # Encontrar el punto de grilla más cercano
        point = np.array([[lat, lon]])
        distances = cdist(point, self.grid_points, metric='euclidean')
        closest_idx = np.argmin(distances[0])
        
        # Seleccionar heatmap apropiado
        if hour is not None and dayofweek is not None:
            if is_weekend is None:
                is_weekend = 1 if dayofweek >= 5 else 0
            
            period_key = self._get_period_key(hour, dayofweek, is_weekend, comuna, barrio)
            
            # Intentar usar heatmap específico, si no existe usar global
            if period_key in self.heatmaps:
                density = self.heatmaps[period_key][closest_idx]
            else:
                # Si no hay heatmap específico, usar el más cercano o global
                density = self.heatmaps.get('global', np.array([0]))[closest_idx]
        else:
            # Usar heatmap global si no hay información temporal
            density = self.heatmaps.get('global', np.array([0]))[closest_idx]
        
        # Normalizar a escala 0-1 (usando percentiles para mejor distribución)
        # La densidad ya está normalizada, pero podemos escalarla
        max_density = max([h.max() for h in self.heatmaps.values()])
        if max_density > 0:
            density_scaled = min(density / max_density, 1.0)
        else:
            density_scaled = 0.0
        
        return float(density_scaled)
    
    @classmethod
    def load(cls, filepath):
        """Carga el modelo desde archivo"""
        model_data = joblib.load(filepath)
        return cls(model_data)


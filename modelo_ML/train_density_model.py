"""
Script para entrenar modelo de densidad/hotspots usando KDE
No requiere pseudo-ausencias ni balanceo de clases
"""
import pandas as pd
import numpy as np
from scipy.stats import gaussian_kde
from scipy.spatial.distance import cdist
import joblib
import os
from datetime import datetime
import json

# Crear directorio para modelos
os.makedirs("../backend/models", exist_ok=True)


class DensityHotspotModel:
    """
    Modelo de densidad/hotspots basado en KDE con segmentación temporal y espacial
    """
    
    def __init__(self, grid_resolution=0.0045, kde_bandwidth='scott'):
        """
        Args:
            grid_resolution: Tamaño de celda en grados (aprox 500m)
            kde_bandwidth: Ancho de banda para KDE ('scott', 'silverman', o float)
        """
        self.grid_resolution = grid_resolution
        self.kde_bandwidth = kde_bandwidth
        self.heatmaps = {}  # Diccionario de heatmaps por periodo
        self.grid_bounds = None
        self.stats = {}
        
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
    
    def _create_grid(self, lat_min, lat_max, lon_min, lon_max):
        """
        Crea una grilla regular para precomputar densidades
        """
        lat_range = np.arange(lat_min, lat_max + self.grid_resolution, self.grid_resolution)
        lon_range = np.arange(lon_min, lon_max + self.grid_resolution, self.grid_resolution)
        
        lon_grid, lat_grid = np.meshgrid(lon_range, lat_range)
        
        grid_points = np.column_stack([lat_grid.ravel(), lon_grid.ravel()])
        
        return grid_points, lat_range, lon_range
    
    def _compute_kde_heatmap(self, data_points, grid_points):
        """
        Calcula densidad usando KDE en los puntos de la grilla
        """
        if len(data_points) < 2:
            # Si hay muy pocos puntos, retornar densidad uniforme baja
            return np.ones(len(grid_points)) * 1e-6
        
        # Calcular KDE
        try:
            kde = gaussian_kde(data_points.T, bw_method=self.kde_bandwidth)
            density = kde(grid_points.T)
        except Exception as e:
            print(f"Warning: Error en KDE, usando densidad simple: {e}")
            # Fallback: densidad basada en distancia inversa
            density = self._compute_distance_based_density(data_points, grid_points)
        
        # Normalizar para que sea una probabilidad
        density = density / (density.sum() + 1e-10)
        
        return density
    
    def _compute_distance_based_density(self, data_points, grid_points):
        """
        Método alternativo basado en distancia inversa cuando KDE falla
        """
        # Calcular distancias
        distances = cdist(grid_points, data_points, metric='euclidean')
        
        # Densidad inversa a la distancia (con suavizado)
        epsilon = 0.001  # Evitar división por cero
        density = 1.0 / (distances.min(axis=1) + epsilon)
        
        # Normalizar
        density = density / (density.sum() + 1e-10)
        
        return density
    
    def fit(self, df):
        """
        Entrena el modelo calculando heatmaps por periodo
        
        Args:
            df: DataFrame con columnas: latitud, longitud, hour, dayofweek, is_weekend,
                codigo_comuna, codigo_barrio_num (opcionales)
        """
        print("=" * 60)
        print("ENTRENANDO MODELO DE DENSIDAD/HOTSPOTS")
        print("=" * 60)
        
        # Calcular límites geográficos
        self.grid_bounds = {
            'lat_min': df['latitud'].min(),
            'lat_max': df['latitud'].max(),
            'lon_min': df['longitud'].min(),
            'lon_max': df['longitud'].max()
        }
        
        print(f"\nLímites geográficos:")
        print(f"  Latitud: [{self.grid_bounds['lat_min']:.4f}, {self.grid_bounds['lat_max']:.4f}]")
        print(f"  Longitud: [{self.grid_bounds['lon_min']:.4f}, {self.grid_bounds['lon_max']:.4f}]")
        print(f"  Total de registros: {len(df):,}")
        
        # Crear grilla
        print(f"\nCreando grilla con resolución {self.grid_resolution} grados...")
        grid_points, lat_range, lon_range = self._create_grid(
            self.grid_bounds['lat_min'],
            self.grid_bounds['lat_max'],
            self.grid_bounds['lon_min'],
            self.grid_bounds['lon_max']
        )
        
        self.grid_points = grid_points
        self.lat_range = lat_range
        self.lon_range = lon_range
        
        print(f"  Grilla creada: {len(grid_points):,} puntos")
        
        # Segmentar datos por periodo
        print("\nSegmentando datos por periodo temporal...")
        
        # Agregar columnas de periodo si no existen
        if 'is_weekend' not in df.columns:
            df['is_weekend'] = (df['dayofweek'] >= 5).astype(int)
        
        # Calcular heatmaps por periodo
        periods = []
        for period_key in ['weekday_morning', 'weekday_afternoon', 'weekday_evening', 'weekday_night',
                           'weekend_morning', 'weekend_afternoon', 'weekend_evening', 'weekend_night']:
            period, time_period = period_key.split('_')
            is_weekend = 1 if period == 'weekend' else 0
            
            if time_period == 'morning':
                hour_filter = (df['hour'] >= 6) & (df['hour'] < 12)
            elif time_period == 'afternoon':
                hour_filter = (df['hour'] >= 12) & (df['hour'] < 18)
            elif time_period == 'evening':
                hour_filter = (df['hour'] >= 18) & (df['hour'] < 24)
            else:  # night
                hour_filter = (df['hour'] < 6) | (df['hour'] >= 24)
            
            period_data = df[(df['is_weekend'] == is_weekend) & hour_filter]
            
            if len(period_data) > 0:
                print(f"  {period_key}: {len(period_data):,} registros")
                data_points = period_data[['latitud', 'longitud']].values
                
                # Calcular heatmap
                heatmap = self._compute_kde_heatmap(data_points, grid_points)
                self.heatmaps[period_key] = heatmap
                
                periods.append({
                    'period': period_key,
                    'count': len(period_data),
                    'max_density': float(heatmap.max()),
                    'mean_density': float(heatmap.mean())
                })
        
        # Heatmap global (todos los datos)
        print("\nCalculando heatmap global...")
        all_data_points = df[['latitud', 'longitud']].values
        global_heatmap = self._compute_kde_heatmap(all_data_points, grid_points)
        self.heatmaps['global'] = global_heatmap
        
        # Guardar estadísticas
        self.stats = {
            'total_records': len(df),
            'grid_resolution': self.grid_resolution,
            'grid_size': len(grid_points),
            'periods': periods,
            'global_max_density': float(global_heatmap.max()),
            'global_mean_density': float(global_heatmap.mean())
        }
        
        print(f"\n✅ Modelo entrenado exitosamente")
        print(f"   Heatmaps calculados: {len(self.heatmaps)}")
        print(f"   Períodos segmentados: {len(periods)}")
        
        return self
    
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
    
    def save(self, filepath):
        """Guarda el modelo"""
        model_data = {
            'heatmaps': {k: v.tolist() for k, v in self.heatmaps.items()},
            'grid_points': self.grid_points.tolist(),
            'lat_range': self.lat_range.tolist(),
            'lon_range': self.lon_range.tolist(),
            'grid_bounds': self.grid_bounds,
            'grid_resolution': self.grid_resolution,
            'kde_bandwidth': self.kde_bandwidth,
            'stats': self.stats
        }
        
        joblib.dump(model_data, filepath)
        print(f"Modelo guardado en: {filepath}")
    
    @classmethod
    def load(cls, filepath):
        """Carga el modelo"""
        model_data = joblib.load(filepath)
        
        model = cls(
            grid_resolution=model_data['grid_resolution'],
            kde_bandwidth=model_data.get('kde_bandwidth', 'scott')
        )
        
        model.heatmaps = {k: np.array(v) for k, v in model_data['heatmaps'].items()}
        model.grid_points = np.array(model_data['grid_points'])
        model.lat_range = np.array(model_data['lat_range'])
        model.lon_range = np.array(model_data['lon_range'])
        model.grid_bounds = model_data['grid_bounds']
        model.stats = model_data.get('stats', {})
        
        return model


def main():
    """Función principal"""
    print("=" * 60)
    print("ENTRENAMIENTO DEL MODELO DE DENSIDAD/HOTSPOTS")
    print("=" * 60)
    
    # 1. Cargar datos
    print("\n1. Cargando dataset...")
    df = pd.read_csv("dataset_postprocess.csv")
    print(f"   Dataset cargado: {len(df):,} registros")
    
    # Verificar columnas necesarias
    required_cols = ['latitud', 'longitud', 'hour', 'dayofweek']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Faltan columnas requeridas: {missing_cols}")
    
    # Asegurar que is_weekend existe
    if 'is_weekend' not in df.columns:
        df['is_weekend'] = (df['dayofweek'] >= 5).astype(int)
    
    # 2. Entrenar modelo
    print("\n2. Entrenando modelo de densidad...")
    model = DensityHotspotModel(
        grid_resolution=0.0045,  # ~500m
        kde_bandwidth='scott'  # Método automático de Scott
    )
    
    model.fit(df)
    
    # 3. Guardar modelo
    print("\n3. Guardando modelo...")
    model_path = "../backend/models/density_hotspot_model.pkl"
    model.save(model_path)
    
    # 4. Guardar estadísticas
    stats_path = "../backend/models/density_model_stats.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(model.stats, f, indent=2, ensure_ascii=False)
    print(f"   Estadísticas guardadas en: {stats_path}")
    
    # 5. Prueba rápida
    print("\n4. Prueba de predicción...")
    test_lat = df['latitud'].median()
    test_lon = df['longitud'].median()
    test_hour = 14
    test_dayofweek = 1  # Lunes
    
    prob = model.predict_density(test_lat, test_lon, test_hour, test_dayofweek, is_weekend=0)
    print(f"   Punto de prueba: ({test_lat:.4f}, {test_lon:.4f})")
    print(f"   Hora: {test_hour}, Día: {test_dayofweek} (weekday)")
    print(f"   Probabilidad de riesgo: {prob:.4f}")
    
    print("\n" + "=" * 60)
    print("ENTRENAMIENTO COMPLETADO")
    print("=" * 60)
    print(f"\nModelo guardado en: {model_path}")
    print(f"El modelo está listo para usar en producción.")


if __name__ == "__main__":
    main()


"""
Sistema de Predicción de Riesgo de Hurto en Rutas
================================================

Este módulo implementa un sistema de predicción de riesgo de hurto basado en datos históricos
de Medellín. Utiliza una cuadrícula de 500m x 500m para analizar patrones espaciales y temporales.

Autor: Sistema Alerta Vial
Fecha: 2024
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Optional
import json
from datetime import datetime
import os

class PredictorRiesgoRutas:
    """
    Sistema de predicción de riesgo de hurto en rutas basado en datos históricos.
    
    Utiliza una cuadrícula espacial de 500m x 500m para analizar patrones de hurto
    y calcular scores de riesgo para rutas específicas.
    """
    
    def __init__(self, datos_celdas_path: str = None):
        """
        Inicializa el predictor con los datos de celdas y sus scores de riesgo.
        
        Args:
            datos_celdas_path: Ruta al archivo CSV con datos de celdas y scores
        """
        self.cell_size = 0.0045  # Tamaño de celda en grados (aprox 500m)
        self.latitud_min = 6.15
        self.longitud_min = -75.71
        
        # Cargar datos de celdas
        if datos_celdas_path and os.path.exists(datos_celdas_path):
            self.datos_celdas = pd.read_csv(datos_celdas_path)
        else:
            # Crear datos vacíos si no se encuentra el archivo
            self.datos_celdas = pd.DataFrame()
            print("⚠️ Advertencia: No se encontraron datos de celdas. Inicializando con datos vacíos.")
    
    def coordenadas_a_celda(self, lat: float, lon: float) -> Optional[int]:
        """
        Convierte coordenadas a ID de celda.
        
        Args:
            lat: Latitud
            lon: Longitud
            
        Returns:
            ID de la celda correspondiente o None si está fuera del área
        """
        if self.datos_celdas.empty:
            return None
            
        # Buscar celda correspondiente usando coordenadas
        celda = self.datos_celdas[
            (self.datos_celdas['lat_centro'] >= lat - self.cell_size/2) &
            (self.datos_celdas['lat_centro'] < lat + self.cell_size/2) &
            (self.datos_celdas['lon_centro'] >= lon - self.cell_size/2) &
            (self.datos_celdas['lon_centro'] < lon + self.cell_size/2)
        ]
        
        if len(celda) > 0:
            return celda.iloc[0]['celda_id']
        return None
    
    def calcular_riesgo_ruta(self, 
                           puntos_ruta: List[Tuple[float, float]], 
                           hora_consulta: Optional[int] = None, 
                           dia_semana: Optional[int] = None,
                           incluir_detalles: bool = True) -> Dict:
        """
        Calcula el riesgo de una ruta basado en los puntos que la componen.
        
        Args:
            puntos_ruta: Lista de tuplas (lat, lon) que forman la ruta
            hora_consulta: Hora de la consulta (0-23)
            dia_semana: Día de la semana (0-6, donde 0 es lunes)
            incluir_detalles: Si incluir información detallada de cada segmento
            
        Returns:
            Dict con información de riesgo de la ruta
        """
        if self.datos_celdas.empty:
            return self._respuesta_sin_datos()
        
        segmentos_riesgo = []
        score_total = 0
        celdas_unicas = set()
        
        for i, (lat, lon) in enumerate(puntos_ruta):
            celda_id = self.coordenadas_a_celda(lat, lon)
            
            if celda_id is not None:
                celda_data = self.datos_celdas[self.datos_celdas['celda_id'] == celda_id]
                
                if len(celda_data) > 0:
                    celda_info = celda_data.iloc[0]
                    celdas_unicas.add(celda_id)
                    
                    # Ajustar score por hora del día si se proporciona
                    score_ajustado = celda_info['score_riesgo']
                    
                    if hora_consulta is not None:
                        score_ajustado = self._ajustar_por_hora(
                            score_ajustado, celda_info, hora_consulta
                        )
                    
                    segmento_info = {
                        'segmento': i,
                        'lat': lat,
                        'lon': lon,
                        'celda_id': celda_id,
                        'score_riesgo': score_ajustado,
                        'nivel_riesgo': celda_info['nivel_riesgo'],
                        'total_hurtos': celda_info['total_hurtos']
                    }
                    
                    if incluir_detalles:
                        segmento_info.update({
                            'hora_promedio': celda_info['hora_promedio'],
                            'modalidad_comun': celda_info['modalidad_comun'],
                            'lugar_comun': celda_info['lugar_comun'],
                            'densidad_hurtos': celda_info['densidad_hurtos']
                        })
                    
                    segmentos_riesgo.append(segmento_info)
                    score_total += score_ajustado
        
        # Calcular métricas de la ruta
        if len(segmentos_riesgo) > 0:
            score_promedio = score_total / len(segmentos_riesgo)
            score_maximo = max(seg['score_riesgo'] for seg in segmentos_riesgo)
            
            # Clasificar riesgo general de la ruta
            riesgo_general = self._clasificar_riesgo_general(score_promedio)
            
            # Generar recomendaciones
            recomendaciones = self._generar_recomendaciones(
                segmentos_riesgo, hora_consulta, dia_semana
            )
            
            return {
                'riesgo_general': riesgo_general,
                'score_promedio': round(score_promedio, 2),
                'score_maximo': round(score_maximo, 2),
                'total_segmentos': len(segmentos_riesgo),
                'celdas_unicas': len(celdas_unicas),
                'segmentos_riesgo': segmentos_riesgo if incluir_detalles else [],
                'recomendaciones': recomendaciones,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return self._respuesta_sin_datos()
    
    def _ajustar_por_hora(self, score_base: float, celda_info: pd.Series, hora_consulta: int) -> float:
        """
        Ajusta el score de riesgo basado en la hora de consulta.
        """
        hora_promedio = celda_info['hora_promedio']
        hora_std = celda_info['hora_std']
        
        # Si la hora consultada está cerca de la hora promedio de hurtos
        if abs(hora_consulta - hora_promedio) <= hora_std:
            return score_base * 1.2  # 20% más riesgo
        elif abs(hora_consulta - hora_promedio) <= hora_std * 2:
            return score_base * 1.1  # 10% más riesgo
        
        return score_base
    
    def _clasificar_riesgo_general(self, score_promedio: float) -> str:
        """
        Clasifica el nivel de riesgo general de la ruta.
        """
        if score_promedio >= 70:
            return 'MUY_ALTO'
        elif score_promedio >= 50:
            return 'ALTO'
        elif score_promedio >= 30:
            return 'MEDIO'
        elif score_promedio >= 15:
            return 'BAJO'
        else:
            return 'MUY_BAJO'
    
    def _generar_recomendaciones(self, 
                               segmentos_riesgo: List[Dict], 
                               hora_consulta: Optional[int] = None,
                               dia_semana: Optional[int] = None) -> List[str]:
        """
        Genera recomendaciones basadas en el análisis de riesgo.
        """
        recomendaciones = []
        
        # Analizar segmentos de alto riesgo
        segmentos_alto_riesgo = [
            seg for seg in segmentos_riesgo 
            if seg['nivel_riesgo'] in ['ALTO', 'MUY_ALTO']
        ]
        
        if len(segmentos_alto_riesgo) > 0:
            recomendaciones.append(
                f"⚠️ Evitar {len(segmentos_alto_riesgo)} segmentos de alto riesgo"
            )
            
            # Recomendaciones específicas por hora
            if hora_consulta is not None:
                if 18 <= hora_consulta <= 23:
                    recomendaciones.append("🌙 Horario nocturno: mayor precaución recomendada")
                elif 6 <= hora_consulta <= 8:
                    recomendaciones.append("🌅 Horario matutino: estar alerta en zonas de alto tráfico")
        
        # Analizar patrones temporales
        horas_riesgo = [
            seg['hora_promedio'] for seg in segmentos_riesgo 
            if seg.get('hora_promedio', 0) > 0
        ]
        
        if len(horas_riesgo) > 0:
            hora_mas_riesgo = max(set(horas_riesgo), key=horas_riesgo.count)
            recomendaciones.append(
                f"⏰ Mayor actividad delictiva reportada alrededor de las {int(hora_mas_riesgo)}:00"
            )
        
        # Recomendaciones generales
        if len(segmentos_riesgo) > 5:
            recomendaciones.append("🛣️ Ruta larga: considerar alternativas más seguras")
        
        # Recomendaciones por día de la semana
        if dia_semana is not None:
            if dia_semana in [5, 6]:  # Fin de semana
                recomendaciones.append("📅 Fin de semana: mayor vigilancia en zonas comerciales")
        
        if not recomendaciones:
            recomendaciones.append("✅ Ruta con riesgo bajo según datos históricos")
        
        return recomendaciones
    
    def _respuesta_sin_datos(self) -> Dict:
        """
        Retorna respuesta estándar cuando no hay datos disponibles.
        """
        return {
            'riesgo_general': 'SIN_DATOS',
            'score_promedio': 0,
            'score_maximo': 0,
            'total_segmentos': 0,
            'celdas_unicas': 0,
            'segmentos_riesgo': [],
            'recomendaciones': ['No se encontraron datos de riesgo para esta ruta'],
            'timestamp': datetime.now().isoformat()
        }
    
    def obtener_info_celda(self, lat: float, lon: float) -> Dict:
        """
        Obtiene información detallada de una celda específica.
        
        Args:
            lat: Latitud
            lon: Longitud
            
        Returns:
            Dict con información de la celda
        """
        celda_id = self.coordenadas_a_celda(lat, lon)
        
        if celda_id is None:
            return {'error': 'Coordenadas fuera del área de cobertura'}
        
        celda_data = self.datos_celdas[self.datos_celdas['celda_id'] == celda_id]
        
        if len(celda_data) == 0:
            return {'error': 'No se encontraron datos para esta celda'}
        
        celda_info = celda_data.iloc[0]
        
        # Información básica
        info = {
            'celda_id': celda_id,
            'lat_centro': celda_info['lat_centro'],
            'lon_centro': celda_info['lon_centro'],
            'score_riesgo': celda_info['score_riesgo'],
            'nivel_riesgo': celda_info['nivel_riesgo'],
            'total_hurtos': celda_info['total_hurtos'],
            'densidad_hurtos': celda_info['densidad_hurtos'],
            'hora_promedio': celda_info['hora_promedio'],
            'modalidad_comun': celda_info['modalidad_comun'],
            'lugar_comun': celda_info['lugar_comun']
        }
        
        # Agregar información de clustering si está disponible
        if 'cluster' in celda_info:
            info['cluster_id'] = celda_info['cluster']
            # Obtener información del cluster
            cluster_data = self.datos_celdas[self.datos_celdas['cluster'] == celda_info['cluster']]
            info['cluster_info'] = {
                'total_celdas': len(cluster_data),
                'score_promedio_cluster': cluster_data['score_riesgo'].mean(),
                'nivel_predominante': cluster_data['nivel_riesgo'].mode().iloc[0] if len(cluster_data) > 0 else 'N/A'
            }
        
        return info
    
    def obtener_info_cluster(self, cluster_id: int) -> Dict:
        """
        Obtiene información detallada de un cluster específico.
        
        Args:
            cluster_id: ID del cluster
            
        Returns:
            Dict con información del cluster
        """
        if self.datos_celdas.empty:
            return {'error': 'No hay datos disponibles'}
        
        cluster_data = self.datos_celdas[self.datos_celdas['cluster'] == cluster_id]
        
        if len(cluster_data) == 0:
            return {'error': f'Cluster {cluster_id} no encontrado'}
        
        # Estadísticas del cluster
        stats = {
            'cluster_id': cluster_id,
            'total_celdas': len(cluster_data),
            'score_promedio': cluster_data['score_riesgo'].mean(),
            'score_std': cluster_data['score_riesgo'].std(),
            'hurtos_totales': cluster_data['total_hurtos'].sum(),
            'hurtos_promedio': cluster_data['total_hurtos'].mean(),
            'densidad_promedio': cluster_data['densidad_hurtos'].mean(),
            'hora_promedio': cluster_data['hora_promedio'].mean(),
            'edad_promedio_victimas': cluster_data['edad_promedio'].mean(),
            'ubicacion_centro': {
                'lat': cluster_data['lat_centro'].mean(),
                'lon': cluster_data['lon_centro'].mean()
            },
            'distribucion_riesgo': cluster_data['nivel_riesgo'].value_counts().to_dict(),
            'nivel_predominante': cluster_data['nivel_riesgo'].mode().iloc[0]
        }
        
        return stats
    
    def obtener_estadisticas_generales(self) -> Dict:
        """
        Obtiene estadísticas generales del sistema.
        """
        if self.datos_celdas.empty:
            return {'error': 'No hay datos disponibles'}
        
        total_celdas = len(self.datos_celdas)
        celdas_con_hurtos = len(self.datos_celdas[self.datos_celdas['total_hurtos'] > 0])
        
        distribucion_riesgo = self.datos_celdas['nivel_riesgo'].value_counts().to_dict()
        
        stats = {
            'total_celdas': total_celdas,
            'celdas_con_hurtos': celdas_con_hurtos,
            'celdas_sin_hurtos': total_celdas - celdas_con_hurtos,
            'distribucion_riesgo': distribucion_riesgo,
            'score_promedio': self.datos_celdas['score_riesgo'].mean(),
            'score_maximo': self.datos_celdas['score_riesgo'].max(),
            'total_hurtos_historicos': self.datos_celdas['total_hurtos'].sum()
        }
        
        # Agregar información de clusters si está disponible
        if 'cluster' in self.datos_celdas.columns:
            clusters_unicos = self.datos_celdas['cluster'].nunique()
            distribucion_clusters = self.datos_celdas['cluster'].value_counts().to_dict()
            
            stats.update({
                'total_clusters': clusters_unicos,
                'distribucion_clusters': distribucion_clusters,
                'clustering_disponible': True
            })
        else:
            stats['clustering_disponible'] = False
        
        return stats


# Función de utilidad para crear el predictor
def crear_predictor(datos_celdas_path: str = "resumen_hurtos_por_celda.csv") -> PredictorRiesgoRutas:
    """
    Crea una instancia del predictor con los datos de celdas.
    
    Args:
        datos_celdas_path: Ruta al archivo CSV con datos de celdas
        
    Returns:
        Instancia del PredictorRiesgoRutas
    """
    return PredictorRiesgoRutas(datos_celdas_path)


if __name__ == "__main__":
    # Ejemplo de uso - especificar la ruta correcta del archivo
    predictor = crear_predictor("ml_service/analisis_inicial/resumen_hurtos_por_celda.csv")
    
    # Ejemplo de ruta con ALTO RIESGO (zonas con muchos hurtos históricos)
    ruta_ejemplo = [
        (6.18375, -75.57275),  # Zona ALTO riesgo (355 hurtos)
        (6.18825, -75.57725),  # Zona ALTO riesgo (387 hurtos) 
        (6.19275, -75.57725),  # Zona ALTO riesgo (882 hurtos)
        (6.19725, -75.58625)   # Zona ALTO riesgo (461 hurtos)
    ]
    
    # Analizar ruta en horario de mayor actividad
    resultado = predictor.calcular_riesgo_ruta(ruta_ejemplo, hora_consulta=14, dia_semana=3)
    print("Resultado del análisis:")
    
    # Mostrar resultado de forma más simple
    print(f"Riesgo general: {resultado['riesgo_general']}")
    print(f"Score promedio: {resultado['score_promedio']}")
    print(f"Score máximo: {resultado['score_maximo']}")
    print(f"Total segmentos: {resultado['total_segmentos']}")
    print(f"Celdas únicas: {resultado['celdas_unicas']}")
    print(f"Recomendaciones:")
    for rec in resultado['recomendaciones']:
        print(f"  • {rec}")
    
    print(f"\nDetalles de segmentos:")
    for i, seg in enumerate(resultado['segmentos_riesgo']):
        print(f"  Segmento {i+1}: {seg['nivel_riesgo']} (Score: {seg['score_riesgo']:.1f})")
        print(f"    Ubicación: ({seg['lat']:.4f}, {seg['lon']:.4f})")
        print(f"    Total hurtos: {seg['total_hurtos']}")
        print()

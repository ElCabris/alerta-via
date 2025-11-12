import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface StatisticsOverview {
  total_incidentes: number;
  incidentes_hoy: number;
  incidentes_ultimo_mes: number;
  zonas_seguras: number;
  tendencia: string;
  cambio_porcentual: number;
}

export interface IncidentByType {
  type: string;
  count: number;
}

export interface IncidentByHour {
  hour: number;
  count: number;
  label: string;
}

export interface IncidentByDay {
  day: string;
  day_en: string;
  count: number;
}

export interface IncidentByBarrio {
  barrio: string;
  count: number;
}

export interface TimelinePoint {
  date: string;
  count: number;
}

export interface HeatmapPoint {
  lat: number;
  lng: number;
  intensity: number;
  risk: string;
  count: number;
}

@Injectable({
  providedIn: 'root'
})
export class StatisticsService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  /**
   * Obtiene estadísticas generales del sistema
   */
  getOverview(): Observable<StatisticsOverview> {
    return this.http.get<StatisticsOverview>(`${this.apiUrl}/statistics/overview`);
  }

  /**
   * Obtiene estadísticas de incidentes por tipo
   */
  getByType(): Observable<{ incidents_by_type: IncidentByType[] }> {
    return this.http.get<{ incidents_by_type: IncidentByType[] }>(`${this.apiUrl}/statistics/by-type`);
  }

  /**
   * Obtiene estadísticas de incidentes por hora del día
   */
  getByTime(): Observable<{ incidents_by_hour: IncidentByHour[] }> {
    return this.http.get<{ incidents_by_hour: IncidentByHour[] }>(`${this.apiUrl}/statistics/by-time`);
  }

  /**
   * Obtiene estadísticas de incidentes por día de la semana
   */
  getByDay(): Observable<{ incidents_by_day: IncidentByDay[] }> {
    return this.http.get<{ incidents_by_day: IncidentByDay[] }>(`${this.apiUrl}/statistics/by-day`);
  }

  /**
   * Obtiene estadísticas de incidentes por barrio
   */
  getByBarrio(limit: number = 10): Observable<{ incidents_by_barrio: IncidentByBarrio[] }> {
    return this.http.get<{ incidents_by_barrio: IncidentByBarrio[] }>(`${this.apiUrl}/statistics/by-barrio?limit=${limit}`);
  }

  /**
   * Obtiene línea de tiempo de incidentes
   */
  getTimeline(days: number = 30): Observable<{ timeline: TimelinePoint[] }> {
    return this.http.get<{ timeline: TimelinePoint[] }>(`${this.apiUrl}/statistics/timeline?days=${days}`);
  }

  /**
   * Obtiene datos para el mapa de calor
   */
  getHeatmapData(): Observable<{ heatmap_points: HeatmapPoint[] }> {
    return this.http.get<{ heatmap_points: HeatmapPoint[] }>(`${this.apiUrl}/statistics/heatmap-data`);
  }
}




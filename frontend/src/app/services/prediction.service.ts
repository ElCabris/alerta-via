import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Point {
  latitud: number;
  longitud: number;
}

export interface RouteRequest {
  puntos: Point[];
  fecha_hora?: string;
}

export interface PointPrediction {
  latitud: number;
  longitud: number;
  probabilidad: number;
  riesgo: 'alto' | 'medio' | 'bajo';
}

export interface RoutePredictionResponse {
  puntos: PointPrediction[];
  probabilidad_promedio: number;
  riesgo_alto_count: number;
  riesgo_medio_count: number;
  riesgo_bajo_count: number;
}

@Injectable({
  providedIn: 'root'
})
export class PredictionService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  /**
   * Predice la probabilidad de hurto para una ruta completa
   */
  predictRoute(request: RouteRequest): Observable<RoutePredictionResponse> {
    return this.http.post<RoutePredictionResponse>(`${this.apiUrl}/predict/route`, request);
  }

  /**
   * Predice la probabilidad de hurto para un solo punto
   */
  predictPoint(point: {
    latitud: number;
    longitud: number;
    fecha_hora?: string;
  }): Observable<PointPrediction> {
    return this.http.post<PointPrediction>(`${this.apiUrl}/predict/point`, point);
  }

  /**
   * Verifica el estado del sistema
   */
  checkHealth(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`);
  }

  /**
   * Obtiene información del modelo
   */
  getModelInfo(): Observable<any> {
    return this.http.get(`${this.apiUrl}/model/info`);
  }

  /**
   * Obtiene una ruta real usando OSRM (a través del backend para evitar CORS)
   */
  getRouteFromOSRM(
    originLat: number,
    originLng: number,
    destinationLat: number,
    destinationLng: number,
    profile: string = 'driving'
  ): Observable<any> {
    return this.http.post(`${this.apiUrl}/route/osrm`, {
      origin_lat: originLat,
      origin_lng: originLng,
      destination_lat: destinationLat,
      destination_lng: destinationLng,
      profile: profile
    });
  }

  /**
   * Geocodifica una dirección a coordenadas
   */
  geocodeAddress(address: string): Observable<{
    latitud: number;
    longitud: number;
    direccion: string;
    direccion_original: string;
  }> {
    return this.http.post<{
      latitud: number;
      longitud: number;
      direccion: string;
      direccion_original: string;
    }>(`${this.apiUrl}/geocode`, { address });
  }
}


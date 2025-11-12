import { Component, OnInit, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { PredictionService, RouteRequest, RoutePredictionResponse, PointPrediction, GeocodeSuggestion } from '../../services/prediction.service';

// Declarar Leaflet para TypeScript
declare var L: any;

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule]
})
export class DashboardComponent implements OnInit, AfterViewInit, OnDestroy {
  currentTime: string = '';
  isQuickActionsOpen: boolean = false;
  showLogoutModal: boolean = false;

  // Variables para el mapa
  private map: any;
  private markers: any[] = [];
  private userLocation: any = null;
  private routePolyline: any = null;
  private routeMarkers: any[] = [];

  // Variables para origen y destino
  originInput: string = '';
  destinationInput: string = '';
  originCoords: { lat: number; lng: number } | null = null;
  destinationCoords: { lat: number; lng: number } | null = null;
  selectionMode: 'origin' | 'destination' | 'auto' = 'auto'; // Modo de selección
  
  // Variables para geocodificación
  isGeocodingOrigin: boolean = false;
  isGeocodingDestination: boolean = false;
  originAddress: string = '';  // Dirección formateada del origen
  destinationAddress: string = '';  // Dirección formateada del destino
  originSuggestions: GeocodeSuggestion[] = [];
  destinationSuggestions: GeocodeSuggestion[] = [];
  showOriginSuggestions: boolean = false;
  showDestinationSuggestions: boolean = false;

  private originSearchTimeout: any = null;
  private destinationSearchTimeout: any = null;

  // Variables para predicciones
  isLoadingPrediction: boolean = false;
  predictionResult: RoutePredictionResponse | null = null;
  predictionError: string = '';

  constructor(
    private router: Router,
    private predictionService: PredictionService
  ) { }

  ngOnInit() {
    this.updateTime();
    setInterval(() => this.updateTime(), 60000);
  }

  ngAfterViewInit() {
    // Inicializar el mapa después de que la vista se haya renderizado
    setTimeout(() => {
      this.initializeMap();
    }, 100);
  }

  ngOnDestroy() {
    // Limpiar el mapa al destruir el componente
    if (this.map) {
      this.map.remove();
    }

    if (this.originSearchTimeout) {
      clearTimeout(this.originSearchTimeout);
    }

    if (this.destinationSearchTimeout) {
      clearTimeout(this.destinationSearchTimeout);
    }
  }

  initializeMap() {
    // Coordenadas por defecto (Medellín, Colombia)
    const defaultLat = 6.2442;
    const defaultLng = -75.5812;

    // Crear el mapa
    this.map = L.map('map').setView([defaultLat, defaultLng], 13);

    // Agregar capa de tiles (usando OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18
    }).addTo(this.map);

    // Intentar obtener la ubicación del usuario
    this.getUserLocation();

    // Agregar controles al mapa
    this.addMapControls();

    // Permitir hacer clic en el mapa para establecer origen/destino
    this.map.on('click', (e: any) => {
      this.onMapClick(e);
    });
  }

  getUserLocation() {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          this.userLocation = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          };

          // Centrar el mapa en la ubicación del usuario
          this.map.setView([this.userLocation.lat, this.userLocation.lng], 15);

          // Agregar marcador de ubicación del usuario
          this.addUserMarker();

          // Si no hay origen, usar la ubicación actual como origen
          if (!this.originCoords) {
            this.originCoords = { ...this.userLocation };
          }
        },
        (error) => {
          // Silenciar el error de geolocalización, usar ubicación por defecto
          // Esto es normal si el usuario no permite permisos o no está en HTTPS/localhost
          this.userLocation = { lat: 6.2442, lng: -75.5812 };
          this.originCoords = { lat: 6.2442, lng: -75.5812 };
        }
      );
    }
  }

  addUserMarker() {
    if (this.userLocation) {
      const userIcon = L.divIcon({
        html: '<div class="user-marker"></div>',
        className: 'user-location-marker',
        iconSize: [20, 20]
      });

      const marker = L.marker([this.userLocation.lat, this.userLocation.lng], {
        icon: userIcon
      }).addTo(this.map)
        .bindPopup('Tu ubicación actual')
        .openPopup();

      this.markers.push(marker);
    }
  }

  onMapClick(e: any) {
    const coords = { lat: e.latlng.lat, lng: e.latlng.lng };
    
    // Determinar qué punto establecer según el modo
    if (this.selectionMode === 'origin') {
      // Establecer origen
      if (this.originCoords) {
        // Remover marcador anterior
        this.removeOriginMarker();
      }
      this.originCoords = coords;
      this.addOriginMarker(coords);
      // Si ya hay destino, limpiar ruta anterior
      if (this.destinationCoords) {
        this.clearRoute();
      }
    } else if (this.selectionMode === 'destination') {
      // Establecer destino
      if (this.destinationCoords) {
        // Remover marcador anterior
        this.removeDestinationMarker();
      }
      this.destinationCoords = coords;
      this.addDestinationMarker(coords);
      // Si ya hay origen, limpiar ruta anterior
      if (this.originCoords) {
        this.clearRoute();
      }
    } else {
      // Modo automático: establecer origen primero, luego destino
      if (!this.originCoords) {
        this.originCoords = coords;
        this.addOriginMarker(coords);
      } else if (!this.destinationCoords) {
        this.destinationCoords = coords;
        this.addDestinationMarker(coords);
      } else {
        // Si ambos están establecidos, reemplazar destino por defecto
        this.removeDestinationMarker();
        this.destinationCoords = coords;
        this.addDestinationMarker(coords);
        this.clearRoute();
      }
    }
  }

  setSelectionMode(mode: 'origin' | 'destination' | 'auto') {
    this.selectionMode = mode;
  }

  clearOrigin() {
    this.removeOriginMarker();
    this.originCoords = null;
    this.originInput = '';
    this.originAddress = '';
    this.originSuggestions = [];
    this.showOriginSuggestions = false;
    this.clearRoute();
  }

  clearDestination() {
    this.removeDestinationMarker();
    this.destinationCoords = null;
    this.destinationInput = '';
    this.destinationAddress = '';
    this.destinationSuggestions = [];
    this.showDestinationSuggestions = false;
    this.clearRoute();
  }

  /**
   * Geocodifica una dirección a coordenadas
   */
  geocodeOrigin() {
    if (!this.originInput.trim()) {
      alert('Por favor, ingresa una dirección');
      return;
    }

    this.isGeocodingOrigin = true;
    this.predictionError = '';

    this.predictionService.geocodeAddress(this.originInput).subscribe({
      next: (results) => {
        this.isGeocodingOrigin = false;

        this.originSuggestions = results;
        this.showOriginSuggestions = results.length > 0;

        if (results.length === 0) {
          this.predictionError = `No se encontraron direcciones similares para: ${this.originInput}`;
          return;
        }

        // Seleccionar automáticamente el primer resultado, pero mantener visibles las sugerencias
        this.applyOriginSuggestion(results[0], { centerMap: true, hideSuggestions: false });
      },
      error: (error) => {
        console.error('Error al geocodificar origen:', error);
        this.predictionError = error.error?.detail || `No se pudo buscar la dirección: ${this.originInput}`;
        this.isGeocodingOrigin = false;
      }
    });
  }

  /**
   * Geocodifica una dirección de destino a coordenadas
   */
  geocodeDestination() {
    if (!this.destinationInput.trim()) {
      alert('Por favor, ingresa una dirección');
      return;
    }

    this.isGeocodingDestination = true;
    this.predictionError = '';

    this.predictionService.geocodeAddress(this.destinationInput).subscribe({
      next: (results) => {
        this.isGeocodingDestination = false;

        this.destinationSuggestions = results;
        this.showDestinationSuggestions = results.length > 0;

        if (results.length === 0) {
          this.predictionError = `No se encontraron direcciones similares para: ${this.destinationInput}`;
          return;
        }

        // Seleccionar automáticamente el primer resultado, pero mantener visibles las sugerencias
        this.applyDestinationSuggestion(results[0], { centerMap: true, hideSuggestions: false });
      },
      error: (error) => {
        console.error('Error al geocodificar destino:', error);
        this.predictionError = error.error?.detail || `No se pudo buscar la dirección: ${this.destinationInput}`;
        this.isGeocodingDestination = false;
      }
    });
  }

  onOriginInputChange(value: string) {
    this.originInput = value;
    this.originAddress = '';

    if (this.originSearchTimeout) {
      clearTimeout(this.originSearchTimeout);
    }

    if (!value.trim() || value.trim().length < 3) {
      this.originSuggestions = [];
      this.showOriginSuggestions = false;
      return;
    }

    this.originSearchTimeout = setTimeout(() => {
      this.fetchOriginSuggestions(value.trim());
    }, 400);
  }

  onDestinationInputChange(value: string) {
    this.destinationInput = value;
    this.destinationAddress = '';

    if (this.destinationSearchTimeout) {
      clearTimeout(this.destinationSearchTimeout);
    }

    if (!value.trim() || value.trim().length < 3) {
      this.destinationSuggestions = [];
      this.showDestinationSuggestions = false;
      return;
    }

    this.destinationSearchTimeout = setTimeout(() => {
      this.fetchDestinationSuggestions(value.trim());
    }, 400);
  }

  onOriginInputFocus() {
    if (this.originSuggestions.length > 0) {
      this.showOriginSuggestions = true;
    }
  }

  onDestinationInputFocus() {
    if (this.destinationSuggestions.length > 0) {
      this.showDestinationSuggestions = true;
    }
  }

  onOriginInputBlur() {
    setTimeout(() => {
      this.showOriginSuggestions = false;
    }, 200);
  }

  onDestinationInputBlur() {
    setTimeout(() => {
      this.showDestinationSuggestions = false;
    }, 200);
  }

  selectOriginSuggestion(suggestion: GeocodeSuggestion) {
    this.predictionError = '';
    this.applyOriginSuggestion(suggestion, { centerMap: true, hideSuggestions: true });
  }

  selectDestinationSuggestion(suggestion: GeocodeSuggestion) {
    this.predictionError = '';
    this.applyDestinationSuggestion(suggestion, { centerMap: true, hideSuggestions: true });
  }

  private fetchOriginSuggestions(query: string) {
    this.predictionService.geocodeAddress(query).subscribe({
      next: (results) => {
        this.originSuggestions = results;
        this.showOriginSuggestions = results.length > 0;
      },
      error: (error) => {
        console.error('Error al obtener sugerencias de origen:', error);
        this.originSuggestions = [];
        this.showOriginSuggestions = false;
      }
    });
  }

  private fetchDestinationSuggestions(query: string) {
    this.predictionService.geocodeAddress(query).subscribe({
      next: (results) => {
        this.destinationSuggestions = results;
        this.showDestinationSuggestions = results.length > 0;
      },
      error: (error) => {
        console.error('Error al obtener sugerencias de destino:', error);
        this.destinationSuggestions = [];
        this.showDestinationSuggestions = false;
      }
    });
  }

  private applyOriginSuggestion(
    suggestion: GeocodeSuggestion,
    options: { centerMap?: boolean; hideSuggestions?: boolean } = {}
  ) {
    const { centerMap = true, hideSuggestions = true } = options;

    this.originCoords = {
      lat: suggestion.latitud,
      lng: suggestion.longitud
    };
    this.originAddress = suggestion.direccion;
    this.originInput = suggestion.direccion;

    this.addOriginMarker(this.originCoords);

    if (centerMap && this.map) {
      this.map.setView([suggestion.latitud, suggestion.longitud], 15);
    }

    if (hideSuggestions) {
      this.showOriginSuggestions = false;
      this.originSuggestions = [];
    }

    this.clearRoute();
  }

  private applyDestinationSuggestion(
    suggestion: GeocodeSuggestion,
    options: { centerMap?: boolean; hideSuggestions?: boolean } = {}
  ) {
    const { centerMap = true, hideSuggestions = true } = options;

    this.destinationCoords = {
      lat: suggestion.latitud,
      lng: suggestion.longitud
    };
    this.destinationAddress = suggestion.direccion;
    this.destinationInput = suggestion.direccion;

    this.addDestinationMarker(this.destinationCoords);

    if (centerMap && this.map) {
      this.map.setView([suggestion.latitud, suggestion.longitud], 15);
    }

    if (hideSuggestions) {
      this.showDestinationSuggestions = false;
      this.destinationSuggestions = [];
    }

    this.clearRoute();
  }

  private originMarker: any = null;
  private destinationMarker: any = null;

  removeOriginMarker() {
    if (this.originMarker) {
      const markerToRemove = this.originMarker;
      this.map.removeLayer(markerToRemove);
      // Remover del array antes de ponerlo en null
      this.routeMarkers = this.routeMarkers.filter(m => m !== markerToRemove);
      this.originMarker = null;
    }
  }

  removeDestinationMarker() {
    if (this.destinationMarker) {
      const markerToRemove = this.destinationMarker;
      this.map.removeLayer(markerToRemove);
      // Remover del array antes de ponerlo en null
      this.routeMarkers = this.routeMarkers.filter(m => m !== markerToRemove);
      this.destinationMarker = null;
    }
  }

  addOriginMarker(coords: { lat: number; lng: number }) {
    // Remover marcador anterior si existe
    this.removeOriginMarker();

    const icon = L.divIcon({
      html: '<div class="marker-origin"><span>O</span><div class="marker-label">Origen</div></div>',
      className: 'marker-origin-container',
      iconSize: [32, 45]
    });

    this.originMarker = L.marker([coords.lat, coords.lng], { 
      icon,
      draggable: true,
      zIndexOffset: 1000
    }).addTo(this.map)
      .bindPopup('📍 Origen<br>Arrastra para mover');

    // Permitir arrastrar el marcador
    this.originMarker.on('dragend', (e: any) => {
      const newCoords = e.target.getLatLng();
      this.originCoords = { lat: newCoords.lat, lng: newCoords.lng };
      this.clearRoute();
      if (this.destinationCoords) {
        // Si hay destino, actualizar popup con coordenadas
        this.originMarker.setPopupContent(`📍 Origen<br>Lat: ${newCoords.lat.toFixed(6)}<br>Lng: ${newCoords.lng.toFixed(6)}`);
      }
    });
    
    this.routeMarkers.push(this.originMarker);
  }

  addDestinationMarker(coords: { lat: number; lng: number }) {
    // Remover marcador anterior si existe
    this.removeDestinationMarker();

    const icon = L.divIcon({
      html: '<div class="marker-destination"><span>D</span><div class="marker-label">Destino</div></div>',
      className: 'marker-destination-container',
      iconSize: [32, 45]
    });

    this.destinationMarker = L.marker([coords.lat, coords.lng], { 
      icon,
      draggable: true,
      zIndexOffset: 1000
    }).addTo(this.map)
      .bindPopup('📍 Destino<br>Arrastra para mover');

    // Permitir arrastrar el marcador
    this.destinationMarker.on('dragend', (e: any) => {
      const newCoords = e.target.getLatLng();
      this.destinationCoords = { lat: newCoords.lat, lng: newCoords.lng };
      this.clearRoute();
      if (this.originCoords) {
        // Si hay origen, actualizar popup con coordenadas
        this.destinationMarker.setPopupContent(`📍 Destino<br>Lat: ${newCoords.lat.toFixed(6)}<br>Lng: ${newCoords.lng.toFixed(6)}`);
      }
    });
    
    this.routeMarkers.push(this.destinationMarker);
  }

  getMarkerColor(riskLevel: string): string {
    switch (riskLevel) {
      case 'high': return '#dc3545';
      case 'medium': return '#ffc107';
      case 'low': return '#28a745';
      default: return '#6c757d';
    }
  }

  addMapControls() {
    // Agregar control de escala
    L.control.scale().addTo(this.map);

    // Agregar botón de localización
    const locateControl = L.control({ position: 'topleft' });

    locateControl.onAdd = () => {
      const div = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom');
      div.innerHTML = `
        <button class="locate-btn" title="Centrar en mi ubicación">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm8.94 3A8.994 8.994 0 0 0 13 3.06V1h-2v2.06A8.994 8.994 0 0 0 3.06 11H1v2h2.06A8.994 8.994 0 0 0 11 20.94V23h2v-2.06A8.994 8.994 0 0 0 20.94 13H23v-2h-2.06zM12 19c-3.87 0-7-3.13-7-7s3.13-7 7-7 7 3.13 7 7-3.13 7-7 7z"/>
          </svg>
        </button>
      `;

      div.addEventListener('click', () => {
        this.centerToUserLocation();
      });

      return div;
    };

    locateControl.addTo(this.map);
  }

  centerToUserLocation() {
    if (this.userLocation) {
      this.map.setView([this.userLocation.lat, this.userLocation.lng], 15);
    } else {
      this.getUserLocation();
    }
  }

  // Método para trazar ruta y obtener predicciones
  async traceRoute() {
    if (!this.originCoords || !this.destinationCoords) {
      alert('Por favor, establece origen y destino ingresando direcciones o haciendo clic en el mapa');
      return;
    }

    this.isLoadingPrediction = true;
    this.predictionError = '';
    this.predictionResult = null;

    try {
      // Obtener ruta real usando OSRM (solo por calles)
      const routePoints = await this.getRouteFromOSRM(
        this.originCoords,
        this.destinationCoords
      );

      if (routePoints.length === 0) {
        this.predictionError = 'No se pudo calcular una ruta entre los puntos seleccionados. Intenta con otros puntos.';
        this.isLoadingPrediction = false;
        return;
      }

      // Preparar request para la API
      const request: RouteRequest = {
        puntos: routePoints.map(p => ({ latitud: p.lat, longitud: p.lng }))
      };

      // Llamar al servicio de predicción
      this.predictionService.predictRoute(request).subscribe({
        next: (response) => {
          this.predictionResult = response;
          this.visualizeRouteWithRisk(response.puntos);
          this.isLoadingPrediction = false;
        },
        error: (error: any) => {
          console.error('Error al obtener predicción:', error);
          
          // Mensajes de error más descriptivos
          if (error.status === 0 || error.statusText === 'Unknown Error' || error.message?.includes('Connection refused')) {
            this.predictionError = 'No se puede conectar al servidor backend. Por favor, inicia el servidor ejecutando en una terminal: cd backend && python run_server.py';
          } else if (error.status === 503) {
            this.predictionError = 'El modelo no está disponible. Por favor, ejecuta primero: cd modelo_ML && python train_density_model.py';
          } else if (error.status === 400) {
            this.predictionError = 'Error en los datos enviados. Verifica que hayas establecido origen y destino.';
          } else {
            this.predictionError = `Error al obtener predicción: ${error.error?.detail || error.message || 'Error desconocido'}`;
          }
          
          this.isLoadingPrediction = false;
        }
      });
    } catch (error: any) {
      console.error('Error:', error);
      this.predictionError = error.message || 'Error al calcular la ruta. Verifica que los puntos sean accesibles por calles.';
      this.isLoadingPrediction = false;
    }
  }

  /**
   * Obtiene una ruta real usando OSRM (solo por calles)
   * Usa el backend como proxy para evitar problemas de CORS
   */
  getRouteFromOSRM(
    origin: { lat: number; lng: number },
    destination: { lat: number; lng: number }
  ): Promise<{ lat: number; lng: number }[]> {
    return new Promise((resolve, reject) => {
      // Usar perfil 'walking' por defecto (rutas peatonales)
      // OSRM generalmente devuelve rutas similares para todos los perfiles
      const profile = 'walking';

      // Llamar al backend que hace de proxy con OSRM
      this.predictionService.getRouteFromOSRM(
        origin.lat,
        origin.lng,
        destination.lat,
        destination.lng,
        profile
      ).subscribe({
        next: (data) => {
          // Extraer coordenadas de la respuesta
          if (data.coordinates && Array.isArray(data.coordinates)) {
            // Formato GeoJSON: [longitud, latitud]
            const routePoints = data.coordinates.map((coord: number[]) => ({
              lng: coord[0],
              lat: coord[1]
            }));
            resolve(routePoints);
          } else {
            reject(new Error('Formato de respuesta inválido'));
          }
        },
        error: (error) => {
          console.error('Error al obtener ruta de OSRM:', error);
          reject(new Error(error.error?.detail || 'No se pudo calcular la ruta. Verifica que los puntos sean accesibles por calles.'));
        }
      });
    });
  }


  visualizeRouteWithRisk(puntos: PointPrediction[]) {
    // Limpiar ruta anterior
    this.clearRoute();

    // Crear coordenadas para la polyline
    const coordinates = puntos.map(p => [p.latitud, p.longitud]);

    // Crear una polyline continua con colores por segmentos
    // Usar un gradiente o colores segmentados según el riesgo
    const segments: any[] = [];
    for (let i = 0; i < puntos.length - 1; i++) {
      const currentPoint = puntos[i];
      const nextPoint = puntos[i + 1];
      
      const color = this.getRiskColor(currentPoint.riesgo);
      
      // Crear segmento de ruta con color según riesgo
      const segment = L.polyline(
        [[currentPoint.latitud, currentPoint.longitud], [nextPoint.latitud, nextPoint.longitud]],
        {
          color: color,
          weight: 6,
          opacity: 0.8
        }
      ).addTo(this.map);

      segments.push(segment);
      this.routeMarkers.push(segment);
    }

    // Agregar marcadores de riesgo en puntos clave (cada 5 puntos para no saturar)
    const markerInterval = Math.max(1, Math.floor(puntos.length / 10));
    for (let i = 0; i < puntos.length; i += markerInterval) {
      const point = puntos[i];
      const color = this.getRiskColor(point.riesgo);
      
      const marker = L.circleMarker([point.latitud, point.longitud], {
        radius: 6,
        fillColor: color,
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.9
      }).addTo(this.map)
        .bindPopup(`
          <div class="risk-popup">
            <strong>Riesgo: ${point.riesgo.toUpperCase()}</strong><br>
            Probabilidad: ${(point.probabilidad * 100).toFixed(1)}%
          </div>
        `);

      this.routeMarkers.push(marker);
    }

    // Ajustar vista al mapa para mostrar toda la ruta
    if (coordinates.length > 0) {
      const bounds = L.latLngBounds(coordinates);
      this.map.fitBounds(bounds, { padding: [50, 50] });
    }
  }

  getRiskColor(riesgo: string): string {
    switch (riesgo) {
      case 'alto': return '#dc3545'; // Rojo
      case 'medio': return '#ffc107'; // Amarillo
      case 'bajo': return '#28a745'; // Verde
      default: return '#6c757d'; // Gris
    }
  }

  clearRoute() {
    // Eliminar polyline anterior
    if (this.routePolyline) {
      this.map.removeLayer(this.routePolyline);
      this.routePolyline = null;
    }

    // Eliminar solo los marcadores de ruta (no origen/destino)
    const markersToRemove = this.routeMarkers.filter(m => 
      m !== this.originMarker && m !== this.destinationMarker
    );
    markersToRemove.forEach(marker => {
      this.map.removeLayer(marker);
    });
    this.routeMarkers = this.routeMarkers.filter(m => 
      m === this.originMarker || m === this.destinationMarker
    );
  }

  clearRouteAndPoints() {
    this.clearRoute();
    this.removeOriginMarker();
    this.removeDestinationMarker();
    this.originCoords = null;
    this.destinationCoords = null;
    this.predictionResult = null;
    this.routeMarkers = [];
  }

  updateTime() {
    const now = new Date();
    this.currentTime = now.toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }

  toggleQuickActions() {
    this.isQuickActionsOpen = !this.isQuickActionsOpen;
  }

  openLogoutConfirmation() {
    this.showLogoutModal = true;
  }

  closeLogoutModal() {
    this.showLogoutModal = false;
  }

  confirmLogout() {
    console.log('Cerrando sesión...');

    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    sessionStorage.clear();

    this.closeLogoutModal();
    this.router.navigate(['/login']);
  }

  onKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape' && this.showLogoutModal) {
      this.closeLogoutModal();
    }
  }
}

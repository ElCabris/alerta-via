import { Component, OnInit, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';

// Declarar Leaflet para TypeScript
declare var L: any;

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
  standalone: true,
  imports: [CommonModule, RouterModule]
})
export class DashboardComponent implements OnInit, AfterViewInit, OnDestroy {
  currentTime: string = '';
  isQuickActionsOpen: boolean = false;
  showLogoutModal: boolean = false;

  // Variables para el mapa
  private map: any;
  private markers: any[] = [];
  private userLocation: any = null;

  constructor(private router: Router) { }

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
  }

  initializeMap() {
    // Coordenadas por defecto (puedes cambiarlas)
    const defaultLat = 19.4326; // Ciudad de México
    const defaultLng = -99.1332;

    // Crear el mapa
    this.map = L.map('map').setView([defaultLat, defaultLng], 13);

    // Agregar capa de tiles (usando OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18
    }).addTo(this.map);

    // Intentar obtener la ubicación del usuario
    this.getUserLocation();

    // Agregar marcadores de ejemplo (alertas)
    this.addSampleMarkers();

    // Agregar controles al mapa
    this.addMapControls();
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
        },
        (error) => {
          console.warn('No se pudo obtener la ubicación:', error);
          // Usar ubicación por defecto
          this.userLocation = { lat: 19.4326, lng: -99.1332 };
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

  addSampleMarkers() {
    // Marcadores de ejemplo para alertas
    const sampleAlerts = [
      { lat: 19.4326, lng: -99.1332, type: 'high', title: 'Robo frecuente', description: 'Zona de alto riesgo' },
      { lat: 19.4340, lng: -99.1400, type: 'medium', title: 'Robo ocasional', description: 'Mantente alerta' },
      { lat: 19.4300, lng: -99.1250, type: 'low', title: 'Riesgo bajo', description: 'Precaución normal' }
    ];

    sampleAlerts.forEach(alert => {
      const markerColor = this.getMarkerColor(alert.type);

      const alertIcon = L.divIcon({
        html: `<div class="alert-marker ${alert.type}"></div>`,
        className: `alert-marker-${alert.type}`,
        iconSize: [15, 15]
      });

      const marker = L.marker([alert.lat, alert.lng], {
        icon: alertIcon
      }).addTo(this.map)
        .bindPopup(`
          <div class="alert-popup">
            <h4>${alert.title}</h4>
            <p>${alert.description}</p>
            <div class="risk-level ${alert.type}">Riesgo ${alert.type}</div>
          </div>
        `);

      this.markers.push(marker);
    });
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

  // Método para trazar ruta (ejemplo básico)
  traceRoute(origin: string, destination: string) {
    // Aquí integrarías un servicio de routing como OSRM
    console.log('Trazando ruta desde:', origin, 'hasta:', destination);

    // Ejemplo de polyline simple
    if (this.userLocation) {
      const routeCoordinates = [
        [this.userLocation.lat, this.userLocation.lng],
        [19.4340, -99.1400] // Coordenada de ejemplo
      ];

      const polyline = L.polyline(routeCoordinates, {
        color: '#007bff',
        weight: 4,
        opacity: 0.7
      }).addTo(this.map);

      this.markers.push(polyline);
    }
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

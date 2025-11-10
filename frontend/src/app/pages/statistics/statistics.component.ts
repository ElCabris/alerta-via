import { Component, OnInit, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { StatisticsService, IncidentByType, IncidentByHour, IncidentByDay, IncidentByBarrio, TimelinePoint, HeatmapPoint } from '../../services/statistics.service';

// Declarar Leaflet para TypeScript
declare var L: any;

@Component({
  selector: 'app-statistics',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './statistics.component.html',
  styleUrls: ['./statistics.component.scss']
})
export class StatisticsComponent implements OnInit, AfterViewInit, OnDestroy {
  // Estadísticas generales
  stats: Array<{ label: string; value: string; trend: string }> = [];
  loading = true;

  showLogoutModal = false;
  private map: any = null;
  private heatmapLayer: any = null;

  // Datos de gráficos
  incidentsByType: IncidentByType[] = [];
  incidentsByHour: IncidentByHour[] = [];
  incidentsByDay: IncidentByDay[] = [];
  incidentsByBarrio: IncidentByBarrio[] = [];
  timeline: TimelinePoint[] = [];
  heatmapData: HeatmapPoint[] = [];

  // Configuración de gráficos
  private chartPadding = { left: 40, right: 40, top: 20, bottom: 40 };
  private chartWidth = 320;
  private chartHeight = 240;
  barWidth = 45;
  maxCount = 0;
  maxHourCount = 0;
  maxDayCount = 0;
  maxTimelineCount = 0;

  // Ticks del eje Y
  yAxisTicks: Array<{ value: number; y: number }> = [];
  yAxisTicksHour: Array<{ value: number; y: number }> = [];
  yAxisTicksTimeline: Array<{ value: number; y: number }> = [];

  // Configuración gráfico circular
  pieChartRadius = 100;
  pieChartCenterX = 200;
  pieChartCenterY = 200;

  constructor(
    private router: Router,
    private statisticsService: StatisticsService
  ) {}

  ngOnInit() {
    this.loadStatistics();
  }

  loadStatistics() {
    this.loading = true;

    // Cargar estadísticas generales
    this.statisticsService.getOverview().subscribe({
      next: (overview) => {
        const trend = overview.cambio_porcentual > 0 ? `+${overview.cambio_porcentual.toFixed(1)}%` : 
                     overview.cambio_porcentual < 0 ? `${overview.cambio_porcentual.toFixed(1)}%` : '0%';
        
        this.stats = [
          { 
            label: 'Total Incidentes', 
            value: overview.total_incidentes.toLocaleString(), 
            trend: '' 
          },
          { 
            label: 'Incidentes Hoy', 
            value: overview.incidentes_hoy.toString(), 
            trend: overview.incidentes_hoy > 0 ? `+${overview.incidentes_hoy}` : '0' 
          },
          { 
            label: 'Último Mes', 
            value: overview.incidentes_ultimo_mes.toString(), 
            trend: trend 
          },
          { 
            label: 'Zonas Seguras', 
            value: overview.zonas_seguras.toString(), 
            trend: '+' 
          }
        ];
      },
      error: (err) => {
        console.error('Error cargando overview:', err);
        this.stats = [
          { label: 'Total Incidentes', value: '0', trend: '' },
          { label: 'Incidentes Hoy', value: '0', trend: '0' },
          { label: 'Último Mes', value: '0', trend: '0%' },
          { label: 'Zonas Seguras', value: '0', trend: '+' }
        ];
      }
    });

    // Cargar incidentes por tipo
    this.statisticsService.getByType().subscribe({
      next: (data) => {
        this.incidentsByType = data.incidents_by_type;
        this.maxCount = Math.max(...this.incidentsByType.map(item => item.count), 1);
        this.updateYAxisTicks();
      },
      error: (err) => console.error('Error cargando por tipo:', err)
    });

    // Cargar incidentes por hora
    this.statisticsService.getByTime().subscribe({
      next: (data) => {
        this.incidentsByHour = data.incidents_by_hour;
        this.maxHourCount = Math.max(...this.incidentsByHour.map(item => item.count), 1);
        this.updateYAxisTicksHour();
      },
      error: (err) => console.error('Error cargando por hora:', err)
    });

    // Cargar incidentes por día
    this.statisticsService.getByDay().subscribe({
      next: (data) => {
        this.incidentsByDay = data.incidents_by_day;
        this.maxDayCount = Math.max(...this.incidentsByDay.map(item => item.count), 1);
        // Actualizar maxCount para el gráfico de días
        this.maxCount = this.maxDayCount;
        this.updateYAxisTicks();
      },
      error: (err) => console.error('Error cargando por día:', err)
    });

    // Cargar incidentes por barrio
    this.statisticsService.getByBarrio(10).subscribe({
      next: (data) => {
        this.incidentsByBarrio = data.incidents_by_barrio;
      },
      error: (err) => console.error('Error cargando por barrio:', err)
    });

    // Cargar línea de tiempo
    this.statisticsService.getTimeline(30).subscribe({
      next: (data) => {
        this.timeline = data.timeline;
        this.maxTimelineCount = Math.max(...this.timeline.map(item => item.count), 1);
        this.updateYAxisTicksTimeline();
      },
      error: (err) => console.error('Error cargando timeline:', err)
    });

    // Cargar datos del heatmap
    this.statisticsService.getHeatmapData().subscribe({
      next: (data) => {
        console.log('Datos del heatmap recibidos:', data.heatmap_points.length, 'puntos');
        this.heatmapData = data.heatmap_points;
        this.loading = false;
        // Si el mapa ya está inicializado, crear el heatmap
        if (this.map) {
          console.log('Mapa ya inicializado, creando heatmap...');
          this.createHeatmap(this.heatmapData);
        } else {
          console.log('Mapa aún no inicializado, se creará el heatmap cuando el mapa esté listo');
        }
      },
      error: (err) => {
        console.error('Error cargando heatmap:', err);
        this.loading = false;
      }
    });
  }

  updateYAxisTicks() {
    this.yAxisTicks = [];
    const tickCount = 5;
    for (let i = 0; i <= tickCount; i++) {
      const value = Math.round((this.maxCount / tickCount) * (tickCount - i));
      const y = this.chartPadding.top + (this.chartHeight / tickCount) * i;
      this.yAxisTicks.push({ value, y });
    }
  }

  updateYAxisTicksHour() {
    this.yAxisTicksHour = [];
    const tickCount = 5;
    for (let i = 0; i <= tickCount; i++) {
      const value = Math.round((this.maxHourCount / tickCount) * (tickCount - i));
      const y = this.chartPadding.top + (this.chartHeight / tickCount) * i;
      this.yAxisTicksHour.push({ value, y });
    }
  }

  updateYAxisTicksTimeline() {
    this.yAxisTicksTimeline = [];
    const tickCount = 5;
    for (let i = 0; i <= tickCount; i++) {
      const value = Math.round((this.maxTimelineCount / tickCount) * (tickCount - i));
      const y = this.chartPadding.top + (this.chartHeight / tickCount) * i;
      this.yAxisTicksTimeline.push({ value, y });
    }
  }

  // Métodos para calcular posiciones en el gráfico de barras
  getBarX(index: number): number {
    if (this.incidentsByType.length === 0) return 0;
    const spacing = (this.chartWidth - (this.barWidth * this.incidentsByType.length)) / (this.incidentsByType.length + 1);
    return this.chartPadding.left + spacing + (index * (this.barWidth + spacing));
  }

  getBarY(count: number): number {
    const normalizedHeight = (count / this.maxCount) * this.chartHeight;
    return this.chartPadding.top + this.chartHeight - normalizedHeight;
  }

  getBarHeight(count: number): number {
    return (count / this.maxCount) * this.chartHeight;
  }

  // Métodos para gráfico de horas
  getHourBarX(index: number): number {
    const barWidth = 12;
    const spacing = 2;
    return this.chartPadding.left + (index * (barWidth + spacing));
  }

  getHourBarY(count: number): number {
    const normalizedHeight = (count / this.maxHourCount) * this.chartHeight;
    return this.chartPadding.top + this.chartHeight - normalizedHeight;
  }

  getHourBarHeight(count: number): number {
    return (count / this.maxHourCount) * this.chartHeight;
  }

  // Métodos para gráfico de línea temporal
  getTimelineX(index: number): number {
    if (this.timeline.length <= 1) return this.chartPadding.left;
    const spacing = this.chartWidth / (this.timeline.length - 1);
    return this.chartPadding.left + (index * spacing);
  }

  getTimelineY(count: number): number {
    if (this.maxTimelineCount === 0) return this.chartPadding.top + this.chartHeight;
    const normalizedHeight = (count / this.maxTimelineCount) * this.chartHeight;
    return this.chartPadding.top + this.chartHeight - normalizedHeight;
  }

  getTimelinePoints(): string {
    if (this.timeline.length === 0) return '';
    return this.timeline.map((item, i) => {
      const x = this.getTimelineX(i);
      const y = this.getTimelineY(item.count);
      return `${x},${y}`;
    }).join(' ');
  }

  // Métodos para gráfico circular
  getPiePath(index: number): string {
    if (this.incidentsByType.length === 0 || index >= this.incidentsByType.length) return '';
    
    const total = this.incidentsByType.reduce((sum, item) => sum + item.count, 0);
    if (total === 0) return '';
    
    let currentAngle = 0;
    
    for (let i = 0; i < index; i++) {
      const angle = (this.incidentsByType[i].count / total) * 360;
      currentAngle += angle;
    }
    
    const angle = (this.incidentsByType[index].count / total) * 360;
    if (angle === 0) return '';
    
    const startAngle = currentAngle - 90; // Empezar desde arriba
    const endAngle = currentAngle + angle - 90;
    
    const startAngleRad = (startAngle * Math.PI) / 180;
    const endAngleRad = (endAngle * Math.PI) / 180;
    
    const x1 = this.pieChartCenterX + this.pieChartRadius * Math.cos(startAngleRad);
    const y1 = this.pieChartCenterY + this.pieChartRadius * Math.sin(startAngleRad);
    const x2 = this.pieChartCenterX + this.pieChartRadius * Math.cos(endAngleRad);
    const y2 = this.pieChartCenterY + this.pieChartRadius * Math.sin(endAngleRad);
    
    const largeArcFlag = angle > 180 ? 1 : 0;
    
    return `M ${this.pieChartCenterX} ${this.pieChartCenterY} L ${x1} ${y1} A ${this.pieChartRadius} ${this.pieChartRadius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;
  }

  getTypeColor(type: string): string {
    const colors: { [key: string]: string } = {
      'Hurto de Celular': '#ff6b35',
      'Hurto de Dinero': '#dc3545',
      'Hurto de Computador': '#2196F3',
      'Hurto de Accesorios': '#9C27B0',
      'Hurto de Documentos': '#00BCD4',
      'Hurto de Bicicleta': '#ffc107',
      'Hurto de Vehículo': '#ff9800',
      'Hurto a Persona': '#dc3545',
      'Robo': '#e91e63',
      'Otros': '#6c757d'
    };
    return colors[type] || '#6c757d';
  }

  getShortLabel(type: string): string {
    const shortLabels: { [key: string]: string } = {
      'Hurto de Celular': 'Celular',
      'Hurto de Dinero': 'Dinero',
      'Hurto de Computador': 'Computador',
      'Hurto de Accesorios': 'Accesorios',
      'Hurto de Documentos': 'Documentos',
      'Hurto de Bicicleta': 'Bicicleta',
      'Hurto de Vehículo': 'Vehículo',
      'Hurto a Persona': 'Persona',
      'Robo': 'Robo',
      'Otros': 'Otros'
    };
    return shortLabels[type] || type.substring(0, 10);
  }

  getDayShortLabel(day: string): string {
    return day.substring(0, 3);
  }

  ngAfterViewInit() {
    // Inicializar el mapa después de que la vista se haya renderizado
    // Usar un timeout más largo para asegurar que el DOM esté completamente listo
    setTimeout(() => {
      this.initializeHeatmap();
      // Si los datos ya están disponibles después de inicializar el mapa, crear el heatmap
      if (this.heatmapData && this.heatmapData.length > 0 && this.map) {
        this.createHeatmap(this.heatmapData);
      }
    }, 1000);
  }

  ngOnDestroy() {
    if (this.map) {
      this.map.remove();
    }
  }

  initializeHeatmap() {
    // Coordenadas del centro de Medellín, Colombia
    const medellinLat = 6.2476;
    const medellinLng = -75.5658;
    const defaultZoom = 12; // Zoom adecuado para ver toda la ciudad

    // Verificar que el elemento existe antes de inicializar
    const heatmapElement = document.getElementById('heatmap');
    if (!heatmapElement) {
      console.error('Elemento heatmap no encontrado');
      return;
    }

    console.log('Inicializando mapa de calor centrado en Medellín...');
    this.map = L.map('heatmap').setView([medellinLat, medellinLng], defaultZoom);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18
    }).addTo(this.map);

    // Si los datos ya están disponibles, crear el heatmap
    if (this.heatmapData && this.heatmapData.length > 0) {
      console.log('Datos disponibles, creando heatmap con', this.heatmapData.length, 'puntos');
      this.createHeatmap(this.heatmapData);
    } else {
      console.log('Esperando datos del heatmap...');
    }

    L.control.scale().addTo(this.map);
    console.log('Mapa inicializado correctamente en Medellín');
  }

  createHeatmap(data: HeatmapPoint[]) {
    if (!this.map) {
      console.warn('Mapa no inicializado, no se puede crear el heatmap');
      return;
    }

    if (!data || data.length === 0) {
      console.warn('No hay datos para el heatmap');
      return;
    }

    console.log('Creando heatmap con', data.length, 'puntos');

    if (this.heatmapLayer) {
      this.map.removeLayer(this.heatmapLayer);
    }

    this.heatmapLayer = L.layerGroup();

    data.forEach(point => {
      const color = this.getRiskColor(point.risk);
      const radius = point.intensity * 800;
      const opacity = Math.min(point.intensity + 0.2, 0.7);

      const circle = L.circle([point.lat, point.lng], {
        radius: radius,
        fillColor: color,
        color: color,
        weight: 1,
        opacity: opacity,
        fillOpacity: opacity * 0.6
      });

      circle.bindPopup(`
        <div class="heatmap-popup">
          <strong>Nivel de Riesgo: ${point.risk.toUpperCase()}</strong><br>
          Intensidad: ${(point.intensity * 100).toFixed(0)}%<br>
          Incidentes: ${point.count}<br>
          Lat: ${point.lat.toFixed(4)}<br>
          Lng: ${point.lng.toFixed(4)}
        </div>
      `);

      circle.addTo(this.heatmapLayer);
    });

    this.heatmapLayer.addTo(this.map);

    // Siempre mantener el centro en Medellín
    const medellinLat = 6.2476;
    const medellinLng = -75.5658;
    const defaultZoom = 12;
    this.map.setView([medellinLat, medellinLng], defaultZoom);
    
    console.log('Heatmap creado y mapa centrado en Medellín');
  }

  getRiskColor(risk: string): string {
    switch (risk) {
      case 'alto': return '#dc3545';
      case 'medio': return '#ffc107';
      case 'bajo': return '#28a745';
      default: return '#6c757d';
    }
  }

  openLogoutConfirmation() {
    this.showLogoutModal = true;
  }

  closeLogoutModal() {
    this.showLogoutModal = false;
  }

  confirmLogout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    sessionStorage.clear();
    this.closeLogoutModal();
    this.router.navigate(['/']);
  }

  onKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape' && this.showLogoutModal) {
      this.closeLogoutModal();
    }
  }
}

import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';

@Component({
  selector: 'app-statistics',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './statistics.component.html',
  styleUrls: ['./statistics.component.scss']
})
export class StatisticsComponent {
  stats = [
    { label: 'Alertas Activas', value: '12', trend: '+2' },
    { label: 'Incidentes Hoy', value: '8', trend: '-1' },
    { label: 'Usuarios Activos', value: '45', trend: '+5' },
    { label: 'Zonas Seguras', value: '15', trend: '+3' }
  ];

  showLogoutModal = false;

  constructor(private router: Router) {}


  openLogoutConfirmation() {
    this.showLogoutModal = true;
  }
  closeLogoutModal() {
    this.showLogoutModal = false;
  }

  confirmLogout() {
    console.log('Cerrando sesión desde estadísticas...');
    
    
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
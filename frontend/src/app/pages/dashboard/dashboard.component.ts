import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
  standalone: true,
  imports: [CommonModule, RouterModule]
})
export class DashboardComponent implements OnInit {
  currentTime: string = '';
  isQuickActionsOpen: boolean = false;
  showLogoutModal: boolean = false;

  constructor(private router: Router) {}

  ngOnInit() {
    this.updateTime();
    setInterval(() => this.updateTime(), 60000);
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

  // Abrir modal de confirmación
  openLogoutConfirmation() {
    this.showLogoutModal = true;
  }

  // Cerrar modal
  closeLogoutModal() {
    this.showLogoutModal = false;
  }

  // Confirmar cierre de sesión
  confirmLogout() {
    console.log('Cerrando sesión...');
    
    // Limpiar almacenamiento
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    sessionStorage.clear();
    
    // Cerrar modal
    this.closeLogoutModal();
    
    // Redirigir al login
    this.router.navigate(['/login']);
    
    // Opcional: Podrías agregar un toast de confirmación aquí
  }

  // Manejar tecla Escape para cerrar modal
  onKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape' && this.showLogoutModal) {
      this.closeLogoutModal();
    }
  }
}
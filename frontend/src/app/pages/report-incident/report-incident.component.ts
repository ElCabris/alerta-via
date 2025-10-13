import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-report-incident',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './report-incident.component.html',
  styleUrls: ['./report-incident.component.scss']
})
export class ReportIncidentComponent {
  incidentTypes = ['Robo', 'Accidente', 'Problema vial', 'Otro'];
  selectedType = '';
  showLogoutModal = false;

  constructor(private router: Router) {}
  
  onSubmit() {
    console.log('Incidente reportado:', this.selectedType);
  }
  openLogoutConfirmation() {
    this.showLogoutModal = true;
  }
  closeLogoutModal() {
    this.showLogoutModal = false;
  }
  confirmLogout() {
    console.log('Cerrando sesión desde reportar incidente...');
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
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
  location = '';
  description = '';
  showLogoutModal = false;

  constructor(private router: Router) {}
  
  onSubmit() {
    if (!this.selectedType) {
      alert('Por favor, selecciona un tipo de incidente');
      return;
    }
    
    const incidentData = {
      tipo: this.selectedType,
      ubicacion: this.location,
      descripcion: this.description,
      fecha: new Date().toISOString()
    };
    
    console.log('Incidente reportado:', incidentData);
    
    // TODO: Enviar al backend cuando esté disponible
    // Por ahora, guardar en localStorage como respaldo
    const incidents = JSON.parse(localStorage.getItem('incidents') || '[]');
    incidents.push(incidentData);
    localStorage.setItem('incidents', JSON.stringify(incidents));
    
    alert('Incidente reportado exitosamente');
    
    // Limpiar formulario
    this.selectedType = '';
    this.location = '';
    this.description = '';
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
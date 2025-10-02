import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
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
  
  onSubmit() {
    console.log('Incidente reportado:', this.selectedType);
    // Lógica para enviar el reporte back
  }
}
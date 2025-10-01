import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent {
  isEditing = false; // Agrega esta variable
  
  user = {
    name: 'Juan Pérez',
    email: 'juan.perez@example.com',
    phone: '+57 123 456 7890'
  };

  onSubmit() {
    // Tu lógica para guardar los cambios
    console.log('Perfil actualizado:', this.user);
    this.isEditing = false; // Vuelve al modo visualización después de guardar
  }
}
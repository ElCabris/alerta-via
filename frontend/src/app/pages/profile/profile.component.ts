import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent {
  isEditing = false;
  showLogoutModal = false;
  
  user = {
    name: 'Juan Pérez',
    email: 'juan.perez@example.com',
    phone: '+57 123 456 7890'
  };

  constructor(private router: Router) {}

  onSubmit() {
    console.log('Perfil actualizado:', this.user);
    this.isEditing = false; 
  }

  openLogoutConfirmation() {
    this.showLogoutModal = true;
  }

  closeLogoutModal() {
    this.showLogoutModal = false;
  }

  confirmLogout() {
    console.log('Cerrando sesión desde perfil...');
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
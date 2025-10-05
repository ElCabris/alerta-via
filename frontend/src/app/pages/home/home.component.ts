import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router } from '@angular/router';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule]
})
export class HomeComponent {
  email: string = '';
  password: string = '';
  isLoading: boolean = false;
  emailError: string = '';
  passwordError: string = '';

  constructor(private router: Router) {}

  // Validación para el correo
  isValidEmail(email: string): boolean {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(email);
  }

  validateForm(): boolean {
    this.emailError = '';
    this.passwordError = '';

    if (!this.email.trim()) {
      this.emailError = 'El correo electrónico es requerido';
      return false;
    }

    if (!this.isValidEmail(this.email)) {
      this.emailError = 'Por favor ingresa un correo electrónico válido';
      return false;
    }

    if (!this.password.trim()) {
      this.passwordError = 'La contraseña es requerida';
      return false;
    }

    if (this.password.length < 6) {
      this.passwordError = 'La contraseña debe tener al menos 6 caracteres';
      return false;
    }

    return true;
  }

  onSubmit() {
    if (!this.validateForm()) {
      return;
    }

    console.log('Email:', this.email);
    console.log('Password:', this.password);
    
    this.isLoading = true;
    // Simulación de verificación con backend
    setTimeout(() => {
      this.router.navigate(['/dashboard']);
    }, 1500);
  }

  onEmailInput() {
    if (this.emailError) {
      this.emailError = '';
    }
  }

  onPasswordInput() {
    if (this.passwordError) {
      this.passwordError = '';
    }
  }
}
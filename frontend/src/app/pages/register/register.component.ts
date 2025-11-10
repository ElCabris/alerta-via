import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router } from '@angular/router';

@Component({
  selector: 'app-register',
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss'],
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule]
})
export class RegisterComponent {
  fullName: string = '';
  email: string = '';
  password: string = '';
  confirmPassword: string = '';
  acceptTerms: boolean = false;
  isLoading: boolean = false;

  // Mensajes de error
  fullNameError: string = '';
  emailError: string = '';
  passwordError: string = '';
  confirmPasswordError: string = '';
  termsError: string = '';

  constructor(private router: Router) {}

  // Validación robusta de email
  isValidEmail(email: string): boolean {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(email);
  }

  validateForm(): boolean {
    this.fullNameError = '';
    this.emailError = '';
    this.passwordError = '';
    this.confirmPasswordError = '';
    this.termsError = '';

    // Validacion para poder registrar el usuario
    if (!this.fullName.trim()) {
      this.fullNameError = 'El nombre completo es requerido';
      return false;
    }

    if (this.fullName.trim().length < 2) {
      this.fullNameError = 'El nombre debe tener al menos 2 caracteres';
      return false;
    }

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

    if (!this.confirmPassword.trim()) {
      this.confirmPasswordError = 'Por favor confirma tu contraseña';
      return false;
    }

    if (this.password !== this.confirmPassword) {
      this.confirmPasswordError = 'Las contraseñas no coinciden';
      return false;
    }

    if (!this.acceptTerms) {
      this.termsError = 'Debes aceptar los términos y condiciones';
      return false;
    }

    return true;
  }

  onSubmit() {
    if (!this.validateForm()) {
      return;
    }

    console.log('Datos de registro:', {
      fullName: this.fullName,
      email: this.email,
      password: this.password,
      confirmPassword: this.confirmPassword,
      acceptTerms: this.acceptTerms
    });

    this.isLoading = true;

    setTimeout(() => {
      this.router.navigate(['/dashboard']);
    }, 1500);
  }

  onFullNameInput() {
    if (this.fullNameError) {
      this.fullNameError = '';
    }
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
    if (this.confirmPasswordError && this.password === this.confirmPassword) {
      this.confirmPasswordError = '';
    }
  }

  onConfirmPasswordInput() {
    if (this.confirmPasswordError) {
      this.confirmPasswordError = '';
    }
  }

  onTermsChange() {
    if (this.termsError) {
      this.termsError = '';
    }
  }
}
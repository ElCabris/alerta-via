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
  user = {
    name: 'Juan Pérez',
    email: 'juan@email.com',
    phone: '+57 300 123 4567'
  };
  
  onSubmit() {
    console.log('Perfil actualizado:', this.user);
  }
}
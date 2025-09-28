import { Routes } from '@angular/router';

export const routes: Routes = [
  { 
    path: '', 
    loadComponent: () => import('./pages/home/home.component').then(m => m.HomeComponent)
  },
  { 
    path: 'registro', 
    loadComponent: () => import('./pages/register/register.component').then(m => m.RegisterComponent)
  }
];
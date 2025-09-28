import { Routes } from '@angular/router';

export const routes: Routes = [
  { 
    path: '', 
    loadComponent: () => import('./pages/home/home.component').then(m => m.HomeComponent)
  },
  { 
    path: 'registro', 
    loadComponent: () => import('./pages/register/register.component').then(m => m.RegisterComponent)
  },
  { 
    path: 'terminos', 
    loadComponent: () => import('./pages/terms/terms.component').then(m => m.TermsComponent)
  },
  { 
    path: 'privacidad', 
    loadComponent: () => import('./pages/privacy/privacy.component').then(m => m.PrivacyComponent)
  }
];
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
  },
  { 
    path: 'dashboard', 
    loadComponent: () => import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent)
  },
  { 
    path: 'reportar-incidente', 
    loadComponent: () => import('./pages/report-incident/report-incident.component').then(m => m.ReportIncidentComponent)
  },
  { 
    path: 'estadisticas', 
    loadComponent: () => import('./pages/statistics/statistics.component').then(m => m.StatisticsComponent)
  },
  { 
    path: 'perfil', 
    loadComponent: () => import('./pages/profile/profile.component').then(m => m.ProfileComponent)
  },
  { 
    path: '**', 
    redirectTo: '' 
  }
];
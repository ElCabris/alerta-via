import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
  standalone: true,
  imports: [CommonModule, RouterModule]
})
export class DashboardComponent implements OnInit {
  currentTime: string = '';
  isQuickActionsOpen: boolean = false;

  ngOnInit() {
    this.updateTime();
    setInterval(() => this.updateTime(), 60000);
  }

  updateTime() {
    const now = new Date();
    this.currentTime = now.toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }

  toggleQuickActions() {
    this.isQuickActionsOpen = !this.isQuickActionsOpen;
  }
}
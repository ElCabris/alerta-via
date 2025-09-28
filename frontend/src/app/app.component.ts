import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router'; // ✅ Agrega esta importación

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
  standalone: true,
  imports: [RouterOutlet] // ✅ Agrega RouterOutlet aquí
})
export class AppComponent {
  year = new Date().getFullYear();
}
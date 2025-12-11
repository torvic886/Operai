import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, NavigationEnd, RouterModule } from '@angular/router';
import { filter } from 'rxjs/operators';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css']
})
export class SidebarComponent {
  currentView: 'asistente' | 'powerbi' | 'analisis' = 'asistente';

  constructor(private router: Router) {
    // Detectar cambios de ruta para actualizar vista activa
    this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe((event: any) => {
        const url = event.urlAfterRedirects || event.url;
        
        if (url.includes('powerbi')) {
          this.currentView = 'powerbi';
        } else if (url.includes('analisis')) {
          this.currentView = 'analisis';
        } else {
          this.currentView = 'asistente';
        }
      });
  }

  navigateTo(view: 'asistente' | 'powerbi' | 'analisis'): void {
    this.currentView = view;
    this.router.navigate([`/${view}`]);
    console.log(`📍 Navegando a: ${view}`);
  }

  openSettings(): void {
    console.log('⚙️ Abriendo configuración...');
    // Aquí puedes abrir un modal o navegar a una página de settings
    alert('Configuración próximamente');
  }
}
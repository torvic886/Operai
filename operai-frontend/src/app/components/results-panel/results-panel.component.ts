import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SafeResourceUrl } from '@angular/platform-browser';
import { GastosService } from '../../services/gastos.service';
import { PowerBIService } from '../../services/powerbi.service';
import { Gasto } from '../../models/gasto.model';

@Component({
  selector: 'app-results-panel',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './results-panel.component.html',
  styleUrls: ['./results-panel.component.css']
})
export class ResultsPanelComponent implements OnInit {
  gastos: Gasto[] = [];
  powerBiUrl: SafeResourceUrl;
  showFullscreen = false;
  isLoading = true;

  constructor(
    private gastosService: GastosService,
    private powerBiService: PowerBIService // ✅ INYECTAR EL SERVICIO
  ) {
    // ✅ USAR EL SERVICIO EN LUGAR DE HARDCODEAR
    this.powerBiUrl = this.powerBiService.getDashboardUrl();
  }

  ngOnInit(): void {
    this.gastosService.gastos$.subscribe(gastos => {
      this.gastos = gastos;
    });

    // ✅ SUSCRIBIRSE AL ESTADO DE CARGA
    this.powerBiService.loading$.subscribe(loading => {
      this.isLoading = loading;
    });
  }

  openFullscreen(): void {
    this.showFullscreen = true;
    document.body.style.overflow = 'hidden';
  }

  closeFullscreen(): void {
    this.showFullscreen = false;
    document.body.style.overflow = 'auto';
  }

  // ✅ NUEVO: Método para refrescar el dashboard
  refreshDashboard(): void {
    this.isLoading = true;
    this.powerBiUrl = this.powerBiService.getDashboardUrl();
  }
}
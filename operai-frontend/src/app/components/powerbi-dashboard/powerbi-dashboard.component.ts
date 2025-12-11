import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SafeResourceUrl } from '@angular/platform-browser';
import { PowerBIService } from '../../services/powerbi.service';
import { Subject, takeUntil } from 'rxjs';
import { ChangeDetectorRef } from '@angular/core';


@Component({
  selector: 'app-powerbi-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="powerbi-dashboard">
      <div class="dashboard-header">
        <div class="header-content">
          <div class="header-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"></rect>
              <rect x="14" y="3" width="7" height="7"></rect>
              <rect x="14" y="14" width="7" height="7"></rect>
              <rect x="3" y="14" width="7" height="7"></rect>
            </svg>
          </div>
          <div>
            <h2 class="dashboard-title">Dashboard de Visualización - Power BI</h2>
            <p class="dashboard-subtitle">Análisis en tiempo real de gastos operativos</p>
          </div>
        </div>
        
        <div class="header-actions">
          <button class="btn-action" (click)="refreshDashboard()" title="Actualizar">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 4 23 10 17 10"></polyline>
              <polyline points="1 20 1 14 7 14"></polyline>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
            </svg>
          </button>
          <button class="btn-primary" (click)="toggleFullscreen()" title="Pantalla completa">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
            </svg>
            Pantalla completa
          </button>
        </div>
      </div>

      <div class="dashboard-container" [class.fullscreen]="isFullscreen">
        <!-- Loading State -->
        <div class="loading-overlay" *ngIf="isLoading">
          <div class="spinner"></div>
          <p>Cargando dashboard...</p>
        </div>

        <!-- Error State -->
        <div class="error-state" *ngIf="error && !isLoading">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          <h3>Error al cargar el dashboard</h3>
          <p>{{ error }}</p>
          <button class="btn-retry" (click)="refreshDashboard()">Reintentar</button>
        </div>

        <!-- Power BI Iframe -->
        <iframe 
          *ngIf="!error"
          [src]="powerBiUrl" 
          frameborder="0" 
          allowFullScreen="true"
          class="powerbi-iframe"
          (load)="onIframeLoad()"
          (error)="onIframeError()">
        </iframe>

        <!-- Fullscreen Close Button -->
        <button class="btn-close-fullscreen" *ngIf="isFullscreen" (click)="toggleFullscreen()">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
    </div>
  `,
  styles: [`
    .powerbi-dashboard {
      height: 100%;
      display: flex;
      flex-direction: column;
      background: white;
      border-radius: 12px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      overflow: hidden;
    }

    .dashboard-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 20px 24px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }

    .header-content {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .header-icon {
      width: 48px;
      height: 48px;
      background: rgba(255,255,255,0.2);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      backdrop-filter: blur(10px);
    }

    .dashboard-title {
      margin: 0;
      font-size: 1.5rem;
      font-weight: 700;
    }

    .dashboard-subtitle {
      margin: 4px 0 0 0;
      font-size: 0.875rem;
      opacity: 0.9;
    }

    .header-actions {
      display: flex;
      gap: 12px;
    }

    .btn-action, .btn-primary {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 18px;
      border: none;
      border-radius: 8px;
      font-size: 0.875rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .btn-action {
      background: rgba(255,255,255,0.2);
      color: white;
      backdrop-filter: blur(10px);
    }

    .btn-action:hover {
      background: rgba(255,255,255,0.3);
      transform: scale(1.05);
    }

    .btn-primary {
      background: white;
      color: #667eea;
    }

    .btn-primary:hover {
      background: #f0f0f0;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .dashboard-container {
      flex: 1;
      position: relative;
      background: #f5f5f5;
      min-height: 600px;
    }

    .dashboard-container.fullscreen {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 9999;
      border-radius: 0;
      min-height: 100vh;
    }

    .powerbi-iframe {
      width: 100%;
      height: 100%;
      border: none;
    }

    .loading-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(255,255,255,0.95);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 16px;
      z-index: 10;
    }

    .spinner {
      width: 48px;
      height: 48px;
      border: 4px solid #e5e7eb;
      border-top-color: #667eea;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .error-state {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      text-align: center;
      padding: 40px;
      background: white;
      border-radius: 12px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    .error-state svg {
      color: #ef4444;
      margin-bottom: 16px;
    }

    .error-state h3 {
      margin: 0 0 8px 0;
      color: #1f2937;
      font-size: 1.25rem;
    }

    .error-state p {
      margin: 0 0 20px 0;
      color: #6b7280;
    }

    .btn-retry {
      padding: 10px 24px;
      background: #667eea;
      color: white;
      border: none;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }

    .btn-retry:hover {
      background: #5568d3;
      transform: translateY(-2px);
    }

    .btn-close-fullscreen {
      position: fixed;
      top: 24px;
      right: 24px;
      width: 48px;
      height: 48px;
      background: rgba(0,0,0,0.8);
      color: white;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10000;
      transition: all 0.2s;
      backdrop-filter: blur(10px);
    }

    .btn-close-fullscreen:hover {
      background: rgba(0,0,0,0.9);
      transform: scale(1.1);
    }

    @media (max-width: 768px) {
      .dashboard-header {
        flex-direction: column;
        gap: 16px;
        align-items: flex-start;
      }

      .header-actions {
        width: 100%;
      }

      .btn-primary {
        flex: 1;
      }

      .dashboard-subtitle {
        display: none;
      }
    }
  `]
})
export class PowerBIDashboardComponent implements OnInit, OnDestroy {
  powerBiUrl: SafeResourceUrl;
  isLoading = true;
  error: string | null = null;
  isFullscreen = false;
  private destroy$ = new Subject<void>();

  constructor(private powerBiService: PowerBIService, private cd: ChangeDetectorRef) {
    this.powerBiUrl = this.powerBiService.getDashboardUrl();
  }

  ngOnInit(): void {
    this.powerBiService.loading$
      .pipe(takeUntil(this.destroy$))
      .subscribe(loading => this.isLoading = loading);

    this.powerBiService.error$
      .pipe(takeUntil(this.destroy$))
      .subscribe(error => this.error = error);

    if (!this.powerBiService.isConfigured()) {
      this.error = 'Power BI no está configurado correctamente. Verifica las variables de entorno.';
      this.isLoading = false;
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onIframeLoad(): void {
    console.log('✅ Power BI Dashboard cargado exitosamente');
    this.powerBiService.setLoading(false);
    this.powerBiService.setError(null);
    this.cd.detectChanges();
  }

  onIframeError(): void {
    console.error('❌ Error al cargar Power BI Dashboard');
    this.powerBiService.setError('No se pudo cargar el dashboard. Verifica la URL de Power BI.');
    this.powerBiService.setLoading(false);
  }

  refreshDashboard(): void {
    console.log('🔄 Refrescando dashboard...');
    this.isLoading = true;
    this.error = null;
    this.powerBiUrl = this.powerBiService.getDashboardUrl();
  }

  toggleFullscreen(): void {
    this.isFullscreen = !this.isFullscreen;
    
    if (this.isFullscreen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }
  }
}
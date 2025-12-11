import { Routes } from '@angular/router';
import { PowerBIDashboardComponent } from './components/powerbi-dashboard/powerbi-dashboard.component';
import { ChatPanelComponent } from './components/chat-panel/chat-panel.component';

// Crear componente para Análisis Interactivo
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-analisis-interactivo',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="analisis-container">
      <h2>📈 Análisis Interactivo (Streamlit)</h2>
      <p>Dashboard de análisis en tiempo real</p>
      
      <iframe 
        src="http://localhost:8501" 
        frameborder="0"
        class="streamlit-iframe"
        title="Dashboard Streamlit">
      </iframe>
    </div>
  `,
  styles: [`
    .analisis-container {
      height: 100%;
      display: flex;
      flex-direction: column;
      padding: 24px;
      background: #1e1e2e;
      color: white;
    }

    h2 {
      margin: 0 0 8px 0;
      font-size: 1.5rem;
    }

    p {
      margin: 0 0 24px 0;
      opacity: 0.7;
    }

    .streamlit-iframe {
      flex: 1;
      width: 100%;
      min-height: 600px;
      border-radius: 12px;
      background: white;
    }
  `]
})
export class AnalisisInteractivoComponent {}

// Vista Principal con Chat + Métricas
@Component({
  selector: 'app-asistente-ia',
  standalone: true,
  imports: [CommonModule, ChatPanelComponent],
  template: `
    <div class="asistente-container">
      <!-- Métricas destacadas -->
      <div class="metricas-grid">
        <div class="metrica-card">
          <div class="metrica-icon">📦</div>
          <div class="metrica-content">
            <h3>Total Registros</h3>
            <p class="metrica-valor">3,036</p>
          </div>
        </div>
        
        <div class="metrica-card">
          <div class="metrica-icon">💰</div>
          <div class="metrica-content">
            <h3>Monto Total</h3>
            <p class="metrica-valor">$959,317,860.89</p>
          </div>
        </div>
        
        <div class="metrica-card">
          <div class="metrica-icon">📊</div>
          <div class="metrica-content">
            <h3>Promedio</h3>
            <p class="metrica-valor">$315,980.85</p>
          </div>
        </div>
        
        <div class="metrica-card">
          <div class="metrica-icon">🏷️</div>
          <div class="metrica-content">
            <h3>Categorías</h3>
            <p class="metrica-valor">11</p>
          </div>
        </div>
      </div>

      <!-- Chat Panel -->
      <div class="chat-section">
        <app-chat-panel></app-chat-panel>
      </div>
    </div>
  `,
  styles: [`
    .asistente-container {
      height: 100%;
      display: flex;
      flex-direction: column;
      gap: 24px;
      padding: 24px;
      background: #1e1e2e;
      overflow-y: auto;
    }

    .metricas-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px;
    }

    .metrica-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 16px;
      padding: 24px;
      display: flex;
      align-items: center;
      gap: 16px;
      box-shadow: 0 8px 16px rgba(0,0,0,0.3);
      transition: transform 0.3s ease;
    }

    .metrica-card:hover {
      transform: translateY(-4px);
    }

    .metrica-icon {
      font-size: 2.5rem;
      background: rgba(255,255,255,0.2);
      width: 64px;
      height: 64px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .metrica-content {
      flex: 1;
    }

    .metrica-content h3 {
      margin: 0;
      font-size: 0.875rem;
      color: rgba(255,255,255,0.8);
      font-weight: 500;
    }

    .metrica-valor {
      margin: 4px 0 0 0;
      font-size: 1.75rem;
      font-weight: 700;
      color: white;
    }

    .chat-section {
      flex: 1;
      min-height: 500px;
    }

    @media (max-width: 1200px) {
      .metricas-grid {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    @media (max-width: 768px) {
      .metricas-grid {
        grid-template-columns: 1fr;
      }
    }
  `]
})
export class AsistenteIAComponent {}

export const routes: Routes = [
  {
    path: 'asistente',
    component: AsistenteIAComponent,
    title: '🤖 Asistente IA'
  },
  {
    path: 'powerbi',
    component: PowerBIDashboardComponent,
    title: '📊 Power BI'
  },
  {
    path: 'analisis',
    component: AnalisisInteractivoComponent,
    title: '📈 Análisis Interactivo'
  },
  {
    path: '',
    redirectTo: '/asistente',
    pathMatch: 'full'
  }
];
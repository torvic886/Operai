import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from './components/sidebar/sidebar.component';
import { UploadPanelComponent } from './components/upload-panel/upload-panel.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    SidebarComponent,
    UploadPanelComponent
  ],
  template: `
    <div class="app-container">
      <!-- Header -->
      <header class="app-header">
        <div class="header-left">
          <svg class="logo-icon" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7"></rect>
            <rect x="14" y="3" width="7" height="7"></rect>
            <rect x="14" y="14" width="7" height="7"></rect>
            <rect x="3" y="14" width="7" height="7"></rect>
          </svg>
          <h1 class="app-title">OperAI - Gasto Operativo Casino</h1>
        </div>
        
        <div class="header-right">
          <button class="header-btn btn-upload" (click)="showUploadPanel = !showUploadPanel">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            Cargar Datos
          </button>
          
          <div class="user-info">
            <div class="user-avatar">U</div>
            <span class="user-name">Usuario</span>
          </div>
        </div>
      </header>

      <!-- Layout: Sidebar + Content -->
      <div class="app-content">
        <app-sidebar></app-sidebar>
        
        <main class="main-content">
          <!-- Panel de carga (overlay) -->
          <div class="upload-overlay" *ngIf="showUploadPanel" (click)="showUploadPanel = false">
            <div class="upload-modal" (click)="$event.stopPropagation()">
              <button class="close-modal" (click)="showUploadPanel = false">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
              <app-upload-panel></app-upload-panel>
            </div>
          </div>
          
          <router-outlet></router-outlet>
        </main>
      </div>
    </div>
  `,
  styles: [`
    .app-container {
      min-height: 100vh;
      background-color: #0f172a;
      display: flex;
      flex-direction: column;
    }

    .app-header {
      background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
      color: white;
      padding: 16px 32px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      z-index: 100;
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .logo-icon {
      color: #667eea;
    }

    .app-title {
      font-size: 1.5rem;
      font-weight: 700;
      margin: 0;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .header-btn {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 20px;
      border: none;
      border-radius: 10px;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .btn-upload {
      background: rgba(255, 255, 255, 0.1);
      color: white;
      border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .btn-upload:hover {
      background: rgba(255, 255, 255, 0.15);
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

    .user-info {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 8px 16px;
      background: rgba(255,255,255,0.1);
      border-radius: 24px;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .user-info:hover {
      background: rgba(255,255,255,0.15);
    }

    .user-avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 0.875rem;
    }

    .user-name {
      font-size: 0.875rem;
      font-weight: 600;
    }

    .app-content {
      flex: 1;
      display: flex;
      height: calc(100vh - 68px);
      overflow: hidden;
    }

    .main-content {
      flex: 1;
      overflow-y: auto;
      background: #0f172a;
      position: relative;
      display: flex;
      flex-direction: column;
    }
    
    /* Fix para que router-outlet ocupe toda la altura */
    ::ng-deep router-outlet + * {
      display: flex;
      flex-direction: column;
      flex: 1;
      height: 100%;
    }
    
    /* Ajuste para sidebar en mobile */
    @media (max-width: 768px) {
      .app-content {
        flex-direction: column;
        height: calc(100vh - 140px);
      }
      
      .main-content {
        padding-bottom: 80px;
      }
    }

    .upload-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.75);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      backdrop-filter: blur(4px);
      animation: fadeIn 0.2s ease;
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    .upload-modal {
      background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
      border: 1px solid rgba(102, 126, 234, 0.3);
      border-radius: 20px;
      max-width: 900px;
      width: 90%;
      max-height: 85vh;
      overflow-y: auto;
      position: relative;
      animation: slideUp 0.3s ease;
      box-shadow: 0 25px 80px rgba(0, 0, 0, 0.6);
      padding: 32px;
    }

    .upload-modal::-webkit-scrollbar {
      width: 8px;
    }

    .upload-modal::-webkit-scrollbar-track {
      background: rgba(15, 23, 42, 0.3);
      border-radius: 4px;
    }

    .upload-modal::-webkit-scrollbar-thumb {
      background: rgba(102, 126, 234, 0.4);
      border-radius: 4px;
    }

    @keyframes slideUp {
      from {
        opacity: 0;
        transform: translateY(50px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .close-modal {
      position: fixed;
      top: 16px;
      right: 16px;
      background: rgba(239, 68, 68, 0.9);
      border: 2px solid rgba(255, 255, 255, 0.2);
      border-radius: 50%;
      width: 48px;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: white;
      transition: all 0.3s ease;
      z-index: 1001;
      box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
    }

    .close-modal:hover {
      background: rgba(239, 68, 68, 1);
      transform: rotate(90deg) scale(1.1);
      box-shadow: 0 6px 20px rgba(239, 68, 68, 0.6);
    }

    .close-modal svg {
      stroke-width: 3;
    }

    @media (max-width: 768px) {
      .app-header {
        padding: 12px 16px;
      }

      .app-title {
        font-size: 1rem;
      }

      .user-name {
        display: none;
      }

      .app-content {
        flex-direction: column-reverse;
      }
    }
  `]
})
export class AppComponent {
  title = 'OperAI Dashboard';
  showUploadPanel = false;
}
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SidebarComponent } from './components/sidebar/sidebar.component';
import { ChatPanelComponent } from './components/chat-panel/chat-panel.component';
import { ResultsPanelComponent } from './components/results-panel/results-panel.component';
import { UploadPanelComponent } from './components/upload-panel/upload-panel.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    SidebarComponent,
    ChatPanelComponent,
    ResultsPanelComponent,
    UploadPanelComponent
  ],
  template: `
    <div class="app-container">
      <header class="app-header">
        <svg class="menu-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="3" y1="12" x2="21" y2="12"></line>
          <line x1="3" y1="6" x2="21" y2="6"></line>
          <line x1="3" y1="18" x2="21" y2="18"></line>
        </svg>
        <h1 class="app-title">OperAI - Gasto Operativo Casino</h1>
        
        <div class="header-actions">
          <button class="header-btn" (click)="toggleView('upload')" [class.active]="currentView === 'upload'">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            Cargar Datos
          </button>
          <button class="header-btn" (click)="toggleView('dashboard')" [class.active]="currentView === 'dashboard'">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"></rect>
              <rect x="14" y="3" width="7" height="7"></rect>
              <rect x="14" y="14" width="7" height="7"></rect>
              <rect x="3" y="14" width="7" height="7"></rect>
            </svg>
            Dashboard
          </button>
        </div>
      </header>

      <div class="app-content">
        <app-sidebar (sectionChange)="onSectionChange($event)"></app-sidebar>
        
        <main class="main-content" *ngIf="currentView === 'dashboard'">
          <app-chat-panel></app-chat-panel>
          <app-results-panel></app-results-panel>
        </main>

        <main class="main-content-full" *ngIf="currentView === 'upload'">
          <app-upload-panel></app-upload-panel>
        </main>
      </div>
    </div>
  `,
  styles: [`
    .app-container {
      min-height: 100vh;
      background-color: #f3f4f6;
      display: flex;
      flex-direction: column;
    }

    .app-header {
      background-color: #1f2937;
      color: white;
      padding: 16px 24px;
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .menu-icon {
      cursor: pointer;
    }

    .app-title {
      font-size: 1.25rem;
      font-weight: 600;
      margin: 0;
      flex: 1;
    }

    .header-actions {
      display: flex;
      gap: 12px;
    }

    .header-btn {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      background-color: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 6px;
      color: white;
      cursor: pointer;
      transition: all 0.2s;
      font-size: 0.875rem;
    }

    .header-btn:hover {
      background-color: rgba(255, 255, 255, 0.2);
    }

    .header-btn.active {
      background-color: #14b8a6;
      border-color: #14b8a6;
    }

    .app-content {
      flex: 1;
      display: flex;
      height: calc(100vh - 64px);
    }

    .main-content {
      flex: 1;
      padding: 24px;
      display: grid;
      grid-template-columns: 1fr 1.5fr;
      gap: 24px;
      overflow: hidden;
    }

    .main-content-full {
      flex: 1;
      padding: 24px;
      overflow: auto;
    }

    @media (max-width: 1400px) {
      .main-content {
        grid-template-columns: 1fr 1fr;
      }
    }

    @media (max-width: 1024px) {
      .main-content {
        grid-template-columns: 1fr;
        overflow-y: auto;
      }
    }
  `]
})
export class AppComponent {
  activeSection = 'chat';
  currentView: 'dashboard' | 'upload' = 'dashboard';

  onSectionChange(section: string): void {
    this.activeSection = section;
    console.log('Section changed to:', section);
  }

  toggleView(view: 'dashboard' | 'upload'): void {
    this.currentView = view;
  }
}	
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpService } from '../../services/http.service';

@Component({
  selector: 'app-upload-panel',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './upload-panel.component.html',
  styleUrls: ['./upload-panel.component.css']
})
export class UploadPanelComponent {
  selectedFile: File | null = null;
  isDragging = false;
  isUploading = false;
  isImporting = false;
  isExporting = false;
  
  importSheetUrl = '';
  importSheetName = '';
  
  exportSheetUrl = '';
  exportSheetName = '';
  lastExportInfo: { rows: number, date: Date } | null = null;
  
  stats: any = null;
  notification: { type: 'success' | 'error', message: string } | null = null;

  constructor(private httpService: HttpService) {
    this.loadStats();
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = false;
    
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.selectedFile = files[0];
    }
  }

  onFileSelected(event: any): void {
    const files = event.target.files;
    if (files && files.length > 0) {
      this.selectedFile = files[0];
    }
  }

  removeFile(): void {
    this.selectedFile = null;
  }

  uploadFile(): void {
    if (!this.selectedFile) return;

    this.isUploading = true;
    const formData = new FormData();
    formData.append('file', this.selectedFile);

    this.httpService.uploadFile('/upload/csv', formData).subscribe({
      next: (response: any) => {
        this.isUploading = false;
        this.selectedFile = null;
        
        // ✅ MENSAJE MEJORADO
        const rows = response.rows_processed || 0;
        const filename = response.filename || 'archivo';
        
        this.showNotification(
          'success', 
          `${rows} ${rows === 1 ? 'registro cargado' : 'registros cargados'} desde "${filename}"`
        );
        
        this.loadStats();
      },
      error: (error) => {
        this.isUploading = false;
        
        // ✅ MANEJO DE ERRORES MEJORADO
        let errorMsg = 'No se pudo cargar el archivo. Verifica el formato.';
        
        if (error.status === 0) {
          errorMsg = 'No se pudo conectar con el servidor. Verifica tu conexión.';
        } else if (error.error?.detail) {
          errorMsg = error.error.detail;
        } else if (error.message) {
          errorMsg = error.message;
        }
        
        this.showNotification('error', errorMsg);
      }
    });
  }

  importFromGoogleSheets(): void {
    if (!this.importSheetUrl) return;

    this.isImporting = true;
    this.httpService.post('/sync/google-sheets', {
      sheet_url: this.importSheetUrl,
      sheet_name: this.importSheetName || null
    }).subscribe({
      next: (response: any) => {
        this.isImporting = false;
        this.importSheetUrl = '';
        this.importSheetName = '';
        
        // ✅ MENSAJE MEJORADO
        const rows = response.rows_processed || 0;
        this.showNotification(
          'success', 
          `${rows} ${rows === 1 ? 'registro importado' : 'registros importados'} desde Google Sheets`
        );
        
        this.loadStats();
      },
      error: (error) => {
        this.isImporting = false;
        this.showNotification('error', error.error?.detail || 'Error al importar desde Google Sheets');
      }
    });
  }

  exportToGoogleSheets(): void {
    if (!this.exportSheetUrl) return;

    this.isExporting = true;
    this.httpService.post('/sync/export-to-sheets', {
      sheet_url: this.exportSheetUrl,
      sheet_name: this.exportSheetName || null
    }).subscribe({
      next: (response: any) => {
        this.isExporting = false;
        this.lastExportInfo = {
          rows: response.rows_exported,
          date: new Date()
        };
        
        // ✅ MENSAJE MEJORADO
        const rows = response.rows_exported || 0;
        this.showNotification(
          'success', 
          `${rows} ${rows === 1 ? 'registro exportado' : 'registros exportados'} a Google Sheets`
        );
      },
      error: (error) => {
        this.isExporting = false;
        this.showNotification('error', error.error?.detail || 'Error al exportar a Google Sheets');
      }
    });
  }

  loadStats(): void {
    this.httpService.get<any>('/upload/stats').subscribe({
      next: (response) => {
        this.stats = response;
      },
      error: (error) => {
        console.error('❌ Error cargando estadísticas:', error);
      }
    });
  }

  showNotification(type: 'success' | 'error', message: string): void {
    this.notification = { type, message };
    setTimeout(() => {
      this.notification = null;
    }, 5000);
  }
}
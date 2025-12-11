// =====================================================================
// 1. SERVICIO POWER BI - src/app/services/powerbi.service.ts
// =====================================================================
import { Injectable } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { BehaviorSubject, Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface PowerBIConfig {
  reportId: string;
  embedUrl: string;
  accessToken?: string;
  groupId?: string;
}

@Injectable({
  providedIn: 'root'
})
export class PowerBIService {
  private loadingSubject = new BehaviorSubject<boolean>(true);
  private errorSubject = new BehaviorSubject<string | null>(null);

  loading$ = this.loadingSubject.asObservable();
  error$ = this.errorSubject.asObservable();

  constructor(private sanitizer: DomSanitizer) {
    console.log('🔧 PowerBI Service inicializado');
  }

  /**
   * Obtiene la URL sanitizada del dashboard de Power BI
   */
  getDashboardUrl(): SafeResourceUrl {
    const url = environment.powerBiEmbedUrl;
    console.log('📊 Cargando Power BI Dashboard:', url);
    return this.sanitizer.bypassSecurityTrustResourceUrl(url);
  }

  /**
   * Construye una URL personalizada de Power BI
   */
  buildEmbedUrl(config: PowerBIConfig): SafeResourceUrl {
    let url = `https://app.powerbi.com/reportEmbed?reportId=${config.reportId}`;
    
    if (config.groupId) {
      url += `&groupId=${config.groupId}`;
    }
    
    url += '&autoAuth=true&ctid=d3eb04d5-5d9f-4e83-ae9e-51d614d1e8cf';
    
    console.log('🔗 URL de Power BI construida:', url);
    return this.sanitizer.bypassSecurityTrustResourceUrl(url);
  }

  /**
   * Maneja el estado de carga del iframe
   */
  setLoading(isLoading: boolean): void {
    this.loadingSubject.next(isLoading);
  }

  /**
   * Maneja errores de carga
   */
  setError(error: string | null): void {
    this.errorSubject.next(error);
  }

  /**
   * Verifica si el Power BI está configurado
   */
  isConfigured(): boolean {
    return !!environment.powerBiEmbedUrl && environment.powerBiEmbedUrl !== '';
  }
}
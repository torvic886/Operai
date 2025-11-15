import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment.development';

@Injectable({
  providedIn: 'root'
})
export class HttpService {
  private apiUrl = environment.apiUrl;
  private chatUrl = environment.chatEndpoint;

  constructor(private http: HttpClient) {
    console.log('🔧 API URL configurada:', this.apiUrl);
    console.log('🔧 Chat URL configurada:', this.chatUrl);
  }

  get<T>(endpoint: string, params?: any): Observable<T> {
    const url = `${this.apiUrl}${endpoint}`;
    console.log('📡 GET Request:', url, params);
    return this.http.get<T>(url, { params });
  }

  post<T>(endpoint: string, data: any): Observable<T> {
    const headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    const url = `${this.apiUrl}${endpoint}`;
    console.log('📡 POST Request:', url, data);
    return this.http.post<T>(url, data, { headers });
  }

  sendChatMessage(message: string): Observable<any> {
    console.log('💬 Enviando mensaje al chat:', this.chatUrl);
    return this.http.post<any>(this.chatUrl, { message });
  }

  uploadFile(endpoint: string, formData: FormData): Observable<any> {
    const url = `${this.apiUrl}${endpoint}`;
    console.log('📤 Subiendo archivo:', url);
    return this.http.post<any>(url, formData);
  }
}
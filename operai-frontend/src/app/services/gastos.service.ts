import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, forkJoin } from 'rxjs';
import { Gasto, Message } from '../models/gasto.model';
import { HttpService } from './http.service';
import { catchError, map } from 'rxjs/operators';
import { of } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class GastosService {
  private gastosSubject = new BehaviorSubject<Gasto[]>([]);
  private messagesSubject = new BehaviorSubject<Message[]>([
    {
      type: 'ai',
      text: 'Hola, soy OperAI. ¿En qué puedo ayudarte con los gastos del casino?',
      timestamp: new Date()
    }
  ]);

  gastos$: Observable<Gasto[]> = this.gastosSubject.asObservable();
  messages$: Observable<Message[]> = this.messagesSubject.asObservable();

  private categorias: string[] = [];
  private initialMessage: Message = {
    type: 'ai',
    text: 'Hola, soy OperAI. ¿En qué puedo ayudarte con los gastos del casino?',
    timestamp: new Date()
  };

  constructor(private httpService: HttpService) {
    this.loadCategoriasYGastos();
  }

  loadCategoriasYGastos(): void {
    console.log('🔄 Cargando categorías desde el backend...');

    this.httpService.get<any>('/tools/categorias').subscribe({
      next: (response) => {
        this.categorias = response.categorias || [];
        console.log('📂 Categorías disponibles:', this.categorias);

        if (this.categorias.length > 0) {
          this.loadGastos();
        } else {
          console.warn('⚠️ No hay categorías disponibles');
        }
      },
      error: (err) => {
        console.error('❌ Error al cargar categorías:', err);
        this.categorias = ['BONO CLIENTE', 'MANTENIMIENTO', 'SALARIOS', 'UTILIDADES'];
        this.loadGastos();
      }
    });
  }

  loadGastos(): void {
    console.log('🔄 Cargando gastos desde el backend...');

    const fechaFin = new Date().toISOString().split('T')[0];
    const fechaInicio = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
      .toISOString()
      .split('T')[0];

    const categoriasParaMostrar = this.categorias.slice(0, 4);

    const requests = categoriasParaMostrar.map(cat =>
      this.httpService.get<any>('/tools/total_categoria_valor', {
        categoria: cat,
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin
      }).pipe(
        map(data => ({
          categoria: cat,
          servicios: data?.monto_total || 0,
          monto: data?.monto_total || 0,
          success: true
        })),
        catchError(err => {
          console.error(`❌ Error al cargar ${cat}:`, err);
          return of({
            categoria: cat,
            servicios: 0,
            monto: 0,
            success: false
          });
        })
      )
    );

    forkJoin(requests).subscribe({
      next: (results) => {
        const gastosValidos = results.filter(r => r.success);
        console.log('✅ Gastos cargados:', gastosValidos);

        if (gastosValidos.length > 0) {
          this.gastosSubject.next(gastosValidos);
        } else {
          console.warn('⚠️ No hay datos válidos');
          this.gastosSubject.next([]);
        }
      },
      error: (err) => {
        console.error('❌ Error general:', err);
        this.gastosSubject.next([]);
      }
    });
  }

  addMessage(message: Message): void {
    console.log('📤 Enviando mensaje:', message.text);

    const currentMessages = this.messagesSubject.value;
    this.messagesSubject.next([...currentMessages, message]);

    this.httpService.sendChatMessage(message.text).subscribe({
      next: (response) => {
        console.log('📥 Respuesta del chat:', response);

        const aiMessage: Message = {
          type: 'ai',
          text: response.reply || 'No pude procesar tu solicitud.',
          timestamp: new Date()
        };
        const updatedMessages = this.messagesSubject.value;
        this.messagesSubject.next([...updatedMessages, aiMessage]);

        if (response.data) {
          this.loadGastos();
        }
      },
      error: (err) => {
        console.error('❌ Error al comunicarse con el chat:', err);
        const errorMessage: Message = {
          type: 'ai',
          text: 'Lo siento, hubo un error. Verifica que el backend esté corriendo en http://localhost:8000',
          timestamp: new Date()
        };
        const updatedMessages = this.messagesSubject.value;
        this.messagesSubject.next([...updatedMessages, errorMessage]);
      }
    });
  }

  clearMessages(): void {
    console.log('🗑️ Limpiando conversación...');
    // Reiniciar con el mensaje inicial
    this.messagesSubject.next([{ ...this.initialMessage, timestamp: new Date() }]);
  }

  getGastos(): Gasto[] {
    return this.gastosSubject.value;
  }
}
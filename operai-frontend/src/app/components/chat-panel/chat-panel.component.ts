import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { GastosService } from '../../services/gastos.service';
import { Message } from '../../models/gasto.model';

@Component({
  selector: 'app-chat-panel',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat-panel.component.html',
  styleUrls: ['./chat-panel.component.css']
})
export class ChatPanelComponent implements OnInit {
  messages: Message[] = [];
  inputText = '';
  showClearConfirm = false;
  showNotification = false;
  notificationMessage = '';
  showExamples = false;
  lastUserMessage = '';

  exampleQuestions = [
    '¿Cuánto gastamos en BONO CLIENTE en octubre 2025?',
    '¿Cuál es el promedio de gastos para la categoría CAFETERIA entre 2025-01-01 y 2025-10-31?',
    '¿¿Cuál es el presupuesto restante para la categoría ADMINISTRATIVOS para el periodo 2025-10??',
    'Dame los productos más caros de Cafetería entre 2025-01-01 y 2025-01-31',
    'Total de gastos en ASEO de enero de 2025'
  ];

  constructor(private gastosService: GastosService) {}

  ngOnInit(): void {
    this.gastosService.messages$.subscribe(messages => {
      this.messages = messages;
    });
  }

  sendMessage(): void {
    if (this.inputText.trim()) {
      this.lastUserMessage = this.inputText;
      this.gastosService.addMessage({
        type: 'user',
        text: this.inputText,
        timestamp: new Date()
      });
      this.inputText = '';
      this.showExamples = false;
    }
  }

  toggleExamples(): void {
    this.showExamples = !this.showExamples;
  }

  useExample(example: string): void {
    this.inputText = example;
    this.showExamples = false;
  }

  regenerateLastMessage(): void {
    if (this.lastUserMessage) {
      this.gastosService.addMessage({
        type: 'user',
        text: this.lastUserMessage,
        timestamp: new Date()
      });
      this.showNotificationMessage('Regenerando respuesta...');
    }
  }

  exportChat(): void {
    const chatContent = this.messages.map(msg => {
      const time = new Date(msg.timestamp).toLocaleString('es-ES');
      const sender = msg.type === 'ai' ? 'OperAI' : 'Usuario';
      return `[${time}] ${sender}: ${msg.text}`;
    }).join('\n\n');

    const blob = new Blob([chatContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `chat-operai-${new Date().toISOString().split('T')[0]}.txt`;
    link.click();
    URL.revokeObjectURL(url);

    this.showNotificationMessage('Chat exportado exitosamente');
  }

  confirmClearChat(): void {
    this.showClearConfirm = true;
  }

  cancelClear(): void {
    this.showClearConfirm = false;
  }

  clearChat(): void {
    this.gastosService.clearMessages();
    this.showClearConfirm = false;
    this.lastUserMessage = '';
    this.showNotificationMessage('Conversación limpiada exitosamente');
  }

  showNotificationMessage(message: string): void {
    this.notificationMessage = message;
    this.showNotification = true;
    setTimeout(() => {
      this.showNotification = false;
    }, 3000);
  }
}
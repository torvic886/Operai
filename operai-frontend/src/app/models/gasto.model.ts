export interface Gasto {
  categoria: string;
  servicios: number;
  monto: number;
}

export interface Message {
  type: 'ai' | 'user';
  text: string;
  timestamp: Date;
}

export interface ChartData {
  labels: string[];
  values: number[];
}
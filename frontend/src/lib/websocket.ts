/**
 * WebSocket Client para telemetría en tiempo real
 * 
 * Cliente WebSocket para recibir datos de simulación en tiempo real
 * desde el backend FastAPI.
 */

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

export interface TelemetryMessage {
  timestamp: number;
  component_id: string;
  signal_id: string;
  value: number;
  unit?: string;
}

export interface SimulationStatus {
  run_id: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'stopped';
  progress: number;
  current_time: number;
  duration: number;
  error?: string;
}

export interface WebSocketMessage {
  type: 'telemetry' | 'status' | 'alert' | 'error';
  data: TelemetryMessage | SimulationStatus | any;
}

type MessageHandler = (message: WebSocketMessage) => void;
type ErrorHandler = (error: Event) => void;
type CloseHandler = (event: CloseEvent) => void;

/**
 * Cliente WebSocket para telemetría de simulaciones
 */
export class SimulationWebSocket {
  private ws: WebSocket | null = null;
  private runId: string;
  private messageHandlers: Set<MessageHandler> = new Set();
  private errorHandlers: Set<ErrorHandler> = new Set();
  private closeHandlers: Set<CloseHandler> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // ms

  constructor(runId: string) {
    this.runId = runId;
  }

  /**
   * Conectar al WebSocket
   */
  connect(token?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const url = token 
          ? `${WS_BASE_URL}/ws/telemetry/${this.runId}?token=${token}`
          : `${WS_BASE_URL}/ws/telemetry/${this.runId}`;

        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          console.log(`WebSocket connected to simulation ${this.runId}`);
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.messageHandlers.forEach(handler => handler(message));
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onerror = (event) => {
          console.error('WebSocket error:', event);
          this.errorHandlers.forEach(handler => handler(event));
          reject(event);
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          this.closeHandlers.forEach(handler => handler(event));
          
          // Auto-reconectar si no fue un cierre intencional
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnect(token);
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Reconectar al WebSocket
   */
  private reconnect(token?: string) {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      this.connect(token).catch(() => {
        // Silenciar errores de reconexión, el handler onclose se encargará
      });
    }, delay);
  }

  /**
   * Enviar comando al servidor
   */
  sendCommand(command: string, data?: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        command,
        data
      }));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  /**
   * Suscribirse a mensajes
   */
  onMessage(handler: MessageHandler) {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  /**
   * Suscribirse a errores
   */
  onError(handler: ErrorHandler) {
    this.errorHandlers.add(handler);
    return () => this.errorHandlers.delete(handler);
  }

  /**
   * Suscribirse al evento de cierre
   */
  onClose(handler: CloseHandler) {
    this.closeHandlers.add(handler);
    return () => this.closeHandlers.delete(handler);
  }

  /**
   * Cerrar la conexión WebSocket
   */
  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  /**
   * Verificar si está conectado
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

/**
 * Hook helper para React (opcional)
 */
export function createSimulationWebSocket(runId: string, token?: string) {
  const ws = new SimulationWebSocket(runId);
  ws.connect(token);
  return ws;
}

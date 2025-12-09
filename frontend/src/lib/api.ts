/**
 * API Client para TwinSec Studio Backend
 * 
 * Cliente centralizado para todas las peticiones HTTP al backend FastAPI.
 * Maneja autenticación JWT, refresh tokens, y manejo de errores.
 */

// Configuración base de la API
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_VERSION = '/api/v1';

export const API_URL = `${API_BASE_URL}${API_VERSION}`;

/**
 * Tipos de respuesta de la API
 */
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

/**
 * Token storage en localStorage
 */
const TOKEN_KEY = 'twinsec_access_token';
const REFRESH_TOKEN_KEY = 'twinsec_refresh_token';

export const tokenStorage = {
  getAccessToken: (): string | null => localStorage.getItem(TOKEN_KEY),
  setAccessToken: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  getRefreshToken: (): string | null => localStorage.getItem(REFRESH_TOKEN_KEY),
  setRefreshToken: (token: string) => localStorage.setItem(REFRESH_TOKEN_KEY, token),
  clearTokens: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
};

/**
 * Cliente HTTP con manejo automático de JWT
 */
class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  /**
   * Obtiene los headers comunes para las peticiones
   */
  private getHeaders(includeAuth = true): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (includeAuth) {
      const token = tokenStorage.getAccessToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  /**
   * Maneja errores de la API
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`
      }));
      
      throw new Error(error.detail || error.message || 'Unknown error');
    }

    return response.json();
  }

  /**
   * Realiza una petición GET
   */
  async get<T>(endpoint: string, includeAuth = true): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'GET',
      headers: this.getHeaders(includeAuth),
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Realiza una petición POST
   */
  async post<T>(endpoint: string, body?: any, includeAuth = true): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers: this.getHeaders(includeAuth),
      body: body ? JSON.stringify(body) : undefined,
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Realiza una petición PUT
   */
  async put<T>(endpoint: string, body: any, includeAuth = true): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'PUT',
      headers: this.getHeaders(includeAuth),
      body: JSON.stringify(body),
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Realiza una petición DELETE
   */
  async delete<T>(endpoint: string, includeAuth = true): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'DELETE',
      headers: this.getHeaders(includeAuth),
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Realiza una petición PATCH
   */
  async patch<T>(endpoint: string, body: any, includeAuth = true): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'PATCH',
      headers: this.getHeaders(includeAuth),
      body: JSON.stringify(body),
    });

    return this.handleResponse<T>(response);
  }
}

// Instancia singleton del cliente API
export const apiClient = new ApiClient(API_URL);

/**
 * API Endpoints - Autenticación
 */
export const authAPI = {
  /**
   * Login con email y password
   */
  login: async (email: string, password: string) => {
    const response = await apiClient.post<{
      access_token: string;
      refresh_token: string;
      token_type: string;
      expires_in: number;
    }>('/auth/login', { username: email, password }, false);
    
    // Guardar tokens
    tokenStorage.setAccessToken(response.access_token);
    tokenStorage.setRefreshToken(response.refresh_token);
    
    return response;
  },

  /**
   * Registro de nuevo usuario
   */
  register: async (email: string, password: string, fullName?: string) => {
    return apiClient.post('/auth/register', {
      email,
      password,
      full_name: fullName
    }, false);
  },

  /**
   * Obtener información del usuario actual
   */
  getCurrentUser: async () => {
    return apiClient.get('/auth/me');
  },

  /**
   * Refresh del access token
   */
  refreshToken: async () => {
    const refreshToken = tokenStorage.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await apiClient.post<{
      access_token: string;
      token_type: string;
      expires_in: number;
    }>('/auth/refresh', { refresh_token: refreshToken }, false);

    tokenStorage.setAccessToken(response.access_token);
    
    return response;
  },

  /**
   * Logout
   */
  logout: () => {
    tokenStorage.clearTokens();
  }
};

/**
 * API Endpoints - Modelos
 */
export const modelsAPI = {
  /**
   * Generar modelo con LLM
   */
  generate: async (prompt: string, modelType?: string) => {
    return apiClient.post('/models/generate', {
      prompt,
      model_type: modelType
    });
  },

  /**
   * Listar modelos del usuario
   */
  list: async (page = 1, size = 20) => {
    return apiClient.get<PaginatedResponse<any>>(`/models?page=${page}&size=${size}`);
  },

  /**
   * Obtener un modelo por ID
   */
  get: async (modelId: number) => {
    return apiClient.get(`/models/${modelId}`);
  },

  /**
   * Actualizar un modelo
   */
  update: async (modelId: number, data: any) => {
    return apiClient.put(`/models/${modelId}`, data);
  },

  /**
   * Eliminar un modelo
   */
  delete: async (modelId: number) => {
    return apiClient.delete(`/models/${modelId}`);
  }
};

/**
 * API Endpoints - Simulaciones
 */
export const simulationsAPI = {
  /**
   * Iniciar una simulación
   */
  start: async (modelId: number, duration: number, timeStep: number, attackConfig?: any) => {
    return apiClient.post('/runs/start', {
      model_id: modelId,
      duration,
      time_step: timeStep,
      attack_config: attackConfig
    });
  },

  /**
   * Listar simulaciones del usuario
   */
  list: async (page = 1, size = 20) => {
    return apiClient.get<PaginatedResponse<any>>(`/runs?page=${page}&size=${size}`);
  },

  /**
   * Obtener una simulación por run_id
   */
  get: async (runId: string) => {
    return apiClient.get(`/runs/${runId}`);
  },

  /**
   * Detener una simulación
   */
  stop: async (runId: string) => {
    return apiClient.post(`/runs/${runId}/stop`, {});
  },

  /**
   * Pausar una simulación
   */
  pause: async (runId: string) => {
    return apiClient.post(`/runs/${runId}/pause`, {});
  },

  /**
   * Reanudar una simulación
   */
  resume: async (runId: string) => {
    return apiClient.post(`/runs/${runId}/resume`, {});
  }
};

/**
 * API Endpoints - Logs de Auditoría
 */
export const logsAPI = {
  /**
   * Listar logs de auditoría
   */
  list: async (page = 1, size = 50, eventType?: string, severity?: string) => {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    
    if (eventType) params.append('event_type', eventType);
    if (severity) params.append('severity', severity);

    return apiClient.get<PaginatedResponse<any>>(`/logs?${params.toString()}`);
  },

  /**
   * Exportar logs en formato JSON
   */
  exportJSON: async (startDate?: string, endDate?: string) => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    return apiClient.get(`/logs/export/json?${params.toString()}`);
  },

  /**
   * Exportar logs en formato CEF (para Wazuh)
   */
  exportCEF: async (startDate?: string, endDate?: string) => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    return apiClient.get(`/logs/export/cef?${params.toString()}`);
  }
};

/**
 * Health Check
 */
export const healthAPI = {
  check: async () => {
    return apiClient.get('/health', false);
  }
};

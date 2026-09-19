import { Capacitor } from '@capacitor/core';
import type {
  Analysis,
  CareEvent,
  DashboardStats,
  Entity,
  HealthCheck,
  Plant,
  PlantInput,
  RelationshipSet,
} from '../types';

/**
 * Backend base URL resolution:
 * - Browser/dev: '' (relative paths, Vite dev-server proxy handles /api + /uploads).
 * - Android/iOS app: the user connects to their PlantMind backend over the LAN
 *   (e.g. http://192.168.1.5:8000). The address is entered once in the app and
 *   remembered in localStorage.
 */
const SERVER_URL_KEY = 'plantmind.serverUrl';

export function isNative(): boolean {
  return Capacitor.isNativePlatform();
}

export function getServerUrl(): string {
  if (!isNative()) return '';
  const stored = localStorage.getItem(SERVER_URL_KEY) ?? '';
  return stored.replace(/\/+$/, '');
}

export function setServerUrl(url: string): void {
  localStorage.setItem(SERVER_URL_KEY, url.trim().replace(/\/+$/, ''));
}

export function hasServerUrl(): boolean {
  return isNative() ? Boolean(getServerUrl()) : true;
}

function base(): string {
  const env = (import.meta as unknown as { env?: Record<string, string> }).env?.VITE_API_URL;
  return getServerUrl() || env || '';
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

/** Abort requests after 20 s so a silently-dropped connection (firewall etc.)
 *  surfaces as an error instead of an endless spinner. */
const REQUEST_TIMEOUT_MS = 20_000;

function timeoutSignal(): { signal: AbortSignal; clear: () => void } {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  return { signal: controller.signal, clear: () => clearTimeout(timer) };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const t = timeoutSignal();
  let res: Response;
  try {
    res = await fetch(base() + path, { ...init, signal: t.signal });
  } catch (e) {
    const aborted = e instanceof DOMException && e.name === 'AbortError';
    throw new ApiError(0, aborted
      ? 'Timed out contacting the backend — check the server address, firewall, and that both devices are on the same network.'
      : 'Network error — is the PlantMind backend reachable? '
        + (base() ? `(${base()})` : 'Is the backend running on port 8000?'));
  } finally {
    t.clear();
  }
  if (res.status === 204) return undefined as T;
  let body: Record<string, unknown> = {};
  try { body = await res.json(); } catch {}
  if (!res.ok) {
    const detail = typeof body.detail === 'string' ? body.detail : `Request failed (${res.status})`;
    throw new ApiError(res.status, detail);
  }
  return body as T;
}
async function form<T>(path: string, form: FormData): Promise<T> {
  const t = timeoutSignal();
  let res: Response;
  try {
    res = await fetch(base() + path, { method: 'POST', body: form, signal: t.signal });
  } catch (e) {
    const aborted = e instanceof DOMException && e.name === 'AbortError';
    throw new ApiError(0, aborted
      ? 'Timed out sending the analysis to the backend — check the server address, firewall, and network.'
      : 'Network error — is the PlantMind backend reachable? '
        + (base() ? `(${base()})` : 'Is the backend running on port 8000?'));
  } finally {
    t.clear();
  }
  if (res.status === 204) return undefined as T;
  let body: Record<string, unknown> = {};
  try { body = await res.json(); } catch {}
  if (!res.ok) {
    const detail = typeof body.detail === 'string' ? body.detail : `Request failed (${res.status})`;
    throw new ApiError(res.status, detail);
  }
  return body as T;
}

export const api = {
  health: () => request<HealthCheck>('/api/health'),
  dashboardStats: () => request<DashboardStats>('/api/dashboard/stats'),

  listPlants: () => request<Plant[]>('/api/plants'),
  getPlant: (id: number) => request<Plant>(`/api/plants/${id}`),
  createPlant: (payload: PlantInput) =>
    request<Plant>('/api/plants', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  updatePlant: (id: number, payload: PlantInput) =>
    request<Plant>(`/api/plants/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  deletePlant: (id: number) =>
    request<void>(`/api/plants/${id}`, { method: 'DELETE' }),

  analyzePlant: (plantId: number, image: File, symptoms: string) => {
    const formData = new FormData();
    formData.append('image', image);
    formData.append('symptoms', symptoms);
    return form<Analysis>(`/api/plants/${plantId}/analyze`, formData);
  },

  plantAnalyses: (plantId: number) =>
    request<Analysis[]>(`/api/plants/${plantId}/analyses`),
  plantCare: (plantId: number) =>
    request<CareEvent[]>(`/api/plants/${plantId}/care`),
  allAnalyses: () =>
    request<Analysis[]>('/api/analyses'),
  getAnalysis: (id: number) =>
    request<Analysis>(`/api/analyses/${id}`),

  searchKnowledge: (q?: string, entity_type?: string) => {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (entity_type) params.set('entity_type', entity_type);
    return request<Entity[]>(`/api/knowledge/search?${params}`);
  },
  knowledgeTypes: () =>
    request<Record<string, number>>('/api/knowledge/types'),
  knowledgeEntity: (id: string) =>
    request<Entity>(`/api/knowledge/entity/${id}`),
  knowledgeRelationships: (id: string) =>
    request<RelationshipSet>(`/api/knowledge/relationships/${id}`),

  resetDemo: () =>
    request<{ status: string; demo_plants_created: number }>('/api/demo/reset', {
      method: 'POST',
    }),
};

export function imageUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  // Stored paths look like "uploads/<file>.jpg"; the static mount is /uploads.
  const clean = path.startsWith('uploads/') ? path.slice('uploads/'.length) : path;
  // On native (Android APK) images live on the remote PlantMind server.
  return `${getServerUrl()}/uploads/${clean}`;
}

export type { PlantInput };

export type ApiError = { detail?: string; [key: string]: unknown };

const API_ROOT = '/api/v1';

export class HttpError extends Error {
  status: number;
  payload: ApiError;
  constructor(status: number, payload: ApiError) {
    const detail = typeof payload.detail === 'string' ? payload.detail : Object.values(payload).flat().join(' ');
    super(detail || `Erreur HTTP ${status}`);
    this.status = status;
    this.payload = payload;
  }
}

export async function api<T>(path: string, token?: string | null, options: {
  method?: string; body?: unknown; file?: File; headers?: HeadersInit;
} = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (token) headers.set('Authorization', `Token ${token}`);
  let body: BodyInit | undefined;
  if (options.file) {
    const data = new FormData();
    data.append('file', options.file);
    if (options.body && typeof options.body === 'object') {
      Object.entries(options.body as Record<string, unknown>).forEach(([key, value]) => data.append(key, String(value)));
    }
    body = data;
  } else if (options.body !== undefined) {
    headers.set('Content-Type', 'application/json');
    body = JSON.stringify(options.body);
  }
  const response = await fetch(`${API_ROOT}${path}`, {
    method: options.method || (body ? 'POST' : 'GET'), headers, body, credentials: 'omit',
  });
  if (response.status === 204) return undefined as T;
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json() : { detail: await response.text() };
  if (!response.ok) throw new HttpError(response.status, payload as ApiError);
  return payload as T;
}

export async function downloadCsv(path: string, token: string, filename: string): Promise<void> {
  const response = await fetch(`${API_ROOT}${path}`, { headers: { Authorization: `Token ${token}` } });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new HttpError(response.status, payload);
  }
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}

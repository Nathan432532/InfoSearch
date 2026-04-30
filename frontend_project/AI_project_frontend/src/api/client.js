import axios from 'axios';

const FALLBACK_API_URL = 'http://91.99.180.245:8000';

function resolveApiBaseUrl() {
  const envUrl = (import.meta.env.VITE_API_URL || '').trim();
  if (envUrl) return envUrl.replace(/\/+$/, '');

  if (typeof window === 'undefined') {
    return FALLBACK_API_URL;
  }

  const { protocol, hostname } = window.location;
  const isLocalhost = /^(localhost|127\.0\.0\.1)$/i.test(hostname);

  if (isLocalhost) {
    return 'http://localhost:8000';
  }

  return `${protocol}//${hostname}:8000`;
}

const client = axios.create({
  baseURL: resolveApiBaseUrl(),
  withCredentials: true,
});

export const API_BASE_URL = resolveApiBaseUrl();

export default client;

import axios from 'axios';

const defaultApiUrl =
  typeof window !== 'undefined' && /^(localhost|127\.0\.0\.1)$/i.test(window.location.hostname)
    ? 'http://localhost:8000'
    : 'http://91.99.180.245:8000';

const client = axios.create({
  baseURL: (import.meta.env.VITE_API_URL || defaultApiUrl).replace(/\/+$/, ''),
  withCredentials: true,
});

export default client;

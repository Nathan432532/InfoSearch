import axios from 'axios';

const client = axios.create({
  baseURL: (import.meta.env.VITE_API_URL || 'http://91.99.180.245:8000').replace(/\/+$/, ''),
});

export default client;

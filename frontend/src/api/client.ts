import axios from 'axios';

export const API_BASE_URL = 'http://localhost:5000/api';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getHealth = () => client.get('/health/status');
export const getDashboardStats = () => client.get('/dashboard/stats');
export const getDashboardActivity = (limit = 50) => client.get(`/dashboard/activity?limit=${limit}`);
export const getAlerts = () => client.get('/alerts/');
export const runPrediction = (packet: any) => client.post('/predictions/detect', packet);

export default client;

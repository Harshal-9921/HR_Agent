import axios from 'axios';

const api = axios.create({
<<<<<<< HEAD
  baseURL: 'http://10.130.37.2:8001/api',
=======
  baseURL: '/api', // Works via Nginx proxy
>>>>>>> f7ba691 (Dockerized application, setup staging deployment, and fixed API routing)
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;

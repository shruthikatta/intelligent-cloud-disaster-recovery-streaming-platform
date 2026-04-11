import axios from "axios";

export const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

export const api = axios.create({ baseURL: API_BASE });

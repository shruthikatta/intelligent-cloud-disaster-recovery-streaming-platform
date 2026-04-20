import axios from "axios";

const raw = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";
export const API_BASE = raw.replace(/\/+$/, "");

export const api = axios.create({ baseURL: API_BASE });

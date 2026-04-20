import axios from "axios";

const raw = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";
const base = raw.replace(/\/+$/, "");

export const api = axios.create({ baseURL: base });

export function setAuth(token: string | null) {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common.Authorization;
  }
}

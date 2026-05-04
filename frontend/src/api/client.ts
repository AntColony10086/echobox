import axios, { AxiosError } from "axios";

export const apiClient = axios.create({
  baseURL: "/api",
  timeout: 60_000,
});

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    detail?: Record<string, unknown>;
  };
}

export function unwrapError(err: unknown): { code: string; message: string } {
  if (err instanceof AxiosError && err.response?.data) {
    const body = err.response.data as ApiErrorBody;
    if (body.error)
      return { code: body.error.code, message: body.error.message };
  }
  return { code: "unknown", message: String(err) };
}

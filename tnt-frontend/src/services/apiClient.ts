import axios, { AxiosError } from 'axios';

import { API_BASE_URL, API_PREFIX, STORAGE_KEYS } from '../utils/constants';
import { getItem } from '../utils/storage';

export type ApiError = {
  status: number;
  message: string;
  detail?: unknown;
};

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}${API_PREFIX}`,
  timeout: 20000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(async (config) => {
  const token = await getItem(STORAGE_KEYS.accessToken);
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function toApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const axErr = error as AxiosError<any>;
    const status = axErr.response?.status ?? 0;
    const data = axErr.response?.data;
    const message =
      (typeof data?.detail === 'string' && data.detail) ||
      (typeof data?.message === 'string' && data.message) ||
      axErr.message ||
      'Request failed';

    return { status, message, detail: data };
  }

  if (error instanceof Error) {
    return { status: 0, message: error.message };
  }

  return { status: 0, message: 'Unknown error' };
}

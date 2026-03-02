import { apiClient } from './apiClient';
import type { User } from '../types/models';

export type LoginResponse = {
  success: boolean;
  message: string;
  data: {
    access_token: string;
    token_type: 'bearer';
    user: User;
    is_new_user: boolean;
  };
};

export async function sendOtp(phone: string): Promise<{ message: string }> {
  const res = await apiClient.post('/auth/send-otp', { phone });
  return res.data as { message: string };
}

export async function login(phone: string, otp: string): Promise<LoginResponse> {
  const res = await apiClient.post('/auth/verify-otp', { phone, otp });
  return res.data as LoginResponse;
}

export async function signup(payload: {
  phone: string;
  name: string;
  role: 'student' | 'faculty';
  university_id?: string | null;
}): Promise<User> {
  const res = await apiClient.post('/users/register', payload);
  return res.data as User;
}

export async function logout(): Promise<void> {
  // Stateless backend: logout is client-side token removal; nothing to call server-side.
  return Promise.resolve();
}

export async function getProfile(): Promise<User> {
  const res = await apiClient.get('/users/me');
  return res.data as User;
}

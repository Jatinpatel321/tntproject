import { apiClient } from './apiClient';
import type { NotificationItem } from '../types/models';

export async function getNotifications(): Promise<NotificationItem[]> {
  const res = await apiClient.get('/notifications');
  return res.data as NotificationItem[];
}

export async function markNotificationRead(notificationId: number): Promise<{ message: string }> {
  const res = await apiClient.post(`/notifications/${notificationId}/read`);
  return res.data as { message: string };
}

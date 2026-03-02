import { apiClient } from './apiClient';
import type { Order, OrderHistoryItem } from '../types/models';

export type OrderItemDetail = {
  name: string;
  image_url?: string | null;
  quantity: number;
  price_at_time: number;
  line_total: number;
};

export type OrderDetail = {
  order_id: number;
  status: string;
  created_at: string;
  items: OrderItemDetail[];
  total_amount: number;
};

export async function getMyOrders(): Promise<Order[]> {
  const res = await apiClient.get('/orders/my');
  return res.data as Order[];
}

export async function getVendorOrderDetail(orderId: number): Promise<OrderDetail> {
  const res = await apiClient.get(`/orders/vendor/${orderId}`);
  return res.data as OrderDetail;
}

export async function getOrderTimeline(orderId: number): Promise<OrderHistoryItem[]> {
  const res = await apiClient.get(`/orders/${orderId}/timeline`);
  return res.data as OrderHistoryItem[];
}

export async function getOrderEta(orderId: number): Promise<any> {
  const res = await apiClient.get(`/orders/${orderId}/eta`);
  return res.data;
}

export async function generateOrderQr(orderId: number): Promise<{ qr_code: string }> {
  const res = await apiClient.post(`/orders/${orderId}/qr`);
  return res.data as { qr_code: string };
}

export async function cancelOrder(orderId: number): Promise<{ message: string }> {
  const res = await apiClient.post(`/orders/${orderId}/cancel`);
  return res.data as { message: string };
}

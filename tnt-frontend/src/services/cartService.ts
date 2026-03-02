import { apiClient } from './apiClient';
import type { Cart } from '../types/models';

export async function getCart(): Promise<Cart> {
  const res = await apiClient.get('/cart');
  return res.data as Cart;
}

export async function addCartItem(menu_item_id: number, quantity: number): Promise<Cart> {
  const res = await apiClient.post('/cart/items', { menu_item_id, quantity });
  return res.data as Cart;
}

export async function removeCartItem(menu_item_id: number): Promise<Cart> {
  const res = await apiClient.delete(`/cart/items/${menu_item_id}`);
  return res.data as Cart;
}

export async function clearCart(): Promise<{ message: string }> {
  const res = await apiClient.delete('/cart');
  return res.data as { message: string };
}

export type CheckoutResponse = {
  order_id: number;
  status: string;
  total_amount: number;
  eta_minutes: number;
  pickup_load_label: string;
  express_pickup_eligible: boolean;
};

export async function checkout(slotId: number): Promise<CheckoutResponse> {
  const res = await apiClient.post(`/cart/checkout/${slotId}`);
  return res.data as CheckoutResponse;
}

export type CheckoutPayResponse = {
  order_created: boolean;
  payment_initiated: boolean;
  order: CheckoutResponse;
  payment: null | {
    payment_id: number;
    razorpay_order_id: string;
    amount: number;
    key: string | null;
    idempotent?: boolean;
  };
  payment_error: null | {
    status_code: number;
    detail: unknown;
  };
};

export async function checkoutAndPay(slotId: number, checkoutIdempotencyKey?: string): Promise<CheckoutPayResponse> {
  const res = await apiClient.post(`/cart/checkout/${slotId}/pay`, null, {
    params: checkoutIdempotencyKey ? { checkout_idempotency_key: checkoutIdempotencyKey } : undefined,
  });
  return res.data as CheckoutPayResponse;
}

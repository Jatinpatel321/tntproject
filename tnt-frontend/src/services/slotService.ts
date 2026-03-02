import { apiClient } from './apiClient';

export type Slot = {
  id: number;
  vendor_id: number;
  start_time: string;
  end_time: string;
  max_orders: number;
  current_orders: number;
  status?: string;
  load_label?: string;
  express_pickup_eligible?: boolean;
};

export async function getSlots(): Promise<Slot[]> {
  const res = await apiClient.get('/slots');
  return res.data as Slot[];
}

export async function bookSlot(slotId: number): Promise<{ message: string; slot_id: number } & Record<string, any>> {
  const res = await apiClient.post(`/slots/${slotId}/book`);
  return res.data as any;
}

export type UserRole = 'student' | 'faculty' | 'vendor' | 'admin' | 'super_admin';

export type User = {
  id: number;
  phone: string;
  name: string | null;
  role: UserRole;
  university_id: string | null;
  is_active: boolean;
  is_approved: boolean;
};

export type VendorType = 'food' | 'stationery';

export type Vendor = {
  id: number;
  name: string | null;
  description: string;
  vendor_type: string;
  is_approved: boolean;
  phone: string;
  is_open: boolean;
  logo_url: string | null;
  live_load_label: string;
  express_pickup_eligible: boolean;
};

export type MenuItem = {
  id: number;
  vendor_id: number;
  name: string;
  description: string | null;
  price: number;
  image_url: string;
  is_available: boolean;
  prep_time_minutes?: number | null;
  category?: string | null;
};

export type VendorSlot = {
  id: number;
  vendor_id: number;
  start_time: string;
  end_time: string;
  is_available: boolean;
  max_orders: number;
  current_orders: number;
  load_label: string;
  express_pickup_eligible: boolean;
};

export type CartItem = {
  menu_item_id: number;
  name: string;
  price: number;
  quantity: number;
};

export type Cart = {
  vendor_id: number | null;
  items: CartItem[];
  total_items: number;
  total_amount: number;
};

export type Order = {
  id: number;
  slot_id: number;
  vendor_id: number;
  status: string;
  created_at: string;
};

export type OrderHistoryItem = {
  status: string;
  changed_at: string;
};

export type NotificationItem = {
  id: number;
  user_id: number;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
};

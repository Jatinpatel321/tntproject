import type { VendorType } from './models';
import type { PickedFile } from '../components/FileCard';

export type PrintOptionsPayload = {
  printType: 'bw' | 'color';
  paperSize: 'A4' | 'A3';
  duplex: boolean;
  copies: number;
  pageMode: 'all' | 'custom';
  pageRange?: string;
  notes?: string;
};

export type UploadFileParam = PickedFile;

export type AuthStackParamList = {
  Splash: undefined;
  Login: undefined;
  Signup: undefined;
};

export type RootStackParamList = {
  AppTabs: undefined;
  Auth: undefined;

  VendorList: { type: VendorType };
  VendorDetail: { vendorId: number; vendorName?: string | null };
  Menu: { vendorId: number; vendorName?: string | null };
  FileUpload: { vendorId: number; vendorName?: string | null };
  PrintOptions: { vendorId: number; vendorName?: string | null; file: UploadFileParam };
  Stationery: {
    vendorId: number;
    vendorName?: string | null;
    file: UploadFileParam;
    options: PrintOptionsPayload;
  };
  Cart: undefined;
  SlotSelection: { vendorId: number };
  OrderTracking: { orderId: number };
  QR: { qrCode: string; orderId: number };
  GroupCart: undefined;
};

export type AppTabsParamList = {
  HomeTab: undefined;
  OrdersTab: undefined;
  NotificationsTab: undefined;
  ProfileTab: undefined;
};

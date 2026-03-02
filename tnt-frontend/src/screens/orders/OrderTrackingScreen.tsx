import React, { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Alert, StyleSheet, View } from 'react-native';
import { Text } from 'react-native-paper';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import type { RootStackParamList } from '../../types/navigation';
import type { Order, OrderHistoryItem, Vendor } from '../../types/models';
import { Screen } from '../../components/Screen';
import { GradientButton } from '../../components/GradientButton';
import { OrderStatusCard } from '../../components/OrderStatusCard';
import { ETABox } from '../../components/ETABox';
import { OrderTimeline } from '../../components/OrderTimeline';
import { getMyOrders, getOrderEta, getOrderTimeline, generateOrderQr, getVendorOrderDetail, type OrderDetail } from '../../services/orderService';
import { getVendors } from '../../services/vendorService';
import { getSlots, type Slot } from '../../services/slotService';
import { toApiError } from '../../services/apiClient';

type Props = NativeStackScreenProps<RootStackParamList, 'OrderTracking'>;

export function OrderTrackingScreen({ route, navigation }: Props) {
  const { orderId } = route.params;

  const [loading, setLoading] = useState(true);
  const [order, setOrder] = useState<Order | null>(null);
  const [timeline, setTimeline] = useState<OrderHistoryItem[]>([]);
  const [eta, setEta] = useState<{ estimated_ready_at?: string | null } | null>(null);
  const [vendorMap, setVendorMap] = useState<Record<number, Vendor>>({});
  const [slots, setSlots] = useState<Slot[]>([]);
  const [detail, setDetail] = useState<OrderDetail | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const [orders, timelineRes, etaRes, slotsRes, food, stationery] = await Promise.all([
          getMyOrders(),
          getOrderTimeline(orderId),
          getOrderEta(orderId),
          getSlots(),
          getVendors('food'),
          getVendors('stationery'),
        ]);

        setOrder(orders.find((o) => o.id === orderId) ?? null);
        setTimeline(timelineRes);
        setEta(etaRes as any);
        setSlots(slotsRes);
        const map: Record<number, Vendor> = {};
        [...food, ...stationery].forEach((v) => {
          map[v.id] = v;
        });
        setVendorMap(map);

        try {
          const d = await getVendorOrderDetail(orderId);
          setDetail(d);
        } catch (inner) {
          // ignore if not permitted
        }
      } catch (e) {
        Alert.alert('Failed to load order', toApiError(e).message);
      } finally {
        setLoading(false);
      }
    })();
  }, [orderId]);

  const vendorName = useMemo(() => {
    if (order && vendorMap[order.vendor_id]) return vendorMap[order.vendor_id].name ?? `Vendor #${order.vendor_id}`;
    if (order) return `Vendor #${order.vendor_id}`;
    return 'Vendor';
  }, [order, vendorMap]);

  const orderType = useMemo(() => {
    if (order && vendorMap[order.vendor_id]) {
      return vendorMap[order.vendor_id].vendor_type === 'stationery' ? 'stationery' : 'food';
    }
    return 'food';
  }, [order, vendorMap]);

  const status = useMemo(() => {
    if (timeline.length) return timeline[timeline.length - 1].status;
    return order?.status ?? 'placed';
  }, [timeline, order]);

  const slotWindow = useMemo(() => {
    if (!order) return null;
    const slot = slots.find((s) => s.id === order.slot_id);
    if (!slot) return null;
    const start = new Date(slot.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const end = new Date(slot.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return `${start} – ${end}`;
  }, [order, slots]);

  const items = detail?.items ?? [];
  const totalAmount = detail?.total_amount ?? null;

  const onQr = async () => {
    try {
      const res = await generateOrderQr(orderId);
      navigation.navigate('QR', { qrCode: res.qr_code, orderId });
    } catch (e) {
      Alert.alert('QR failed', toApiError(e).message);
    }
  };

  return (
    <Screen scroll>
      <View style={styles.header}>
        <Text style={styles.title}>Order #{orderId}</Text>
        <Text style={styles.sub}>{status}</Text>
      </View>

      {loading ? (
        <View style={styles.center}><ActivityIndicator /></View>
      ) : (
        <View style={styles.gap16}>
          <OrderStatusCard status={status} vendorName={vendorName} orderType={orderType as any} />
          <ETABox etaIso={eta?.estimated_ready_at} />
          <OrderTimeline items={timeline} />

          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Order Details</Text>
            <Text style={styles.meta}>Vendor: {vendorName}</Text>
            {slotWindow ? <Text style={styles.meta}>Slot: {slotWindow}</Text> : null}
            <Text style={styles.meta}>Order Type: {orderType === 'stationery' ? 'Stationery' : 'Food'}</Text>
            {totalAmount !== null && <Text style={styles.meta}>Total: ₹{Number(totalAmount).toFixed(2)}</Text>}
          </View>

          {items.length > 0 && (
            <View style={styles.card}>
              <Text style={styles.sectionTitle}>Items</Text>
              {items.map((item, idx) => (
                <View key={`${item.name}-${idx}`} style={styles.itemRow}>
                  <Text style={styles.itemName}>{item.name}</Text>
                  <Text style={styles.itemMeta}>Qty: {item.quantity}</Text>
                  <Text style={styles.itemMeta}>₹{Number(item.line_total).toFixed(2)}</Text>
                </View>
              ))}
            </View>
          )}

          <View style={styles.actions}>
            <GradientButton label="View QR Code" onPress={onQr} />
          </View>
        </View>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: {
    paddingVertical: 10,
  },
  title: {
    fontSize: 18,
    fontWeight: '800',
  },
  sub: {
    fontSize: 14,
    color: '#6B7280',
  },
  center: {
    paddingVertical: 24,
    alignItems: 'center',
  },
  gap16: {
    gap: 16,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    shadowColor: 'rgba(0,0,0,0.08)',
    shadowOpacity: 0.08,
    shadowOffset: { width: 0, height: 3 },
    shadowRadius: 8,
    elevation: 4,
    gap: 6,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '800',
  },
  meta: {
    fontSize: 14,
    color: '#4B5563',
  },
  itemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 6,
  },
  itemName: {
    fontSize: 14,
    fontWeight: '700',
    flex: 1,
  },
  itemMeta: {
    fontSize: 13,
    color: '#6B7280',
    marginLeft: 10,
  },
  actions: {
    marginVertical: 10,
  },
});

import React from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { Text } from 'react-native-paper';

import type { Order } from '../types/models';

const STATUS_LABELS: Record<string, string> = {
  placed: 'Order Placed',
  pending: 'Order Placed',
  confirmed: 'Vendor Accepted',
  ready: 'Ready for Pickup',
  ready_for_pickup: 'Ready for Pickup',
  picked: 'Collected',
  completed: 'Collected',
  cancelled: 'Cancelled',
};

export function OrderHistoryCard(props: {
  order: Order;
  vendorName: string;
  totalAmount?: number | null;
  onPress: () => void;
}) {
  const { order, vendorName, totalAmount, onPress } = props;
  const statusKey = (order.status || '').toLowerCase();
  const statusLabel = STATUS_LABELS[statusKey] ?? order.status;

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.wrap, pressed && styles.pressed]}>
      <View style={styles.card}>
        <Text style={styles.title}>{vendorName}</Text>
        <Text style={styles.meta}>{statusLabel}</Text>
        <Text style={styles.meta}>{new Date(order.created_at).toLocaleString()}</Text>
        <View style={styles.row}>
          <Text style={styles.orderId}>Order #{order.id}</Text>
          {typeof totalAmount === 'number' ? <Text style={styles.total}>₹{Number(totalAmount).toFixed(2)}</Text> : null}
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  wrap: {
    width: '100%',
  },
  pressed: {
    opacity: 0.9,
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
  title: {
    fontSize: 16,
    fontWeight: '800',
    color: '#111827',
  },
  meta: {
    fontSize: 13,
    color: '#4B5563',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  orderId: {
    fontSize: 13,
    color: '#6B7280',
  },
  total: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
  },
});

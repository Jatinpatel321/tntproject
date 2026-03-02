import React from 'react';
import { StyleSheet, View } from 'react-native';
import { Text } from 'react-native-paper';

const STATUS_LABELS: Record<string, string> = {
  placed: 'Order Placed',
  pending: 'Order Placed',
  confirmed: 'Vendor Accepted',
  preparing: 'Preparing',
  ready: 'Ready for Pickup',
  ready_for_pickup: 'Ready for Pickup',
  picked: 'Collected',
  completed: 'Collected',
  cancelled: 'Cancelled',
};

export function OrderStatusCard(props: {
  status: string;
  vendorName: string;
  orderType: 'food' | 'stationery';
}) {
  const statusKey = (props.status || '').toLowerCase();
  const label = STATUS_LABELS[statusKey] ?? props.status ?? 'Unknown';
  const isReady = ['ready', 'ready_for_pickup'].includes(statusKey);

  return (
    <View style={[styles.card, isReady && styles.readyCard]}>
      <Text style={styles.caption}>Status</Text>
      <Text style={styles.title}>{label}</Text>
      <Text style={styles.meta}>{props.vendorName}</Text>
      <Text style={styles.meta}>Order Type: {props.orderType === 'stationery' ? 'Stationery' : 'Food'}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
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
  readyCard: {
    backgroundColor: '#E7F6EC',
  },
  caption: {
    fontSize: 13,
    color: '#6B7280',
  },
  title: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
  },
  meta: {
    fontSize: 14,
    color: '#4B5563',
  },
});

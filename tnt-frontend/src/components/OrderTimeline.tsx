import React from 'react';
import { StyleSheet, View } from 'react-native';
import { Text } from 'react-native-paper';

export type TimelineItem = {
  status: string;
  changed_at: string;
};

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

export function OrderTimeline(props: { items: TimelineItem[] }) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Timeline</Text>
      {props.items.length === 0 ? (
        <Text style={styles.muted}>No events yet.</Text>
      ) : (
        props.items.map((item, idx) => {
          const statusKey = (item.status || '').toLowerCase();
          const label = STATUS_LABELS[statusKey] ?? item.status;
          const done = ['placed', 'pending', 'confirmed', 'preparing', 'ready', 'ready_for_pickup', 'picked', 'completed'].includes(statusKey);
          return (
            <View key={`${item.changed_at}-${idx}`} style={styles.row}>
              <View style={[styles.dot, done ? styles.dotDone : styles.dotPending]} />
              <View style={styles.rowContent}>
                <Text style={styles.label}>{label}</Text>
                <Text style={styles.time}>{new Date(item.changed_at).toLocaleString()}</Text>
              </View>
            </View>
          );
        })
      )}
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
    gap: 10,
  },
  title: {
    fontSize: 16,
    fontWeight: '800',
  },
  muted: {
    color: '#6B7280',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  dot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginTop: 4,
  },
  dotDone: {
    backgroundColor: '#6C63FF',
  },
  dotPending: {
    backgroundColor: '#9CA3AF',
  },
  rowContent: {
    flex: 1,
    gap: 2,
  },
  label: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
  },
  time: {
    fontSize: 12,
    color: '#6B7280',
  },
});

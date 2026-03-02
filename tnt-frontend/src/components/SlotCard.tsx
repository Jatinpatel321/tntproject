import React from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { Text } from 'react-native-paper';

import type { Slot } from '../services/slotService';

export function SlotCard(props: {
  slot: Slot;
  selected: boolean;
  onPress: () => void;
}) {
  const { slot, selected, onPress } = props;

  const available = Math.max((slot.max_orders ?? 0) - (slot.current_orders ?? 0), 0);
  const isFull = available <= 0 || (slot.status ?? '').toLowerCase() === 'full';

  const content = (
    <View style={[styles.card, isFull && styles.cardFull]}>
      <Text style={styles.time}>{formatRange(slot.start_time, slot.end_time)}</Text>
      <Text style={styles.meta}>Available: {available}</Text>
      <Text style={styles.meta}>ETA: {formatEta(slot.start_time)}</Text>
    </View>
  );

  if (selected && !isFull) {
    return (
      <LinearGradient colors={['#6C63FF', '#4A90E2']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.border}>
        <Pressable onPress={onPress} disabled={isFull} style={styles.pressable}>
          {content}
        </Pressable>
      </LinearGradient>
    );
  }

  return (
    <Pressable onPress={onPress} disabled={isFull} style={styles.pressable}>
      {content}
    </Pressable>
  );
}

function formatRange(start: string, end: string): string {
  const s = new Date(start);
  const e = new Date(end);
  return `${formatTime(s)} – ${formatTime(e)}`;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatEta(start: string): string {
  const now = Date.now();
  const startMs = new Date(start).getTime();
  const diffMin = Math.max(Math.round((startMs - now) / 60000), 0);
  return `${diffMin} min`;
}

const styles = StyleSheet.create({
  pressable: {
    width: '48%',
  },
  border: {
    borderRadius: 18,
    padding: 2,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 14,
    shadowColor: 'rgba(0,0,0,0.08)',
    shadowOpacity: 0.08,
    shadowOffset: { width: 0, height: 3 },
    shadowRadius: 8,
    elevation: 4,
    gap: 4,
  },
  cardFull: {
    backgroundColor: '#EEEEEE',
  },
  time: {
    fontSize: 16,
    fontWeight: '800',
    color: '#111827',
  },
  meta: {
    fontSize: 13,
    color: '#6B7280',
  },
});

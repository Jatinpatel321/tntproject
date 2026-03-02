import React, { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Alert, StyleSheet, View } from 'react-native';
import { Text } from 'react-native-paper';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import type { RootStackParamList } from '../../types/navigation';
import { Screen } from '../../components/Screen';
import { GradientButton } from '../../components/GradientButton';
import { SlotCard } from '../../components/SlotCard';
import { bookSlot, getSlots, type Slot } from '../../services/slotService';
import { toApiError } from '../../services/apiClient';

type Props = NativeStackScreenProps<RootStackParamList, 'SlotSelection'>;

export function SlotSelectionScreen({ route, navigation }: Props) {
  const { vendorId } = route.params;

  const [slots, setSlots] = useState<Slot[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [booking, setBooking] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const list = await getSlots();
        const scoped = list.filter((s) => !vendorId || s.vendor_id === vendorId);
        setSlots(scoped);
      } catch (e) {
        Alert.alert('Failed to load slots', toApiError(e).message);
      } finally {
        setLoading(false);
      }
    })();
  }, [vendorId]);

  const selectedSlot = useMemo(() => slots.find((s) => s.id === selectedId) ?? null, [slots, selectedId]);

  const etaLabel = useMemo(() => {
    const source = selectedSlot ?? slots.find((s) => !isFullSlot(s));
    if (!source) return '—';
    const start = new Date(source.start_time);
    return start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }, [selectedSlot, slots]);

  const onConfirm = async () => {
    if (!selectedSlot) return;
    try {
      setBooking(true);
      const res = await bookSlot(selectedSlot.id);
      const orderId = (res as any)?.order_id ?? (res as any)?.orderId ?? null;

      if (orderId) {
        navigation.navigate('OrderTracking', { orderId: Number(orderId) });
        return;
      }

      Alert.alert('Slot confirmed', 'Slot booked successfully. Order details were not returned by the API.');
    } catch (e) {
      Alert.alert('Booking failed', toApiError(e).message);
    } finally {
      setBooking(false);
    }
  };

  return (
    <Screen scroll>
      <View style={styles.header}>
        <Text style={styles.title}>Select a slot</Text>
        <Text style={styles.sub}>Pick your pickup window and continue.</Text>
      </View>

      <View style={styles.etaBlock}>
        <Text style={styles.etaLabel}>Estimated Ready Time</Text>
        <Text style={styles.etaValue}>{etaLabel}</Text>
      </View>

      {loading ? (
        <View style={styles.center}><ActivityIndicator /></View>
      ) : slots.length === 0 ? (
        <Text style={styles.empty}>No slots available.</Text>
      ) : (
        <View style={styles.grid}>
          {slots.map((slot) => (
            <SlotCard
              key={slot.id}
              slot={slot}
              selected={selectedId === slot.id}
              onPress={() => !isFullSlot(slot) && setSelectedId(slot.id)}
            />
          ))}
        </View>
      )}

      <View style={styles.actions}>
        <GradientButton
          label={booking ? 'Booking…' : 'Confirm Slot'}
          onPress={onConfirm}
          disabled={!selectedSlot || booking}
        />
      </View>
    </Screen>
  );
}

function isFullSlot(slot: Slot): boolean {
  const available = Math.max((slot.max_orders ?? 0) - (slot.current_orders ?? 0), 0);
  return available <= 0 || (slot.status ?? '').toLowerCase() === 'full';
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
    marginTop: 4,
  },
  etaBlock: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 14,
    shadowColor: 'rgba(0,0,0,0.08)',
    shadowOpacity: 0.08,
    shadowOffset: { width: 0, height: 3 },
    shadowRadius: 8,
    elevation: 4,
    marginTop: 12,
    gap: 6,
  },
  etaLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  etaValue: {
    fontSize: 20,
    fontWeight: '900',
    color: '#111827',
  },
  center: {
    paddingVertical: 24,
    alignItems: 'center',
  },
  empty: {
    color: '#6B7280',
    marginTop: 12,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginTop: 14,
  },
  actions: {
    marginTop: 18,
    marginBottom: 10,
  },
});

import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Alert, StyleSheet, View } from 'react-native';
import { Text } from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import type { RootStackParamList } from '../../types/navigation';
import type { Order } from '../../types/models';
import { Screen } from '../../components/Screen';
import { RoundedCard } from '../../components/RoundedCard';
import { getMyOrders } from '../../services/orderService';
import { toApiError } from '../../services/apiClient';

type Nav = NativeStackNavigationProp<RootStackParamList>;

export function OrdersScreen() {
  const navigation = useNavigation<Nav>();
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState<Order[]>([]);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const list = await getMyOrders();
        setOrders(list);
      } catch (e) {
        Alert.alert('Failed to load orders', toApiError(e).message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <Screen scroll>
      <View style={styles.header}>
        <Text variant="headlineSmall" style={styles.title}>My Orders</Text>
        <Text style={styles.sub}>Track status and pickup QR.</Text>
      </View>

      {loading ? (
        <View style={styles.center}><ActivityIndicator /></View>
      ) : orders.length === 0 ? (
        <Text style={styles.empty}>No orders yet.</Text>
      ) : (
        orders.map((o) => (
          <RoundedCard key={o.id} onPress={() => navigation.navigate('OrderTracking', { orderId: o.id })}>
            <Text variant="titleMedium" style={styles.name}>Order #{o.id}</Text>
            <Text style={styles.meta}>Status: {o.status}</Text>
            <Text style={styles.meta}>Created: {new Date(o.created_at).toLocaleString()}</Text>
          </RoundedCard>
        ))
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: {
    paddingTop: 18,
    paddingBottom: 8,
  },
  title: {
    fontWeight: '900',
  },
  sub: {
    opacity: 0.7,
    marginTop: 4,
  },
  center: {
    paddingVertical: 24,
    alignItems: 'center',
  },
  empty: {
    opacity: 0.7,
    paddingTop: 12,
  },
  name: {
    fontWeight: '800',
  },
  meta: {
    opacity: 0.7,
    marginTop: 4,
  },
});

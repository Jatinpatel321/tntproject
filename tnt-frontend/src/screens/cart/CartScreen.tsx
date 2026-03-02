import React from 'react';
import { Alert, FlatList, StyleSheet, View } from 'react-native';
import { Text } from 'react-native-paper';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import type { RootStackParamList } from '../../types/navigation';
import { Screen } from '../../components/Screen';
import { GradientButton } from '../../components/GradientButton';
import { useCart } from '../../context/CartContext';
import { formatMoneyPaise } from '../../utils/format';

type Props = NativeStackScreenProps<RootStackParamList, 'Cart'>;

export function CartScreen({ navigation }: Props) {
  const { cart, updateQuantity, clearCart } = useCart();

  const total = cart?.total_amount ?? 0;
  const vendorId = cart?.vendor_id ?? null;

  return (
    <Screen>
      <View style={styles.header}>
        <Text style={styles.title}>Cart</Text>
        <Text style={styles.sub}>Manage quantities and proceed to slot selection.</Text>
      </View>

      <FlatList
        data={cart?.items ?? []}
        keyExtractor={(item) => String(item.menu_item_id)}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.itemName}>{item.name}</Text>
            <Text style={styles.meta}>{formatMoneyPaise(item.price)}</Text>
            <View style={styles.qtyRow}>
              <GradientButton
                label="-"
                onPress={() => updateQuantity(item.menu_item_id, item.quantity - 1)}
                style={styles.smallBtn}
              />
              <Text style={styles.qtyValue}>{item.quantity}</Text>
              <GradientButton
                label="+"
                onPress={() => updateQuantity(item.menu_item_id, item.quantity + 1)}
                style={styles.smallBtn}
              />
            </View>
          </View>
        )}
        contentContainerStyle={styles.list}
        ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
        ListEmptyComponent={<Text style={styles.muted}>Cart is empty.</Text>}
      />

      <View style={styles.totalCard}>
        <Text style={styles.totalLabel}>Total</Text>
        <Text style={styles.totalValue}>{formatMoneyPaise(total)}</Text>
      </View>

      <View style={styles.actions}>
        <GradientButton label="Clear Cart" onPress={clearCart} />
        <GradientButton
          label="Proceed to Slot Selection"
          onPress={() => {
            if (!vendorId) {
              Alert.alert('No vendor selected', 'Add items from a vendor first.');
              return;
            }
            navigation.navigate('SlotSelection', { vendorId });
          }}
          disabled={!vendorId}
        />
      </View>
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
    marginTop: 4,
  },
  list: {
    paddingVertical: 10,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    shadowColor: 'rgba(0,0,0,0.1)',
    shadowOpacity: 0.1,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 8,
    elevation: 4,
  },
  itemName: {
    fontSize: 16,
    fontWeight: '700',
  },
  meta: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  qtyRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginTop: 10,
  },
  qtyValue: {
    fontSize: 16,
    fontWeight: '700',
  },
  smallBtn: {
    flex: 1,
    minWidth: 40,
    height: 40,
    borderRadius: 14,
  },
  muted: {
    textAlign: 'center',
    color: '#6B7280',
  },
  totalCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    shadowColor: 'rgba(0,0,0,0.1)',
    shadowOpacity: 0.1,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 8,
    elevation: 4,
    marginTop: 10,
  },
  totalLabel: {
    fontSize: 16,
    fontWeight: '700',
  },
  totalValue: {
    fontSize: 18,
    fontWeight: '800',
    marginTop: 4,
  },
  actions: {
    marginTop: 12,
    gap: 10,
  },
});

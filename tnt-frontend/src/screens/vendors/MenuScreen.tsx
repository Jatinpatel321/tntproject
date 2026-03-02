import React, { useEffect, useState } from 'react';
import { Alert, FlatList, StyleSheet, View } from 'react-native';
import { Text } from 'react-native-paper';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import type { RootStackParamList } from '../../types/navigation';
import type { MenuItem } from '../../types/models';
import { Screen } from '../../components/Screen';
import { MenuItemCard } from '../../components/MenuItemCard';
import { getVendorMenu } from '../../services/vendorService';
import { toApiError } from '../../services/apiClient';
import { useCart } from '../../context/CartContext';

type Props = NativeStackScreenProps<RootStackParamList, 'Menu'>;

export function MenuScreen({ route }: Props) {
  const { vendorId, vendorName } = route.params;
  const [menu, setMenu] = useState<MenuItem[]>([]);
  const [loading, setLoading] = useState(false);
  const { cart, updateQuantity, addItem } = useCart();

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const items = await getVendorMenu(vendorId);
        setMenu(items);
      } catch (e) {
        Alert.alert('Menu unavailable', toApiError(e).message);
      } finally {
        setLoading(false);
      }
    })();
  }, [vendorId]);

  const getQty = (menuItemId: number) => cart?.items.find((i) => i.menu_item_id === menuItemId)?.quantity ?? 0;

  return (
    <Screen>
      <View style={styles.header}>
        <Text style={styles.title}>{vendorName ?? `Vendor #${vendorId}`}</Text>
        <Text style={styles.sub}>Menu</Text>
      </View>

      <FlatList
        data={menu}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => (
          <MenuItemCard
            item={item}
            quantity={getQty(item.id)}
            onIncrement={() => addItem(item.id, getQty(item.id) + 1)}
            onDecrement={() => updateQuantity(item.id, getQty(item.id) - 1)}
          />
        )}
        contentContainerStyle={styles.list}
        ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
        ListEmptyComponent={!loading ? <Text style={styles.muted}>No items available.</Text> : null}
      />
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
  muted: {
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 12,
  },
});

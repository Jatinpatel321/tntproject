import React, { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Alert, FlatList, Image, Pressable, StyleSheet, View } from 'react-native';
import { Text } from 'react-native-paper';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import type { AppTabsParamList, RootStackParamList } from '../../types/navigation';
import type { Order, User, Vendor } from '../../types/models';
import { Screen } from '../../components/Screen';
import { GradientButton } from '../../components/GradientButton';
import { OrderHistoryCard } from '../../components/OrderHistoryCard';
import { getProfile, logout as apiLogout } from '../../services/authService';
import { getMyOrders } from '../../services/orderService';
import { getVendors } from '../../services/vendorService';
import { toApiError } from '../../services/apiClient';
import { useAuth } from '../../hooks/useAuth';
import { LOGO } from '../../assets';

 type Props = NativeStackScreenProps<AppTabsParamList & RootStackParamList, 'ProfileTab'>;

export function ProfileScreen({ navigation }: Props) {
  const { logout } = useAuth();
  const [profile, setProfile] = useState<User | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [vendors, setVendors] = useState<Record<number, Vendor>>({});
  const [loading, setLoading] = useState(true);
  const [ordersLoading, setOrdersLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [p, myOrders, food, stationery] = await Promise.all([
          getProfile(),
          getMyOrders(),
          getVendors('food'),
          getVendors('stationery'),
        ]);
        setProfile(p);
        setOrders(myOrders);
        const map: Record<number, Vendor> = {};
        [...food, ...stationery].forEach((v) => {
          map[v.id] = v;
        });
        setVendors(map);
      } catch (e) {
        Alert.alert('Failed to load profile', toApiError(e).message);
      } finally {
        setLoading(false);
        setOrdersLoading(false);
      }
    })();
  }, []);

  const vendorName = (vendorId: number) => vendors[vendorId]?.name ?? `Vendor #${vendorId}`;

  const onLogout = async () => {
    try {
      await apiLogout();
      await logout();
      navigation.reset({ index: 0, routes: [{ name: 'Auth' as keyof RootStackParamList }] });
    } catch (e) {
      Alert.alert('Logout failed', toApiError(e).message);
    }
  };

  const settings = useMemo(
    () => [
      { key: 'edit', label: 'Edit Profile' },
      { key: 'password', label: 'Change Password' },
      { key: 'help', label: 'Help & Support' },
    ],
    [],
  );

  return (
    <Screen scroll>
      <View style={styles.header}>
        <Text style={styles.title}>Profile</Text>
      </View>

      <View style={styles.logoWrap}>
        <Image source={LOGO} style={styles.logo} resizeMode="contain" />
      </View>

      <View style={styles.profileCard}>
        <View style={styles.avatar}>
          <MaterialCommunityIcons name="account" size={32} color="#6C63FF" />
        </View>
        <View style={styles.profileInfo}>
          <Text style={styles.name}>{profile?.name ?? 'User'}</Text>
          <Text style={styles.meta}>{profile?.university_id ?? 'University ID not set'}</Text>
          <Text style={styles.meta}>{profile?.phone ?? ''}</Text>
          <Text style={styles.meta}>Role: {profile?.role ?? '—'}</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>My Orders</Text>
        {ordersLoading ? (
          <View style={styles.center}><ActivityIndicator /></View>
        ) : orders.length === 0 ? (
          <Text style={styles.muted}>No orders yet.</Text>
        ) : (
          <FlatList
            data={orders}
            keyExtractor={(item) => String(item.id)}
            renderItem={({ item }) => (
              <OrderHistoryCard
                order={item}
                vendorName={vendorName(item.vendor_id)}
                totalAmount={undefined}
                onPress={() => navigation.navigate('OrderTracking' as any, { orderId: item.id })}
              />
            )}
            ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
            scrollEnabled={false}
            contentContainerStyle={{ gap: 10 }}
          />
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Settings</Text>
        {settings.map((s) => (
          <Pressable key={s.key} style={styles.settingCard}>
            <Text style={styles.settingLabel}>{s.label}</Text>
            <MaterialCommunityIcons name="chevron-right" size={22} color="#6B7280" />
          </Pressable>
        ))}
      </View>

      <View style={styles.actions}>
        <GradientButton label="Logout" onPress={onLogout} />
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
  logoWrap: {
    alignItems: 'center',
    marginBottom: 8,
  },
  logo: {
    width: 80,
    height: 80,
  },
  profileCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    shadowColor: 'rgba(0,0,0,0.08)',
    shadowOpacity: 0.08,
    shadowOffset: { width: 0, height: 3 },
    shadowRadius: 8,
    elevation: 4,
    flexDirection: 'row',
    gap: 12,
    alignItems: 'center',
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#F3F2FF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  profileInfo: {
    flex: 1,
    gap: 4,
  },
  name: {
    fontSize: 17,
    fontWeight: '800',
  },
  meta: {
    fontSize: 13,
    color: '#4B5563',
  },
  section: {
    marginTop: 16,
    gap: 10,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '800',
  },
  center: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  muted: {
    color: '#6B7280',
  },
  settingCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    shadowColor: 'rgba(0,0,0,0.08)',
    shadowOpacity: 0.08,
    shadowOffset: { width: 0, height: 3 },
    shadowRadius: 8,
    elevation: 4,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  settingLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  actions: {
    marginTop: 18,
    marginBottom: 14,
  },
});

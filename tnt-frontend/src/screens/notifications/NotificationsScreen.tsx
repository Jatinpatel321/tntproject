import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Alert, FlatList, RefreshControl, StyleSheet, View } from 'react-native';
import { Text } from 'react-native-paper';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import type { AppTabsParamList } from '../../types/navigation';
import type { NotificationItem } from '../../types/models';
import { Screen } from '../../components/Screen';
import { NotificationCard } from '../../components/NotificationCard';
import { getNotifications, markNotificationRead } from '../../services/notificationService';
import { toApiError } from '../../services/apiClient';

type Props = NativeStackScreenProps<AppTabsParamList, 'NotificationsTab'>;

export function NotificationsScreen({ navigation }: Props) {
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const load = async () => {
    try {
      const list = await getNotifications();
      setItems(list);
    } catch (e) {
      Alert.alert('Failed to load notifications', toApiError(e).message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onPress = async (id: number) => {
    try {
      await markNotificationRead(id);
      setItems((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    } catch (e) {
      Alert.alert('Update failed', toApiError(e).message);
    }
  };

  return (
    <Screen>
      <View style={styles.header}>
        <Text style={styles.title}>Notifications</Text>
        <Text style={styles.sub} onPress={() => navigation.goBack()}>Back</Text>
      </View>

      {loading ? (
        <View style={styles.center}><ActivityIndicator /></View>
      ) : items.length === 0 ? (
        <Text style={styles.empty}>No Notifications Yet</Text>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(item) => String(item.id)}
          renderItem={({ item }) => <NotificationCard item={item} onPress={() => onPress(item.id)} />}
          ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
          contentContainerStyle={styles.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
        />
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: {
    paddingVertical: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    fontSize: 18,
    fontWeight: '800',
  },
  sub: {
    fontSize: 14,
    color: '#6C63FF',
  },
  center: {
    paddingVertical: 24,
    alignItems: 'center',
  },
  empty: {
    color: '#6B7280',
    marginTop: 12,
  },
  list: {
    paddingBottom: 12,
  },
});

import React from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { Text } from 'react-native-paper';

import type { NotificationItem } from '../types/models';

export function NotificationCard(props: { item: NotificationItem; onPress: () => void }) {
  const { item, onPress } = props;
  const isRead = item.is_read;

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.wrapper, pressed && styles.pressed]}>
      <View style={[styles.card, !isRead && styles.unreadCard]}>
        <Text style={styles.title}>{item.title}</Text>
        <Text style={styles.message}>{item.message}</Text>
        <Text style={styles.meta}>{new Date(item.created_at).toLocaleString()} • {isRead ? 'Read' : 'Unread'}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    width: '100%',
  },
  pressed: {
    opacity: 0.85,
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
    gap: 6,
  },
  unreadCard: {
    backgroundColor: '#F3F2FF',
  },
  title: {
    fontSize: 15,
    fontWeight: '800',
    color: '#111827',
  },
  message: {
    fontSize: 14,
    color: '#4B5563',
  },
  meta: {
    fontSize: 12,
    color: '#6B7280',
  },
});

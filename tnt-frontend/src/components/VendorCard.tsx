import React from 'react';
import { Image, Pressable, StyleSheet, View } from 'react-native';
import { Text } from 'react-native-paper';
import type { Vendor } from '../types/models';

export function VendorCard(props: { vendor: Vendor; onPress: () => void }) {
  const { vendor } = props;
  return (
    <Pressable style={styles.card} onPress={props.onPress}>
      <View style={styles.imageWrap}>
        {vendor.logo_url ? (
          <Image source={{ uri: vendor.logo_url }} style={styles.image} resizeMode="cover" />
        ) : (
          <View style={styles.placeholder}>
            <Text style={styles.placeholderText}>{vendor.name?.charAt(0)?.toUpperCase() ?? 'V'}</Text>
          </View>
        )}
      </View>
      <Text style={styles.name} numberOfLines={1}>{vendor.name ?? `Vendor #${vendor.id}`}</Text>
      <Text style={styles.meta} numberOfLines={1}>Prep: {vendor.live_load_label ?? '—'}</Text>
      <Text style={styles.category} numberOfLines={1}>{vendor.vendor_type?.toUpperCase() || 'CATEGORY'}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    width: 180,
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    marginRight: 10,
    shadowColor: 'rgba(0,0,0,0.1)',
    shadowOpacity: 0.1,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 8,
    elevation: 4,
  },
  imageWrap: {
    height: 100,
    borderRadius: 14,
    overflow: 'hidden',
    backgroundColor: '#F5F7FB',
    marginBottom: 10,
  },
  image: {
    width: '100%',
    height: '100%',
  },
  placeholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderText: {
    fontSize: 24,
    fontWeight: '800',
    color: '#6C63FF',
  },
  name: {
    fontSize: 16,
    fontWeight: '700',
  },
  meta: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  category: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4A90E2',
    marginTop: 4,
  },
});

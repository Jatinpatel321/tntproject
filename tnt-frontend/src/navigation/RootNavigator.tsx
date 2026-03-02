import React from 'react';
import { ActivityIndicator, View } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import type { RootStackParamList } from '../types/navigation';
import { useAuth } from '../hooks/useAuth';

import { BottomTabNavigator } from './BottomTabNavigator';
import { AuthNavigator } from './AuthNavigator';
import { VendorListScreen } from '../screens/vendors/VendorListScreen';
import { VendorDetailScreen } from '../screens/vendors/VendorDetailScreen';
import { MenuScreen } from '../screens/vendors/MenuScreen';
import { FileUploadScreen } from '../screens/stationery/FileUploadScreen';
import { PrintOptionsScreen } from '../screens/stationery/PrintOptionsScreen';
import { StationeryScreen } from '../screens/stationery/StationeryScreen';
import { CartScreen } from '../screens/cart/CartScreen';
import { SlotSelectionScreen } from '../screens/slots/SlotSelectionScreen';
import { OrderTrackingScreen } from '../screens/orders/OrderTrackingScreen';
import { QRScreen } from '../screens/qr/QRScreen';
import { GroupCartScreen } from '../screens/groups/GroupCartScreen';

const Stack = createNativeStackNavigator<RootStackParamList>();

function RootNavigator() {
  const { isBootstrapping, accessToken } = useAuth();

  if (isBootstrapping) {
    return (
      <NavigationContainer>
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FFFFFF' }}>
          <ActivityIndicator size="large" />
        </View>
      </NavigationContainer>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {accessToken ? (
          <>
            <Stack.Screen name="AppTabs" component={BottomTabNavigator} />
            <Stack.Screen name="VendorList" component={VendorListScreen} />
            <Stack.Screen name="VendorDetail" component={VendorDetailScreen} />
            <Stack.Screen name="Menu" component={MenuScreen} />
            <Stack.Screen name="FileUpload" component={FileUploadScreen} />
            <Stack.Screen name="PrintOptions" component={PrintOptionsScreen} />
            <Stack.Screen name="Stationery" component={StationeryScreen} />
            <Stack.Screen name="Cart" component={CartScreen} />
            <Stack.Screen name="SlotSelection" component={SlotSelectionScreen} />
            <Stack.Screen name="OrderTracking" component={OrderTrackingScreen} />
            <Stack.Screen name="QR" component={QRScreen} />
            <Stack.Screen name="GroupCart" component={GroupCartScreen} />
          </>
        ) : (
          <Stack.Screen name="Auth" component={AuthNavigator} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}

export default RootNavigator;

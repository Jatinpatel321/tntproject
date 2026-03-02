import React from 'react';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { MD3LightTheme, PaperProvider } from 'react-native-paper';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { AuthProvider } from './src/hooks/useAuth';
import RootNavigator from './src/navigation/RootNavigator';
import { CartProvider } from './src/context/CartContext';

const theme = {
  ...MD3LightTheme,
  roundness: 16,
};

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <PaperProvider theme={theme}>
          <AuthProvider>
            <CartProvider>
              <RootNavigator />
            </CartProvider>
          </AuthProvider>
        </PaperProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

import 'react-native-gesture-handler';

import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';

import { AnalysisProvider } from '@/context/AnalysisContext';
import AnalyzeScreen from '@/screens/AnalyzeScreen';
import CoachScreen from '@/screens/CoachScreen';
import ResultScreen from '@/screens/ResultScreen';
import type { RootStackParamList } from '@/screens/types';

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
  return (
    <AnalysisProvider>
      <NavigationContainer>
        <StatusBar style="auto" />
        <Stack.Navigator initialRouteName="Analyze">
          <Stack.Screen name="Analyze" component={AnalyzeScreen} options={{ title: 'Fotoğraf Seç' }} />
          <Stack.Screen name="Result" component={ResultScreen} options={{ title: 'Analiz Sonucu' }} />
          <Stack.Screen name="Coach" component={CoachScreen} options={{ title: 'Koçluk Formu' }} />
        </Stack.Navigator>
      </NavigationContainer>
    </AnalysisProvider>
  );
}

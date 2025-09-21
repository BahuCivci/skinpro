import React, { useState } from 'react';
import { Alert, Button, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { requestCoach } from '@/api/client';
import { useAnalysis } from '@/context/AnalysisContext';

import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from './types';

export type CoachScreenProps = NativeStackScreenProps<RootStackParamList, 'Coach'>;

export const CoachScreen: React.FC<CoachScreenProps> = ({ navigation }) => {
  const { analysis } = useAnalysis();
  const [hydration, setHydration] = useState('Yeterli');
  const [stress, setStress] = useState('Orta');
  const [sleep, setSleep] = useState('7');
  const [diet, setDiet] = useState('Dengeli');
  const [hormonal, setHormonal] = useState('Stabil');
  const [notes, setNotes] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!analysis) {
      Alert.alert('Önce analiz yapın');
      navigation.replace('Analyze');
      return;
    }
    const sleepHours = Number.parseInt(sleep, 10) || 7;
    try {
      setLoading(true);
      const response = await requestCoach(
        {
          diet,
          stress,
          sleep_hours: sleepHours,
          hydration,
          hormonal,
          skincare: notes.filter(Boolean),
        },
        analysis
      );
      navigation.navigate('Result', { photoUri: '' });
      Alert.alert('Koçluk önerileri hazır', response.alerts.join('\n')); // quick feedback
    } catch (error) {
      console.error(error);
      Alert.alert('Koçluk isteği başarısız oldu');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.title}>Koçluk Formu</Text>
        <Text style={styles.label}>Beslenme</Text>
        <TextInput value={diet} onChangeText={setDiet} style={styles.input} placeholder="Dengeli" />
        <Text style={styles.label}>Stres</Text>
        <TextInput value={stress} onChangeText={setStress} style={styles.input} placeholder="Orta" />
        <Text style={styles.label}>Uyku (saat)</Text>
        <TextInput value={sleep} onChangeText={setSleep} style={styles.input} keyboardType="number-pad" />
        <Text style={styles.label}>Su tüketimi</Text>
        <TextInput value={hydration} onChangeText={setHydration} style={styles.input} placeholder="Yeterli" />
        <Text style={styles.label}>Hormonal durum</Text>
        <TextInput value={hormonal} onChangeText={setHormonal} style={styles.input} placeholder="Stabil" />
        <Text style={styles.label}>Rutin notları (virgülle)</Text>
        <TextInput
          value={notes.join(', ')}
          onChangeText={(text) => setNotes(text.split(',').map((item) => item.trim()))}
          style={styles.input}
          placeholder="Nazik temizleyici, SPF"
        />
        <Button title={loading ? 'Gönderiliyor...' : 'Önerileri Al'} onPress={submit} disabled={loading} />
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scroll: {
    padding: 24,
    gap: 12,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 12,
    padding: 12,
  },
});

export default CoachScreen;

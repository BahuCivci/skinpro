import React from 'react';
import { Button, SafeAreaView, ScrollView, StyleSheet, Text, View } from 'react-native';

import { OverlayImage } from '@/components/OverlayImage';
import { useAnalysis } from '@/context/AnalysisContext';

import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from './types';

export type ResultScreenProps = NativeStackScreenProps<RootStackParamList, 'Result'>;

export const ResultScreen: React.FC<ResultScreenProps> = ({ navigation, route }) => {
  const { analysis } = useAnalysis();
  const photoUri = route.params.photoUri;

  if (!analysis) {
    return (
      <SafeAreaView style={styles.centered}>
        <Text>Analiz sonucu bulunamadı.</Text>
        <Button title="Başa dön" onPress={() => navigation.replace('Analyze')} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.title}>Analiz Sonucu</Text>
        <OverlayImage source={{ uri: photoUri }} overlayBase64={analysis.lesions?.detector_overlay} />
        <View style={styles.card}>
          <Text style={styles.label}>Akne Şiddeti</Text>
          <Text style={styles.value}>{analysis.final_grade}</Text>
          <Text style={styles.meta}>Model Güveni: %{Math.round(analysis.confidence * 100)}</Text>
          <Text style={styles.meta}>Kızarıklık Yoğunluğu: %{analysis.inflamed_area_pct.toFixed(1)}</Text>
        </View>
        <View style={styles.card}>
          <Text style={styles.label}>Kullanılan Modeller</Text>
          <Text style={styles.meta}>ONNX: {analysis.used.classifier_onnx ? 'Evet' : 'Hayır'}</Text>
          <Text style={styles.meta}>HF: {analysis.used.classifier_hf ? 'Evet' : 'Hayır'}</Text>
        </View>
        {analysis.lesions?.detector_regions?.length ? (
          <View style={styles.card}>
            <Text style={styles.label}>Lesyon Tespitleri</Text>
            {analysis.lesions.detector_regions.map((det, idx) => (
              <Text key={idx} style={styles.meta}>
                {idx + 1}. {det.label} · Güven: {(det.confidence * 100).toFixed(1)}% · Alan %{det.area_pct.toFixed(1)}
              </Text>
            ))}
          </View>
        ) : null}
        <Button title="Koçluk Önerilerini Gör" onPress={() => navigation.navigate('Coach')} />
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
    gap: 16,
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
  },
  card: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
    gap: 6,
  },
  label: {
    fontSize: 18,
    fontWeight: '600',
  },
  value: {
    fontSize: 22,
    fontWeight: '700',
  },
  meta: {
    fontSize: 14,
    color: '#555',
  },
});

export default ResultScreen;

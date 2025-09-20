import React, { useState } from 'react';
import { ActivityIndicator, Alert, Button, Image, SafeAreaView, StyleSheet, Text, View } from 'react-native';
import * as ImagePicker from 'expo-image-picker';

import { analyzePhoto } from '@/api/client';
import { useAnalysis } from '@/context/AnalysisContext';

import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from './types';

export type AnalyzeScreenProps = NativeStackScreenProps<RootStackParamList, 'Analyze'>;

export const AnalyzeScreen: React.FC<AnalyzeScreenProps> = ({ navigation }) => {
  const { setAnalysis } = useAnalysis();
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.8,
    });
    if (!result.canceled && result.assets?.length) {
      setImageUri(result.assets[0].uri);
    }
  };

  const openCamera = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Kamera izni gerekli');
      return;
    }
    const result = await ImagePicker.launchCameraAsync({ allowsEditing: true, quality: 0.8 });
    if (!result.canceled && result.assets?.length) {
      setImageUri(result.assets[0].uri);
    }
  };

  const runAnalysis = async () => {
    if (!imageUri) {
      Alert.alert('Lütfen bir fotoğraf seçin');
      return;
    }
    try {
      setLoading(true);
      const analysis = await analyzePhoto(imageUri);
      setAnalysis(analysis);
      navigation.navigate('Result', { photoUri: imageUri });
    } catch (error) {
      console.error(error);
      Alert.alert('Analiz hatası', 'Lütfen sonra tekrar deneyin.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>SkinPro Mobil</Text>
      <Text style={styles.subtitle}>Fotoğrafını yükle, AI analizini başlat.</Text>
      <View style={styles.previewBox}>
        {imageUri ? <Image source={{ uri: imageUri }} style={styles.preview} /> : <Text>Henüz fotoğraf seçilmedi</Text>}
      </View>
      <View style={styles.buttons}>
        <Button title="Galeriden Seç" onPress={pickImage} />
        <Button title="Kamera" onPress={openCamera} />
      </View>
      <View style={styles.analyzeButton}>
        {loading ? <ActivityIndicator /> : <Button title="Analiz Et" onPress={runAnalysis} />}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 24,
    gap: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
  },
  subtitle: {
    fontSize: 16,
    color: '#555',
  },
  previewBox: {
    flex: 1,
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: '#bbb',
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  preview: {
    width: '100%',
    height: '100%',
  },
  buttons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  analyzeButton: {
    paddingBottom: 12,
  },
});

export default AnalyzeScreen;

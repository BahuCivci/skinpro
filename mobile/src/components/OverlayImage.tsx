import React from 'react';
import { ImageBackground, StyleSheet, Text, View } from 'react-native';

import type { DetectorRegion } from '@/types/api';

export type OverlayImageProps = {
  sourceUri: string;
  regions?: DetectorRegion[];
  imageSize?: { width: number; height: number };
};

export const OverlayImage: React.FC<OverlayImageProps> = ({ sourceUri, regions = [], imageSize }) => {
  const aspectRatio = imageSize ? imageSize.width / imageSize.height : 3 / 4;

  return (
    <View style={[styles.container, { aspectRatio }] }>
      <ImageBackground source={{ uri: sourceUri }} style={styles.image} resizeMode="cover">
        {regions.map((det, idx) => {
          const [x1, y1, x2, y2] = det.bbox;
          const left = `${x1 * 100}%`;
          const top = `${y1 * 100}%`;
          const width = `${(x2 - x1) * 100}%`;
          const height = `${(y2 - y1) * 100}%`;
          return (
            <View key={idx} style={[styles.box, { left, top, width, height }] }>
              <Text style={styles.label}>
                {det.label} {(det.confidence * 100).toFixed(0)}%
              </Text>
            </View>
          );
        })}
      </ImageBackground>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: '100%',
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: '#000',
  },
  image: {
    flex: 1,
  },
  box: {
    position: 'absolute',
    borderColor: 'red',
    borderWidth: 2,
    borderRadius: 4,
    justifyContent: 'flex-start',
  },
  label: {
    backgroundColor: 'rgba(255,0,0,0.7)',
    color: '#fff',
    fontSize: 12,
    paddingHorizontal: 4,
    paddingVertical: 2,
  },
});

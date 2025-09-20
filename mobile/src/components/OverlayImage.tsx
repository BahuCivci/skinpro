import React from 'react';
import { Image, ImageSourcePropType, StyleSheet, View } from 'react-native';

export type OverlayImageProps = {
  source: ImageSourcePropType;
  overlayBase64?: string;
};

export const OverlayImage: React.FC<OverlayImageProps> = ({ source, overlayBase64 }) => {
  return (
    <View style={styles.container}>
      <Image source={source} style={styles.image} resizeMode="contain" />
      {overlayBase64 ? (
        <Image source={{ uri: `data:image/png;base64,${overlayBase64}` }} style={[styles.image, styles.overlay]} resizeMode="contain" />
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'relative',
    width: '100%',
    aspectRatio: 3 / 4,
  },
  image: {
    width: '100%',
    height: '100%',
    borderRadius: 16,
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
  },
});

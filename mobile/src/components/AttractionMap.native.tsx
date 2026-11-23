import { StyleSheet, View } from 'react-native';
import MapView, { Marker } from 'react-native-maps';

import { radii } from '@/design-system';

import type { AttractionMapProps } from './AttractionMap.types';

export function AttractionMap({ latitude, longitude, title, description }: AttractionMapProps) {
  return (
    <View style={styles.frame}>
      <MapView
        style={styles.map}
        initialRegion={{
          latitude,
          longitude,
          latitudeDelta: 0.012,
          longitudeDelta: 0.012,
        }}
      >
        <Marker coordinate={{ latitude, longitude }} title={title} description={description} />
      </MapView>
    </View>
  );
}

const styles = StyleSheet.create({
  frame: { width: '100%', height: 220, borderRadius: radii.lg, overflow: 'hidden' },
  map: { width: '100%', height: '100%' },
});

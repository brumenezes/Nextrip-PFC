import { StatusBar } from 'expo-status-bar';
import { useEffect, useMemo, useState } from 'react';
import {
  Animated,
  Easing,
  Image,
  StyleSheet,
  Text,
  useWindowDimensions,
  type ImageSourcePropType,
} from 'react-native';
import Svg, {
  Circle,
  Defs,
  LinearGradient,
  Path,
  RadialGradient,
  Stop,
} from 'react-native-svg';

const AnimatedPath = Animated.createAnimatedComponent(Path);

const VIEWBOX_WIDTH = 852;
const VIEWBOX_HEIGHT = 1847;
const TEAL = '#18DCC8';
const BACKGROUND_TOP = '#03223A';
const BACKGROUND_BOTTOM = '#021C30';
const ROUTE_PATH = 'M90 1450 C180 1300 300 1200 430 1230 C560 1260 650 1180 760 1120';
const STEPS = 40;
const PLANE_SIZE = 44;
const MARK_SIZE = 16;
const PIN_WIDTH = 36;
const PIN_HEIGHT = 46;
const PLANE_PATH =
  'M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z';
const LOADING_DOTS = [
  { x: 378, diameter: 16 },
  { x: 426, diameter: 26 },
  { x: 474, diameter: 16 },
];
const LOGO = require('../../assets/nextrip-logo.png') as ImageSourcePropType;

type Point = readonly [number, number];
type Segment = readonly [Point, Point, Point, Point];

const FIRST_SEGMENT: Segment = [[90, 1450], [180, 1300], [300, 1200], [430, 1230]];
const SECOND_SEGMENT: Segment = [[430, 1230], [560, 1260], [650, 1180], [760, 1120]];
const SEGMENTS: readonly Segment[] = [FIRST_SEGMENT, SECOND_SEGMENT];

type AnimatedSplashProps = {
  ready: boolean;
  minDuration?: number;
  onFinish: () => void;
};

function bezier(p0: Point, p1: Point, p2: Point, p3: Point, t: number): Point {
  const inverse = 1 - t;
  return [
    inverse ** 3 * p0[0] + 3 * inverse ** 2 * t * p1[0] + 3 * inverse * t ** 2 * p2[0] + t ** 3 * p3[0],
    inverse ** 3 * p0[1] + 3 * inverse ** 2 * t * p1[1] + 3 * inverse * t ** 2 * p2[1] + t ** 3 * p3[1],
  ];
}

const ROUTE = (() => {
  const points: Point[] = [];
  SEGMENTS.forEach((segment, segmentIndex) => {
    for (let step = 0; step < STEPS; step += 1) {
      points.push(bezier(segment[0], segment[1], segment[2], segment[3], step / STEPS));
    }
    if (segmentIndex === SEGMENTS.length - 1) points.push(segment[3]);
  });

  const cumulative = [0];
  for (let index = 1; index < points.length; index += 1) {
    const current = points[index]!;
    const previous = points[index - 1]!;
    cumulative.push(
      cumulative[index - 1]!
      + Math.hypot(current[0] - previous[0], current[1] - previous[1]),
    );
  }

  const length = cumulative[cumulative.length - 1]!;
  const fractions = cumulative.map((distance) => distance / length);
  const angles = points.map((_, index) => {
    const previous = points[Math.max(index - 1, 0)]!;
    const next = points[Math.min(index + 1, points.length - 1)]!;
    return (Math.atan2(next[1] - previous[1], next[0] - previous[0]) * 180) / Math.PI + 90;
  });

  return { points, fractions, angles, length, middleFraction: fractions[STEPS]! };
})();

const WAYPOINT_START = FIRST_SEGMENT[0];
const WAYPOINT_MIDDLE = FIRST_SEGMENT[3];
const WAYPOINT_END = SECOND_SEGMENT[3];

export function AnimatedSplash({ ready, minDuration = 2400, onFinish }: AnimatedSplashProps) {
  const { width, height } = useWindowDimensions();
  const scale = Math.max(width / VIEWBOX_WIDTH, height / VIEWBOX_HEIGHT);
  const offsetX = (width - VIEWBOX_WIDTH * scale) / 2;
  const offsetY = (height - VIEWBOX_HEIGHT * scale) / 2;
  const [trip] = useState(() => new Animated.Value(0));
  const [routeOpacity] = useState(() => new Animated.Value(1));
  const [dotAnimations] = useState(() => LOADING_DOTS.map(() => new Animated.Value(0)));
  const [splashOpacity] = useState(() => new Animated.Value(1));
  const [minimumDurationPassed, setMinimumDurationPassed] = useState(false);

  useEffect(() => {
    const animations: Animated.CompositeAnimation[] = [
      Animated.loop(
        Animated.sequence([
          Animated.parallel([
            Animated.timing(routeOpacity, { toValue: 1, duration: 0, useNativeDriver: true }),
            Animated.timing(trip, { toValue: 0, duration: 0, useNativeDriver: false }),
          ]),
          Animated.timing(trip, {
            toValue: 1,
            duration: 3800,
            easing: Easing.inOut(Easing.cubic),
            useNativeDriver: false,
          }),
          Animated.delay(900),
          Animated.timing(routeOpacity, { toValue: 0, duration: 450, useNativeDriver: true }),
          Animated.delay(150),
        ]),
      ),
      ...dotAnimations.map((animation, index) =>
        Animated.loop(
          Animated.sequence([
            Animated.delay(index * 200),
            Animated.timing(animation, { toValue: 1, duration: 300, useNativeDriver: true }),
            Animated.timing(animation, { toValue: 0, duration: 300, useNativeDriver: true }),
            Animated.delay((2 - index) * 200),
          ]),
        )),
    ];

    animations.forEach((animation) => animation.start());
    const timer = setTimeout(() => setMinimumDurationPassed(true), minDuration);

    return () => {
      clearTimeout(timer);
      animations.forEach((animation) => animation.stop());
    };
  }, [dotAnimations, minDuration, routeOpacity, trip]);

  useEffect(() => {
    if (!ready || !minimumDurationPassed) return;

    Animated.timing(splashOpacity, {
      toValue: 0,
      duration: 450,
      useNativeDriver: true,
    }).start(({ finished }) => {
      if (finished) onFinish();
    });
  }, [minimumDurationPassed, onFinish, ready, splashOpacity]);

  const pointX = (x: number) => offsetX + x * scale;
  const pointY = (y: number) => offsetY + y * scale;
  const dashOffset = trip.interpolate({
    inputRange: [0, 1],
    outputRange: [ROUTE.length + 4, 0],
  });
  const planeStyle = useMemo(
    () => ({
      opacity: trip.interpolate({
        inputRange: [0, 0.02, 0.96, 1],
        outputRange: [0, 1, 1, 0],
      }),
      transform: [
        {
          translateX: trip.interpolate({
            inputRange: ROUTE.fractions,
            outputRange: ROUTE.points.map((point) => offsetX + point[0] * scale - PLANE_SIZE / 2),
          }),
        },
        {
          translateY: trip.interpolate({
            inputRange: ROUTE.fractions,
            outputRange: ROUTE.points.map((point) => offsetY + point[1] * scale - PLANE_SIZE / 2),
          }),
        },
        {
          rotate: trip.interpolate({
            inputRange: ROUTE.fractions,
            outputRange: ROUTE.angles.map((angle) => `${angle}deg`),
          }),
        },
      ],
    }),
    [offsetX, offsetY, scale, trip],
  );
  const startStyle = {
    opacity: trip.interpolate({ inputRange: [0, 0.02], outputRange: [0, 1], extrapolate: 'clamp' }),
    transform: [{ scale: trip.interpolate({ inputRange: [0, 0.05], outputRange: [0.3, 1], extrapolate: 'clamp' }) }],
  };
  const middleStyle = {
    opacity: trip.interpolate({
      inputRange: [ROUTE.middleFraction - 0.02, ROUTE.middleFraction + 0.01],
      outputRange: [0, 1],
      extrapolate: 'clamp',
    }),
    transform: [{
      scale: trip.interpolate({
        inputRange: [ROUTE.middleFraction - 0.02, ROUTE.middleFraction + 0.04],
        outputRange: [0.3, 1],
        extrapolate: 'clamp',
      }),
    }],
  };
  const destinationStyle = {
    opacity: trip.interpolate({ inputRange: [0.93, 1], outputRange: [0, 1], extrapolate: 'clamp' }),
    transform: [{
      translateY: trip.interpolate({ inputRange: [0.93, 1], outputRange: [-10, 0], extrapolate: 'clamp' }),
    }],
  };
  const layer = { position: 'absolute' as const, inset: 0, width, height };
  const svgProps = {
    width,
    height,
    viewBox: `0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`,
    preserveAspectRatio: 'xMidYMid slice',
  };
  const logoSize = 350 * scale;

  return (
    <Animated.View
      accessibilityLabel="Nextrip carregando"
      accessibilityRole="progressbar"
      style={[styles.root, { width, height, opacity: splashOpacity }]}
    >
      <StatusBar style="light" />
      <Svg {...svgProps} style={layer}>
        <Defs>
          <LinearGradient id="splashBackground" x1="0" y1="0" x2="0" y2="1">
            <Stop offset="0" stopColor={BACKGROUND_TOP} />
            <Stop offset="1" stopColor={BACKGROUND_BOTTOM} />
          </LinearGradient>
          <RadialGradient id="topGlow" cx="0.3" cy="0.3" r="0.8">
            <Stop offset="0" stopColor={TEAL} stopOpacity="0.28" />
            <Stop offset="1" stopColor={TEAL} stopOpacity="0" />
          </RadialGradient>
          <RadialGradient id="bottomGlow" cx="0.7" cy="0.7" r="0.8">
            <Stop offset="0" stopColor={TEAL} stopOpacity="0.28" />
            <Stop offset="1" stopColor={TEAL} stopOpacity="0" />
          </RadialGradient>
        </Defs>
        <Path d={`M0 0 H${VIEWBOX_WIDTH} V${VIEWBOX_HEIGHT} H0 Z`} fill="url(#splashBackground)" />
        <Circle cx={-60} cy={-60} r={420} fill="url(#topGlow)" stroke={TEAL} strokeOpacity={0.3} strokeWidth={2} />
        <Circle cx={1000} cy={1930} r={560} fill="url(#bottomGlow)" stroke={TEAL} strokeOpacity={0.3} strokeWidth={2} />
      </Svg>

      <Image
        accessibilityIgnoresInvertColors
        resizeMode="cover"
        source={LOGO}
        style={[
          styles.logo,
          {
            width: logoSize,
            height: logoSize,
            left: width / 2 - logoSize / 2,
            top: pointY(750) - logoSize / 2,
          },
        ]}
      />
      <Text style={[styles.brandName, { top: pointY(960), fontSize: 62 * scale, lineHeight: 76 * scale }]}>nextrip</Text>

      <Animated.View pointerEvents="none" style={[layer, { opacity: routeOpacity }]}>
        <Svg {...svgProps} style={layer}>
          <Path d={ROUTE_PATH} stroke={TEAL} strokeOpacity={0.25} strokeWidth={2} strokeDasharray="12 12" fill="none" />
          <AnimatedPath
            d={ROUTE_PATH}
            stroke={TEAL}
            strokeOpacity={0.18}
            strokeWidth={14}
            strokeLinecap="round"
            strokeDasharray={`${ROUTE.length + 4} ${ROUTE.length + 4}`}
            strokeDashoffset={dashOffset}
            fill="none"
          />
          <AnimatedPath
            d={ROUTE_PATH}
            stroke={TEAL}
            strokeWidth={4}
            strokeDasharray={`${ROUTE.length + 4} ${ROUTE.length + 4}`}
            strokeDashoffset={dashOffset}
            fill="none"
          />
        </Svg>

        <Animated.View
          style={[
            styles.mark,
            { left: pointX(WAYPOINT_START[0]) - MARK_SIZE / 2, top: pointY(WAYPOINT_START[1]) - MARK_SIZE / 2 },
            startStyle,
          ]}
        />
        <Animated.View
          style={[
            styles.mark,
            { left: pointX(WAYPOINT_MIDDLE[0]) - MARK_SIZE / 2, top: pointY(WAYPOINT_MIDDLE[1]) - MARK_SIZE / 2 },
            middleStyle,
          ]}
        />
        <Animated.View
          style={[
            styles.pin,
            { left: pointX(WAYPOINT_END[0]) - PIN_WIDTH / 2, top: pointY(WAYPOINT_END[1]) - PIN_HEIGHT },
            destinationStyle,
          ]}
        >
          <Svg width={PIN_WIDTH} height={PIN_HEIGHT} viewBox="0 0 36 46">
            <Path
              d="M18 44 C18 44 3 28 3 17 A15 15 0 0 1 33 17 C33 28 18 44 18 44 Z"
              stroke={TEAL}
              strokeWidth={3.5}
              fill="none"
              strokeLinejoin="round"
            />
            <Circle cx={18} cy={17} r={5} fill={TEAL} />
          </Svg>
        </Animated.View>
        <Animated.View style={[styles.plane, planeStyle]}>
          <Svg width={PLANE_SIZE} height={PLANE_SIZE} viewBox="0 0 24 24">
            <Path d={PLANE_PATH} fill={TEAL} />
          </Svg>
        </Animated.View>
      </Animated.View>

      {LOADING_DOTS.map((dot, index) => {
        const animation = dotAnimations[index]!;
        return (
          <Animated.View
            key={dot.x}
            pointerEvents="none"
            style={{
              position: 'absolute',
              left: pointX(dot.x) - (dot.diameter * scale) / 2,
              top: pointY(1553) - (dot.diameter * scale) / 2,
              width: dot.diameter * scale,
              height: dot.diameter * scale,
              borderRadius: (dot.diameter * scale) / 2,
              backgroundColor: TEAL,
              opacity: animation.interpolate({ inputRange: [0, 1], outputRange: [0.3, 1] }),
              transform: [{
                scale: animation.interpolate({ inputRange: [0, 1], outputRange: [0.75, 1.25] }),
              }],
            }}
          />
        );
      })}
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: BACKGROUND_TOP,
    overflow: 'hidden',
  },
  logo: {
    position: 'absolute',
    borderRadius: 28,
  },
  brandName: {
    position: 'absolute',
    left: 0,
    width: '100%',
    color: '#FFFFFF',
    fontFamily: 'Inter_700Bold',
    letterSpacing: 1.5,
    textAlign: 'center',
  },
  plane: {
    position: 'absolute',
    left: 0,
    top: 0,
    width: PLANE_SIZE,
    height: PLANE_SIZE,
  },
  mark: {
    position: 'absolute',
    width: MARK_SIZE,
    height: MARK_SIZE,
    borderRadius: MARK_SIZE / 2,
    backgroundColor: BACKGROUND_TOP,
    borderWidth: 3,
    borderColor: TEAL,
  },
  pin: {
    position: 'absolute',
  },
});

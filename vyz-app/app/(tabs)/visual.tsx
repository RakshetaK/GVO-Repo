import React, { useMemo, useRef, useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  Image,
  TouchableOpacity,
  Animated,
  PanResponder,
} from "react-native";
import { useRouter } from "expo-router";
import AsyncStorage from "@react-native-async-storage/async-storage";
import Icon from "../../components/Icon";
import Svg, { Circle } from "react-native-svg";
import { Ionicons } from "@expo/vector-icons"; // ← added

const icons = {
  mindfulness: require("../../assets/mindfulness-icon.png"),
  audio: require("../../assets/audio-icon.png"),
  visual: require("../../assets/visual-icon.png"),
  settings: require("../../assets/setting-icon.png"),
  avatar: require("../../assets/profile.png"),
  brightness: require("../../assets/brightness-icon.png"),
};

type Tab = "mindfulness" | "audio" | "visual" | "settings";

export default function VisualScreen() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>("visual");
  const dotLeft = useRef(new Animated.Value(216)).current;

  const animateAndNavigate = (tab: Tab, toPosition: number, route: string) => {
    setActiveTab(tab);

    Animated.timing(dotLeft, {
      // or dotPosition - match your variable name
      toValue: toPosition,
      duration: 300,
      useNativeDriver: false,
    }).start(() => {
      router.replace(route); // Navigate AFTER animation completes
    });
  };

  // ---- brightness value (0..100)
  const [brightness, setBrightness] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  // Load saved brightness value on mount
  useEffect(() => {
    loadBrightness();
  }, []);

  // Save brightness value whenever it changes
  useEffect(() => {
    if (!isLoading) {
      saveBrightness();
    }
  }, [brightness, isLoading]);

  const loadBrightness = async () => {
    try {
      const savedValue = await AsyncStorage.getItem("@brightness_value");
      if (savedValue !== null) {
        setBrightness(parseFloat(savedValue));
      }
    } catch (error) {
      console.error("Error loading brightness:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveBrightness = async () => {
    try {
      await AsyncStorage.setItem("@brightness_value", brightness.toString());
    } catch (error) {
      console.error("Error saving brightness:", error);
    }
  };

  const NUM_SEGS = 8;
  const SEG_H = 30; // bar height
  const SEG_W = 55; // bar width
  const SEG_GAP = 4; // gap between segments
  const SLIDER_HEIGHT = SEG_H * NUM_SEGS + SEG_GAP * (NUM_SEGS - 1); // total height with gaps

  // PanResponder: use local Y inside the hitbox
  const pan = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderGrant: (evt) => updateFromLocal(evt.nativeEvent.locationY),
      onPanResponderMove: (evt) => updateFromLocal(evt.nativeEvent.locationY),
    })
  ).current;

  function clamp(n: number, min: number, max: number) {
    return Math.max(min, Math.min(max, n));
  }

  function updateFromLocal(localY: number) {
    const y = clamp(localY, 0, SLIDER_HEIGHT);

    // OPTION 4: Custom range (e.g., 15% to 85%)
    const minPercent = 15;
    const maxPercent = 100;
    const range = maxPercent - minPercent;
    const pct = maxPercent - Math.round((y / SLIDER_HEIGHT) * range);

    setBrightness(pct);
  }

  // filled segments (from bottom up)
  const filledCount = useMemo(
    () => Math.round((brightness / 100) * NUM_SEGS),
    [brightness]
  );

  // Arc math
  const radius = 185;
  const strokeWidth = 38;
  const circumference = 2 * Math.PI * radius;

  // We draw a 270° arc (75% of full circle)
  const ARC_PCT = 0.75; // 270 / 360
  const START_AT_DEG = 15; // top-left
  const START_OFFSET = (START_AT_DEG / 360) * circumference;

  // Blue length grows 0..270° with brightness
  const arcLength = useMemo(
    () => (brightness / 100) * ARC_PCT * circumference,
    [brightness, circumference]
  );

  return (
    <View style={styles.container}>
      {/* background + welcome card */}
      <View style={styles.background} />
      <View style={styles.headerShadow} />
      <View style={styles.header} />

      {/* Avatar + greeting (fixed positions) */}
      <Image source={icons.avatar} style={styles.avatarAbs} />
      <Text style={styles.greetingAbs}>Welcome, Krish</Text>

      {/* ← back chevron to login */}
      <TouchableOpacity
        style={styles.backButton}
        onPress={() => router.push("/")}
      >
        <Ionicons name="chevron-back" size={28} color="white" />
      </TouchableOpacity>

      {/* Titles */}
      <Text style={styles.title}>Visual</Text>
      <Text style={styles.subtitle}>Brightness</Text>
      <Text style={styles.description}>
        Adjust the amount which your visual surroundings will be darkened
      </Text>

      {/* ARC CIRCLE with progressive fill */}
      <View style={styles.circleContainer}>
        <Svg width={408} height={408} style={styles.svgCircle}>
          {/* Gray background arc: 270° starting at top-left */}
          <Circle
            cx={204}
            cy={204}
            r={radius}
            stroke="#E3E3E3"
            strokeWidth={strokeWidth}
            fill="none"
            strokeDasharray={`${ARC_PCT * circumference} ${circumference}`}
            strokeDashoffset={START_OFFSET}
            rotation="-90" // make 0° = top
            origin="204, 204"
          />
          {/* Blue arc that fills from bottom upward */}
          <Circle
            cx={204}
            cy={204}
            r={radius}
            stroke="#0F62FE"
            strokeWidth={strokeWidth}
            fill="none"
            strokeDasharray={`0 ${
              ARC_PCT * circumference - arcLength
            } ${arcLength}`}
            strokeDashoffset={START_OFFSET}
            rotation="-90"
            origin="204, 204"
            strokeLinecap="butt"
          />
        </Svg>
      </View>

      {/* inner white circle on top */}
      <View style={styles.circleInner} />

      {/* brightness pictogram */}
      <Image source={icons.brightness} style={styles.brightnessIcon} />

      {/* Brightness percentage display */}
      <Text style={styles.brightnessPercent}>{Math.round(brightness)}%</Text>

      {/* RIGHT VERTICAL SLIDER with gaps between segments */}
      <View style={styles.sliderHitbox} {...pan.panHandlers}>
        {Array.from({ length: NUM_SEGS }, (_, i) => {
          const idxFromBottom = NUM_SEGS - 1 - i;
          const filled = idxFromBottom < filledCount;
          const isTop = i === 0;
          const isBottom = i === NUM_SEGS - 1;
          return (
            <View
              key={i}
              style={[
                styles.seg,
                {
                  top: i * (SEG_H + SEG_GAP),
                  backgroundColor: filled ? "#0F62FE" : "#E3E3E3",
                  borderTopLeftRadius: isTop ? 10 : 0,
                  borderTopRightRadius: isTop ? 10 : 0,
                  borderBottomLeftRadius: isBottom ? 10 : 0,
                  borderBottomRightRadius: isBottom ? 10 : 0,
                },
              ]}
            />
          );
        })}
      </View>

      {/* Bottom Navigation Bar */}
      <View style={styles.navBar}>
        <Animated.View style={[styles.activePill, { left: dotLeft }]} />

        <TouchableOpacity
          style={[styles.navBtn, { left: 48 }]}
          onPress={() =>
            animateAndNavigate("mindfulness", 37, "/(tabs)/mindfulness")
          }
        >
          <Icon
            source={icons.mindfulness}
            size={32}
            tint={activeTab === "mindfulness" ? "#fff" : "#000"}
          />
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.navBtn, { left: 143 }]}
          onPress={() => animateAndNavigate("audio", 132, "/(tabs)/audio")}
        >
          <Icon
            source={icons.audio}
            size={32}
            tint={activeTab === "audio" ? "#fff" : "#000"}
          />
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.navBtn, { left: 227 }]}
          onPress={() => {
            // Already on visual, do nothing
          }}
        >
          <Icon
            source={icons.visual}
            size={32}
            tint={activeTab === "visual" ? "#fff" : "#000"}
          />
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.navBtn, { left: 311 }]}
          onPress={() =>
            animateAndNavigate("settings", 300, "/(tabs)/settings")
          }
        >
          <Icon
            source={icons.settings}
            size={32}
            tint={activeTab === "settings" ? "#fff" : "#000"}
          />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: 402,
    height: 874,
    position: "relative",
    overflow: "hidden",
    backgroundColor: "white",
  },
  background: {
    width: 402,
    height: 874,
    position: "absolute",
    left: 0,
    top: 0,
    backgroundColor: "white",
  },

  // Welcome card
  headerShadow: {
    width: 425.38,
    height: 184.5,
    position: "absolute",
    left: -21,
    top: -22,
    backgroundColor: "white",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
    borderRadius: 20,
  },
  header: {
    width: 415,
    height: 180,
    position: "absolute",
    left: -13,
    top: -20,
    backgroundColor: "#0F62FE",
    borderRadius: 20,
  },
  avatarAbs: {
    position: "absolute",
    left: 21,
    top: 92,
    width: 50,
    height: 50,
    borderRadius: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 3,
    zIndex: 20,
  },
  greetingAbs: {
    position: "absolute",
    left: 80,
    top: 104,
    color: "white",
    fontSize: 20,
    fontFamily: "BaiJamjuree-Regular",
    zIndex: 20,
  },

  // ← added
  backButton: {
    position: "absolute",
    left: 350,
    top: 95,
    width: 40,
    height: 40,
    justifyContent: "center",
    alignItems: "center",
    zIndex: 20,
  },

  title: {
    position: "absolute",
    left: 21,
    top: 180,
    color: "#161515",
    fontSize: 24,
    fontFamily: "Gravity-Bold",
  },
  subtitle: {
    position: "absolute",
    left: 21,
    top: 214,
    color: "#161515",
    fontSize: 20,
    fontFamily: "Gravity-Regular",
  },
  description: {
    position: "absolute",
    left: 21,
    top: 243,
    width: 336,
    color: "#161515",
    fontSize: 11,
    fontFamily: "Gravity-Regular",
    fontWeight: "350",
  },

  // Circle container for SVG
  circleContainer: {
    position: "absolute",
    left: -224,
    top: 314,
    width: 408,
    height: 408,
  },
  svgCircle: {
    position: "absolute",
    left: 0,
    top: 0,
  },

  // white inner circle (332x332)
  circleInner: {
    position: "absolute",
    left: -186,
    top: 352,
    width: 332,
    height: 332,
    borderRadius: 166,
    backgroundColor: "white",
  },

  // Brightness pictogram
  brightnessIcon: {
    position: "absolute",
    left: 21,
    top: 435,
    width: 81,
    height: 81,
    resizeMode: "contain",
    tintColor: "#0F62FE",
  },

  // Brightness percentage text
  brightnessPercent: {
    position: "absolute",
    left: 39,
    top: 533,
    fontSize: 24,
    fontFamily: "BaiJamjuree-Regular",
    color: "#0F62FE",
  },

  // Vertical slider area with gaps
  sliderHitbox: {
    position: "absolute",
    left: 270,
    top: 384,
    width: 55,
    height: 268,
    zIndex: 30,
  },

  // Each segment
  seg: {
    position: "absolute",
    left: 0,
    width: 55,
    height: 30,
  },

  // Navbar with active blue pill
  navBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    paddingVertical: 45,
    backgroundColor: "#fff",
    borderTopWidth: 0,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 10,
    zIndex: 20,
  },
  activePill: {
    position: "absolute",
    top: 18,
    width: 54,
    height: 54,
    borderRadius: 27,
    backgroundColor: "#0F62FE",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 6,
    zIndex: 20,
  },
  navBtn: {
    position: "absolute",
    top: 28,
    width: 32,
    height: 32,
    justifyContent: "center",
    alignItems: "center",
    zIndex: 25,
  },
});

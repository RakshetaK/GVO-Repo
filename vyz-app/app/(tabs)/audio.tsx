import React, { useState, useRef, useEffect } from "react";
import {
  StyleSheet,
  View,
  Text,
  Image,
  TouchableOpacity,
  ScrollView,
  Animated,
} from "react-native";
import Slider from "@react-native-community/slider";
import { Ionicons, Feather } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import AsyncStorage from "@react-native-async-storage/async-storage";
import Icon from "../../components/Icon";

const icons = {
  mindfulness: require("../../assets/mindfulness-icon.png"),
  audio: require("../../assets/audio-icon.png"),
  visual: require("../../assets/visual-icon.png"),
  settings: require("../../assets/setting-icon.png"),
  avatar: require("../../assets/profile.png"),
};

const soothingSounds = [
  { id: "1", title: "White Noise" },
  { id: "2", title: "Ocean Waves" },
  { id: "3", title: "Gentle Rain" },
  { id: "4", title: "Brown Noise" },
  { id: "5", title: "Sunday Sunshine" },
  { id: "6", title: "Calming Crickets" },
  { id: "7", title: "Forest Wind" },
  { id: "8", title: "Fireplace Crackle" },
  { id: "9", title: "Soft Piano" },
];

export default function AudioScreen() {
  const router = useRouter();
  const [noiseSuppression, setNoiseSuppression] = useState(0.5);
  const [activeTab, setActiveTab] = useState("audio");
  const [playingStates, setPlayingStates] = useState<{
    [key: string]: boolean;
  }>({});
  const [isLoading, setIsLoading] = useState(true);
  const dotPosition = useRef(new Animated.Value(132)).current;

  // Load saved values on mount
  useEffect(() => {
    loadSavedValues();
  }, []);

  // Save noise suppression value whenever it changes
  useEffect(() => {
    if (!isLoading) {
      saveNoiseSuppressionValue();
    }
  }, [noiseSuppression, isLoading]);

  // Save playing states whenever they change
  useEffect(() => {
    if (!isLoading) {
      savePlayingStates();
    }
  }, [playingStates, isLoading]);

  const loadSavedValues = async () => {
    try {
      // Load noise suppression value
      const savedNoiseValue = await AsyncStorage.getItem(
        "@noise_suppression_value"
      );
      if (savedNoiseValue !== null) {
        setNoiseSuppression(parseFloat(savedNoiseValue));
      }

      // Load playing states
      const savedPlayingStates = await AsyncStorage.getItem("@playing_states");
      if (savedPlayingStates !== null) {
        setPlayingStates(JSON.parse(savedPlayingStates));
      }
    } catch (error) {
      console.error("Error loading saved values:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveNoiseSuppressionValue = async () => {
    try {
      await AsyncStorage.setItem(
        "@noise_suppression_value",
        noiseSuppression.toString()
      );
    } catch (error) {
      console.error("Error saving noise suppression:", error);
    }
  };

  const savePlayingStates = async () => {
    try {
      await AsyncStorage.setItem(
        "@playing_states",
        JSON.stringify(playingStates)
      );
    } catch (error) {
      console.error("Error saving playing states:", error);
    }
  };

  const animateAndNavigate = (
    tab: string,
    toPosition: number,
    route: string
  ) => {
    setActiveTab(tab);

    // Animate the dot
    Animated.timing(dotPosition, {
      toValue: toPosition,
      duration: 300,
      useNativeDriver: false,
    }).start(() => {
      // Navigate after animation completes
      router.push(route);
    });
  };

  const togglePlayPause = (soundId: string) => {
    setPlayingStates((prev) => ({
      ...prev,
      [soundId]: !prev[soundId],
    }));
  };

  return (
    <View style={styles.container}>
      <View style={styles.background} />
      <View style={styles.headerShadow} />
      <View style={styles.header} />

      {/* Avatar and greeting - absolute positioned like mindfulness */}
      <Image source={icons.avatar} style={styles.avatarAbs} />
      <Text style={styles.greetingAbs}>Welcome, Krish</Text>

      {/* Back button */}
      <TouchableOpacity
        style={styles.backButton}
        onPress={() => router.push("/")}
      >
        <Ionicons name="chevron-back" size={28} color="white" />
      </TouchableOpacity>

      {/* Scrollable content */}
      <ScrollView
        style={styles.scrollContainer}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.title}>Audio</Text>

        {/* Noise Suppression Section */}
        <View style={styles.section}>
          <Text style={styles.subTitle}>Noise Suppression</Text>
          <Text style={styles.description}>
            Adjust the amount which your auditory surroundings will be muffled
          </Text>

          <Slider
            style={styles.slider}
            minimumValue={0}
            maximumValue={1}
            value={noiseSuppression}
            onValueChange={(value) => setNoiseSuppression(value)}
            minimumTrackTintColor="#0F62FE"
            maximumTrackTintColor="#ccc"
            thumbTintColor="#0F62FE"
          />

          <Text style={styles.sliderValue}>
            {Math.round(noiseSuppression * 100)}%
          </Text>
        </View>

        {/* Soothing Sounds */}
        <View style={styles.section}>
          <Text style={styles.subTitle}>Soothing Sounds</Text>
          <Text style={styles.description}>
            Pick a soothing sound from a playlist of noise types, or listen to a
            snippet of audio by clicking the volume icon
          </Text>

          {soothingSounds.map((item) => (
            <View key={item.id} style={styles.soundItem}>
              <TouchableOpacity
                style={styles.soundButton}
                onPress={() => togglePlayPause(item.id)}
              >
                <Ionicons
                  name={playingStates[item.id] ? "pause-circle" : "play-circle"}
                  size={24}
                  color="white"
                />
                <Text style={styles.soundText}>{item.title}</Text>
              </TouchableOpacity>
              <TouchableOpacity>
                <Feather name="volume-2" size={20} color="white" />
              </TouchableOpacity>
            </View>
          ))}
        </View>
      </ScrollView>

      {/* Bottom Navigation Bar - matching mindfulness */}
      <View style={styles.navBar}>
        <Animated.View style={[styles.activeCircle, { left: dotPosition }]} />

        <TouchableOpacity
          style={[styles.navButton, { left: 48 }]}
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
          style={[styles.navButton, { left: 143 }]}
          onPress={() => {
            // Already on audio, do nothing
          }}
        >
          <Icon
            source={icons.audio}
            size={32}
            tint={activeTab === "audio" ? "#fff" : "#000"}
          />
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.navButton, { left: 227 }]}
          onPress={() => animateAndNavigate("visual", 216, "/(tabs)/visual")}
        >
          <Icon
            source={icons.visual}
            size={32}
            tint={activeTab === "visual" ? "#fff" : "#000"}
          />
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.navButton, { left: 311 }]}
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
  scrollContainer: {
    position: "absolute",
    top: 160,
    left: 0,
    right: 0,
    bottom: 80,
  },
  scrollContent: {
    paddingTop: 20,
    paddingBottom: 20,
    paddingHorizontal: 21,
  },
  title: {
    marginBottom: 8,
    color: "#161515",
    fontSize: 24,
    fontFamily: "Gravity-Bold",
  },
  section: {
    marginTop: 12,
  },
  subTitle: {
    fontSize: 20,
    fontFamily: "Gravity-Regular",
    marginBottom: 8,
    color: "#161515",
  },
  description: {
    color: "#161515",
    fontSize: 11,
    fontFamily: "Gravity-Regular",
    fontWeight: "350",
    marginBottom: 15,
  },
  slider: {
    width: "100%",
    height: 40,
  },
  sliderValue: {
    fontSize: 16,
    fontWeight: "600",
    color: "#161515",
    textAlign: "center",
    marginTop: 5,
  },
  soundItem: {
    backgroundColor: "#0F62FE",
    padding: 15,
    marginVertical: 5,
    borderRadius: 8,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 3,
    elevation: 2,
  },
  soundButton: {
    flexDirection: "row",
    alignItems: "center",
  },
  soundText: {
    color: "white",
    fontSize: 16,
    marginLeft: 10,
  },
  navBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: "row",
    justifyContent: "space-around",
    alignItems: "center",
    paddingVertical: 45,
    backgroundColor: "#fff",
    borderTopWidth: 0,
    borderTopColor: "#fff",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 10,
    zIndex: 20,
  },
  navButton: {
    position: "absolute",
    padding: 8,
    justifyContent: "center",
    alignItems: "center",
    width: 32,
    height: 32,
    top: 28,
    zIndex: 25,
  },
  activeCircle: {
    width: 54,
    height: 54,
    position: "absolute",
    top: 18,
    backgroundColor: "#0F62FE",
    borderRadius: 27,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 6,
    zIndex: 20,
  },
});

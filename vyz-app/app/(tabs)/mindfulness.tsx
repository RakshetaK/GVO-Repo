import { View, Text, StyleSheet, Pressable, Image, TouchableOpacity, ScrollView, Animated } from "react-native";
import { useRouter } from "expo-router";
import { useState, useRef } from "react";
import Icon from "../../components/Icon";

// Assets
const icons = {
  mindfulness: require("../../assets/mindfulness-icon.png"),
  audio: require("../../assets/audio-icon.png"),
  visual: require("../../assets/visual-icon.png"),
  settings: require("../../assets/setting-icon.png"),
  calm: require("../../assets/calm-icon.png"),
  avatar: require("../../assets/profile.png"),
};

const cardPositions = [
  { left: 21, top: 110, width: 170 },
  { left: 212, top: 110, width: 169 },
  { left: 21, top: 302, width: 170 },
  { left: 212, top: 302, width: 169 },
  { left: 21, top: 494, width: 170 },
  { left: 212, top: 494, width: 169 },
];

// Exercise name positions (relative to ScrollView)
const exercisesInScrollView = [
  { id: 1, name: "Box Breathing", left: 54, top: 243 },
  { id: 2, name: "Balloon Breathing", left: 229, top: 243 },
  { id: 3, name: "Wave Breathing", left: 47, top: 436 },
  { id: 4, name: "4-7-8 Breathing", left: 234, top: 436 },
  { id: 5, name: "Box Breathing", left: 54, top: 627 },
  { id: 6, name: "Balloon Breathing", left: 229, top: 627 },
];

export default function MindfulnessScreen() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("mindfulness");
  const dotPosition = useRef(new Animated.Value(48)).current; // Start at mindfulness position

  const animateAndNavigate = (tab: string, toPosition: number, route: string) => {
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

  return (
    <View style={styles.container}>
      <View style={styles.background} />
      <View style={styles.headerShadow} />

      {/* Header background only */}
      <View style={styles.header} />

      {/* Absolute-positioned avatar + greeting (screen coords) - STATIC */}
      <Image source={icons.avatar} style={styles.avatarAbs} />
      <Text style={styles.greetingAbs}>Welcome, Krish</Text>

      {/* SCROLLABLE CONTENT AREA */}
      <ScrollView 
        style={styles.scrollContainer}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Title + Subtitle - NOW SCROLLABLE */}
        <Text style={styles.title}>Mindfulness</Text>
        <Text style={styles.subtitle}>Breathing Exercises</Text>

        {/* Cards with CALM icon */}
        {cardPositions.map((pos, index) => (
          <Pressable key={index} style={[styles.card, pos]}>
            <Icon
              source={icons.calm}
              size={94}
              style={{ position: "absolute", left: (pos.width - 94) / 2, top: 22 }}
            />
          </Pressable>
        ))}

        {/* Exercise Names */}
        {exercisesInScrollView.map((exercise) => (
          <Text key={exercise.id} style={[styles.exerciseName, { left: exercise.left, top: exercise.top }]}>
            {exercise.name}
          </Text>
        ))}
      </ScrollView>

      {/* Bottom Navigation Bar - STATIC */}
      <View style={styles.navBar}>
        <Animated.View style={[styles.activeCircle, { left: dotPosition }]} />

        <TouchableOpacity
          style={[styles.navButton, { left: 48 }]}
          onPress={() => {
            // Already on mindfulness, do nothing
          }}
        >
          <Icon source={icons.mindfulness} size={32} tint={activeTab === "mindfulness" ? "#fff" : "#000"} />
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.navButton, { left: 143 }]}
          onPress={() => animateAndNavigate("audio", 132, "/(tabs)/audio")}
        >
          <Icon source={icons.audio} size={32} />
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.navButton, { left: 227 }]}
          onPress={() => animateAndNavigate("visual", 216, "/(tabs)/visual")}
        >
          <Icon source={icons.visual} size={32} />
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.navButton, { left: 311 }]}
          onPress={() => animateAndNavigate("settings", 300, "/(tabs)/settings")}
        >
          <Icon source={icons.settings} size={32} />
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
  
  // Scrollable content area - starts right after header
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
    minHeight: 650,
  },
  
  // Title and subtitle now inside ScrollView
  title: {
    paddingLeft: 21,
    marginBottom: 20,
    color: "#161515",
    fontSize: 24,
    fontFamily: "Gravity-Bold",
  },
  subtitle: {
    paddingLeft: 21,
    marginBottom: 20,
    color: "#161515",
    fontSize: 20,
    fontFamily: "Gravity-Regular",
  },
  
  card: {
    height: 174,
    position: "absolute",
    backgroundColor: "#0F62FE",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 3,
  },
  exerciseName: {
    position: "absolute",
    color: "white",
    fontSize: 16,
    fontFamily: "Gravity-Regular",
  },

  // NavBar
  navBar: {
    position: "absolute",
    bottom: 50,
    left: 0,
    right: 0,
    flexDirection: "row",
    justifyContent: "space-around",
    alignItems: "center",
    paddingVertical: 15,
    backgroundColor: "#fff",
    borderTopWidth: 1,
    borderTopColor: "#ccc",
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
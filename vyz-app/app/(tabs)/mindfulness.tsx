import { View, Text, StyleSheet, Pressable, Image } from "react-native";
import Icon from "../../components/Icon";

// Assets
const icons = {
  mindfulness: require("../../assets/mindfulness-icon.png"),
  audio: require("../../assets/audio-icon.png"),
  visual: require("../../assets/visual-icon.png"),
  settings: require("../../assets/vyz-logo.png"),
  calm: require("../../assets/calm-icon.png"),
  avatar: require("../../assets/profile.png"),
};

const breathingExercises = [
  { id: 1, name: "Box Breathing", left: 54, top: 424 },
  { id: 2, name: "Balloon Breathing", left: 229, top: 424 },
  { id: 3, name: "Wave Breathing", left: 47, top: 617 },
  { id: 4, name: "4-7-8 Breathing", left: 234, top: 617 },
  { id: 5, name: "Box Breathing", left: 54, top: 808 },
  { id: 6, name: "Balloon Breathing", left: 229, top: 808 },
];

const cardPositions = [
  { left: 21, top: 291, width: 170 },
  { left: 212, top: 291, width: 169 },
  { left: 21, top: 483, width: 170 },
  { left: 212, top: 483, width: 169 },
  { left: 21, top: 675, width: 170 },
  { left: 212, top: 675, width: 169 },
];

export default function MindfulnessScreen() {
  return (
    <View style={styles.container}>
      <View style={styles.background} />
      <View style={styles.headerShadow} />

      {/* Header */}
      <View style={styles.header}>
        <Image source={icons.avatar} style={styles.avatar} />
        <Text style={styles.greeting}>Welcome, Krish</Text>
      </View>

      {/* Title + Subtitle */}
      <Text style={styles.title}>Mindfulness</Text>
      <Text style={styles.subtitle}>Breathing Exercises</Text>

      {/* Cards with CALM icon */}
      {cardPositions.map((pos, index) => (
        <Pressable key={index} style={[styles.card, pos]}>
          <Icon
            source={icons.calm}
            size={94}
            style={{
              position: "absolute",
              left: (pos.width - 94) / 2,
              top: 22,
            }}
          />
        </Pressable>
      ))}

      {/* Exercise Names */}
      {breathingExercises.map((exercise) => (
        <Text
          key={exercise.id}
          style={[
            styles.exerciseName,
            { left: exercise.left, top: exercise.top },
          ]}
        >
          {exercise.name}
        </Text>
      ))}

      {/* Bottom Navigation */}
      <View style={styles.bottomNav}>
        <View style={styles.activeCircle} />

        {/* ORDER: mindfulness, audio, visual, settings */}
        <Pressable style={[styles.navIcon, { left: 59 }]}>
          <Icon source={icons.mindfulness} size={32} />
        </Pressable>

        <Pressable style={[styles.navIcon, { left: 143 }]}>
          <Icon source={icons.audio} size={32} />
        </Pressable>

        <Pressable style={[styles.navIcon, { left: 227 }]}>
          <Icon source={icons.visual} size={32} />
        </Pressable>

        <Pressable style={[styles.navIcon, { left: 311 }]}>
          <Icon source={icons.settings} size={32} />
        </Pressable>
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
    flexDirection: "row",
    alignItems: "flex-end",
    paddingBottom: 68,
    paddingLeft: 34,
  },
  avatar: {
    width: 50,
    height: 50,
    borderRadius: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 3,
  },
  greeting: {
    position: "absolute",
    left: 84,
    bottom: 75,
    color: "white",
    fontSize: 20,
    fontFamily: "Gravity-Regular",
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
    top: 247,
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
  bottomNav: {
    width: 402,
    height: 95,
    position: "absolute",
    left: 0,
    top: 779,
    backgroundColor: "white",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 10,
  },
  activeCircle: {
    width: 54,
    height: 54,
    position: "absolute",
    left: 48,
    top: 18,
    backgroundColor: "#D9D9D9",
    borderRadius: 27,
  },
  navIcon: {
    width: 32,
    height: 32,
    position: "absolute",
    top: 28,
    justifyContent: "center",
    alignItems: "center",
  },
});

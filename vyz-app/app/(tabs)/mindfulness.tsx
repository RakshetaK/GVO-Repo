import { View, Text, StyleSheet, ScrollView, Pressable } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

const breathingExercises = [
  { id: 1, name: "Box Breathing", icon: "☀️" },
  { id: 2, name: "Balloon Breathing", icon: "☀️" },
  { id: 3, name: "Wave Breathing", icon: "☀️" },
  { id: 4, name: "4-7-8 Breathing", icon: "☀️" },
];

export default function MindfulnessScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.avatar} />
        <Text style={styles.greeting}>Welcome, Krish</Text>
      </View>

      <ScrollView style={styles.content}>
        <Text style={styles.sectionTitle}>Mindfulness</Text>
        <Text style={styles.subtitle}>Breathing Exercises</Text>

        <View style={styles.grid}>
          {breathingExercises.map((exercise) => (
            <Pressable key={exercise.id} style={styles.card}>
              <Text style={styles.icon}>{exercise.icon}</Text>
              <Text style={styles.cardText}>{exercise.name}</Text>
            </Pressable>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F5F5F5",
  },
  header: {
    backgroundColor: "#0066FF",
    padding: 20,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
    flexDirection: "row",
    alignItems: "center",
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "#FFFFFF",
    marginRight: 12,
  },
  greeting: {
    color: "white",
    fontSize: 18,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  sectionTitle: {
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: "#666",
    marginBottom: 20,
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
  },
  card: {
    width: "48%",
    aspectRatio: 1,
    backgroundColor: "#0066FF",
    borderRadius: 12,
    justifyContent: "center",
    alignItems: "center",
  },
  icon: {
    fontSize: 48,
    marginBottom: 8,
  },
  cardText: {
    color: "white",
    fontSize: 14,
    textAlign: "center",
  },
});

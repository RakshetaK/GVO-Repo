import { View, Text, StyleSheet, Pressable, ScrollView } from "react-native";
import { useState } from "react";
import Slider from "@react-native-community/slider";
import { SafeAreaView } from "react-native-safe-area-context";
import { jetsonApi } from "../../services/jetsonApi";

const sounds = [
  "White Noise",
  "Ocean Waves",
  "Gentle Rain",
  "Brown Noise",
  "Sunday Sunshine",
  "Calming Crickets",
];

export default function AudioScreen() {
  const [suppression, setSuppression] = useState(50);
  const [activeSound, setActiveSound] = useState<string | null>(null);

  const handleSoundToggle = async (sound: string) => {
    try {
      if (activeSound === sound) {
        await jetsonApi.stopSound();
        setActiveSound(null);
      } else {
        await jetsonApi.playSoothingSound(sound, 70);
        setActiveSound(sound);
      }
    } catch (error) {
      console.error("Failed to toggle sound:", error);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.avatar} />
        <Text style={styles.greeting}>Welcome, Krish</Text>
      </View>

      <ScrollView style={styles.content}>
        <Text style={styles.title}>Audio</Text>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Noise Suppression</Text>
          <Text style={styles.description}>
            Adjust the amount which your auditory surroundings will be muffled
          </Text>

          <Slider
            style={styles.slider}
            minimumValue={0}
            maximumValue={100}
            value={suppression}
            onValueChange={setSuppression}
            onSlidingComplete={(value) => jetsonApi.setNoiseSuppression(value)}
            minimumTrackTintColor="#0066FF"
            maximumTrackTintColor="#E0E0E0"
          />
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Soothing Sounds</Text>
          <Text style={styles.description}>
            Pick a soothing sound from a playlist of noise types
          </Text>

          {sounds.map((sound) => (
            <Pressable
              key={sound}
              style={[
                styles.soundButton,
                activeSound === sound && styles.soundButtonActive,
              ]}
              onPress={() => handleSoundToggle(sound)}
            >
              <View style={styles.soundInfo}>
                <View style={styles.playIcon} />
                <Text style={styles.soundText}>{sound}</Text>
              </View>
              <View style={styles.volumeIcon} />
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
  title: {
    fontSize: 28,
    fontWeight: "bold",
    marginBottom: 20,
  },
  section: {
    marginBottom: 30,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "600",
    marginBottom: 8,
  },
  description: {
    fontSize: 14,
    color: "#666",
    marginBottom: 20,
  },
  slider: {
    width: "100%",
    height: 40,
  },
  soundButton: {
    backgroundColor: "#0066FF",
    borderRadius: 12,
    padding: 16,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  soundButtonActive: {
    backgroundColor: "#0052CC",
  },
  soundInfo: {
    flexDirection: "row",
    alignItems: "center",
  },
  playIcon: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: "white",
    marginRight: 12,
  },
  soundText: {
    color: "white",
    fontSize: 16,
  },
  volumeIcon: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: "rgba(255, 255, 255, 0.3)",
  },
});

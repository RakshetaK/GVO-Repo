import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  Image,
} from "react-native";
import { useState } from "react";
import Slider from "@react-native-community/slider";

const sounds = [
  "White Noise",
  "Ocean Waves",
  "Gentle Rain",
  "Brown Noise",
  "Sunday Sunshine",
  "Calming Crickets",
];

// Simplified API calls for now - update jetsonApi path if needed
const jetsonApi = {
  setNoiseSuppression: async (level: number) => {
    console.log("Setting noise suppression to:", level);
  },
  playSoothingSound: async (sound: string, volume: number) => {
    console.log("Playing sound:", sound, "at volume:", volume);
  },
  stopSound: async () => {
    console.log("Stopping sound");
  },
};

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

  const handleSuppressionChange = (value: number) => {
    setSuppression(value);
  };

  const handleSuppressionComplete = async (value: number) => {
    try {
      await jetsonApi.setNoiseSuppression(value);
    } catch (error) {
      console.error("Failed to set noise suppression:", error);
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.headerContainer}>
        <View style={styles.headerShadow} />
        <View style={styles.header}>
          <View style={styles.avatar} />
          <Text style={styles.greeting}>Welcome, Krish</Text>
        </View>
      </View>

      {/* Content */}
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <Text style={styles.title}>Audio</Text>

        {/* Noise Suppression Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Noise Suppression</Text>
          <Text style={styles.description}>
            Adjust the amount which your auditory surroundings will be muffled
          </Text>

          <View style={styles.sliderContainer}>
            <Slider
              style={styles.slider}
              minimumValue={0}
              maximumValue={100}
              value={suppression}
              onValueChange={handleSuppressionChange}
              onSlidingComplete={handleSuppressionComplete}
              minimumTrackTintColor="#0F62FE"
              maximumTrackTintColor="#C6C6C6"
              thumbTintColor="#0F62FE"
            />
          </View>
        </View>

        {/* Soothing Sounds Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Soothing Sounds</Text>
          <Text style={styles.description}>
            Pick a soothing sound from a playlist of noise types, or listen to a
            snippet of audio by clicking the volume icon
          </Text>

          <View style={styles.soundsList}>
            {sounds.map((sound) => (
              <Pressable
                key={sound}
                style={styles.soundButton}
                onPress={() => handleSoundToggle(sound)}
              >
                <View style={styles.soundInfo}>
                  <View style={styles.playIconContainer}>
                    <View style={styles.playIcon} />
                  </View>
                  <Text style={styles.soundText}>{sound}</Text>
                </View>
                <View style={styles.volumeIconContainer}>
                  <View style={styles.volumeIcon} />
                </View>
              </Pressable>
            ))}
          </View>
        </View>
      </ScrollView>

      {/* Bottom Navigation */}
      <View style={styles.bottomNav}>
        <Pressable style={styles.navItem}>
          <View style={styles.navIcon}>
            <View style={[styles.iconCircle, { width: 28, height: 28 }]} />
          </View>
        </Pressable>

        <Pressable style={styles.navItem}>
          <View style={styles.navIcon}>
            <View style={styles.iconGlasses} />
          </View>
        </Pressable>

        <Pressable style={[styles.navItem, styles.navItemActive]}>
          <View style={styles.navIconActive}>
            <View style={styles.volumeNavIcon} />
          </View>
        </Pressable>

        <Pressable style={styles.navItem}>
          <View style={styles.navIcon}>
            <View style={styles.settingsIcon} />
          </View>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "white",
  },
  headerContainer: {
    position: "relative",
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
    alignItems: "center",
    paddingTop: 112,
    paddingLeft: 34,
  },
  avatar: {
    width: 50,
    height: 50,
    borderRadius: 10,
    backgroundColor: "#FFFFFF",
  },
  greeting: {
    marginLeft: 13,
    color: "white",
    fontSize: 20,
    fontWeight: "400",
  },
  content: {
    flex: 1,
    paddingHorizontal: 21,
    paddingTop: 160,
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: "#161515",
    marginBottom: 20,
  },
  section: {
    marginBottom: 30,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: "400",
    color: "#161515",
    marginBottom: 8,
  },
  description: {
    fontSize: 11,
    fontWeight: "300",
    color: "#161515",
    width: 336,
    lineHeight: 16,
    marginBottom: 20,
  },
  sliderContainer: {
    width: 349,
    height: 20,
    marginTop: 10,
  },
  slider: {
    width: "100%",
    height: 40,
  },
  soundsList: {
    gap: 19,
    marginTop: 15,
  },
  soundButton: {
    width: 349,
    height: 43,
    backgroundColor: "#0F62FE",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 3,
  },
  soundInfo: {
    flexDirection: "row",
    alignItems: "center",
  },
  playIconContainer: {
    width: 24,
    height: 24,
    justifyContent: "center",
    alignItems: "center",
    marginRight: 11,
  },
  playIcon: {
    width: 0,
    height: 0,
    borderLeftWidth: 10,
    borderLeftColor: "white",
    borderTopWidth: 6,
    borderTopColor: "transparent",
    borderBottomWidth: 6,
    borderBottomColor: "transparent",
  },
  soundText: {
    color: "white",
    fontSize: 15,
    fontWeight: "400",
  },
  volumeIconContainer: {
    width: 24,
    height: 24,
    justifyContent: "center",
    alignItems: "center",
  },
  volumeIcon: {
    width: 16,
    height: 12,
    borderLeftWidth: 6,
    borderLeftColor: "white",
    borderTopWidth: 6,
    borderTopColor: "white",
    borderBottomWidth: 6,
    borderBottomColor: "white",
  },
  bottomNav: {
    width: "100%",
    height: 95,
    backgroundColor: "white",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 10,
    flexDirection: "row",
    justifyContent: "space-around",
    alignItems: "center",
    paddingTop: 28,
  },
  navItem: {
    width: 32,
    height: 32,
    justifyContent: "center",
    alignItems: "center",
  },
  navItemActive: {
    width: 54,
    height: 54,
    backgroundColor: "#D9D9D9",
    borderRadius: 27,
  },
  navIcon: {
    width: 32,
    height: 32,
  },
  navIconActive: {
    width: 32,
    height: 32,
  },
  iconCircle: {
    borderWidth: 2,
    borderColor: "#171717",
    borderRadius: 14,
  },
  iconGlasses: {
    width: 28,
    height: 12,
    borderWidth: 2,
    borderColor: "#171717",
    borderRadius: 6,
  },
  volumeNavIcon: {
    width: 24,
    height: 18,
    borderLeftWidth: 8,
    borderLeftColor: "#171717",
    borderTopWidth: 9,
    borderTopColor: "#171717",
    borderBottomWidth: 9,
    borderBottomColor: "#171717",
  },
  settingsIcon: {
    width: 28,
    height: 28,
    borderWidth: 2,
    borderColor: "#171717",
    borderRadius: 14,
  },
});

import { View, Text, StyleSheet } from "react-native";
import { useState } from "react";
import Slider from "@react-native-community/slider";
import { SafeAreaView } from "react-native-safe-area-context";
import { jetsonApi } from "../../services/jetsonApi";

export default function VisualScreen() {
  const [brightness, setBrightness] = useState(50);

  const handleBrightnessChange = async (value: number) => {
    setBrightness(value);
    try {
      await jetsonApi.setBrightness(value);
    } catch (error) {
      console.error("Failed to set brightness:", error);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.avatar} />
        <Text style={styles.greeting}>Welcome, Krish</Text>
      </View>

      <View style={styles.content}>
        <Text style={styles.title}>Visual</Text>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Brightness</Text>
          <Text style={styles.description}>
            Adjust the amount which your visual surroundings will be darkened
          </Text>

          <View style={styles.controlContainer}>
            <View style={styles.brightnessVisual}>
              <View style={[styles.sun, { opacity: brightness / 100 }]} />
              <View style={styles.arc} />
              <View style={styles.bars}>
                {[...Array(5)].map((_, i) => (
                  <View
                    key={i}
                    style={[
                      styles.bar,
                      { opacity: i < brightness / 20 ? 1 : 0.3 },
                    ]}
                  />
                ))}
              </View>
            </View>

            <Slider
              style={styles.slider}
              minimumValue={0}
              maximumValue={100}
              value={brightness}
              onValueChange={handleBrightnessChange}
              minimumTrackTintColor="#0066FF"
              maximumTrackTintColor="#E0E0E0"
            />
          </View>
        </View>
      </View>
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
  controlContainer: {
    backgroundColor: "white",
    borderRadius: 12,
    padding: 20,
  },
  brightnessVisual: {
    height: 200,
    justifyContent: "center",
    alignItems: "center",
    position: "relative",
  },
  sun: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: "#0066FF",
    position: "absolute",
    left: 40,
  },
  arc: {
    width: 150,
    height: 150,
    borderRadius: 75,
    borderWidth: 8,
    borderColor: "#0066FF",
    borderTopColor: "transparent",
    borderRightColor: "transparent",
    transform: [{ rotate: "-45deg" }],
    position: "absolute",
    left: 60,
  },
  bars: {
    position: "absolute",
    right: 40,
    flexDirection: "column",
    gap: 8,
  },
  bar: {
    width: 30,
    height: 20,
    backgroundColor: "#0066FF",
    borderRadius: 4,
  },
  slider: {
    width: "100%",
    height: 40,
    marginTop: 20,
  },
});

import { View, Text, StyleSheet, Pressable } from "react-native";
import { useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { SafeAreaView } from "react-native-safe-area-context";

export default function WelcomeScreen() {
  const router = useRouter();

  return (
    <LinearGradient colors={["#0066FF", "#0052CC"]} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.content}>
          <View style={styles.waveContainer}>
            {/* Simple wave representation */}
            <View style={styles.wave1} />
            <View style={styles.wave2} />
            <Text style={styles.title}>Welcome to Vyz</Text>
          </View>

          <Pressable
            style={styles.loginButton}
            onPress={() => router.push("/(tabs)/mindfulness")}
          >
            <Text style={styles.loginText}>Log in</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  waveContainer: {
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 100,
  },
  wave1: {
    width: 200,
    height: 100,
    borderRadius: 100,
    borderWidth: 3,
    borderColor: "rgba(255, 255, 255, 0.5)",
    marginBottom: -50,
  },
  wave2: {
    width: 250,
    height: 125,
    borderRadius: 125,
    borderWidth: 3,
    borderColor: "rgba(255, 255, 255, 0.3)",
    marginBottom: 30,
  },
  title: {
    fontSize: 32,
    color: "white",
    fontWeight: "500",
    marginTop: 20,
  },
  loginButton: {
    borderWidth: 2,
    borderColor: "white",
    borderRadius: 8,
    paddingHorizontal: 40,
    paddingVertical: 12,
    position: "absolute",
    bottom: 100,
  },
  loginText: {
    color: "white",
    fontSize: 16,
  },
});

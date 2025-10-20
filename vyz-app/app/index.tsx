import { View, Text, Pressable, StyleSheet, Image } from "react-native";
import { useRouter } from "expo-router";

const logo = require("../assets/vyz-logo.png");

export default function Index() {
  const router = useRouter();

  return (
    <View style={styles.container}>
      {/* Logo Image */}
      <Image source={logo} style={styles.logo} resizeMode="contain" />

      {/* Welcome text */}
      <View style={styles.titleRow}>
        <Text style={styles.welcomeText}>Welcome to </Text>
        <Text style={styles.brandText}>Vyz</Text>
      </View>

      {/* Login button */}
      <Pressable
        onPress={() => router.push("/(tabs)/mindfulness")}
        style={({ pressed }) => [
          styles.loginButton,
          pressed && { opacity: 0.85 },
        ]}
      >
        <Text style={styles.loginText}>Log in</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: "100%",
    height: "100%",
    position: "relative",
    backgroundColor: "#0F62FE",
    overflow: "hidden",
    justifyContent: "center",
    alignItems: "center",
  },
  logo: {
    width: "130%",
    height: 200,
    position: "absolute",
    top: "35%",
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    position: "absolute",
    top: "60%",
  },
  welcomeText: {
    color: "white",
    fontSize: 32,
    fontWeight: "300",
  },
  brandText: {
    color: "white",
    fontSize: 32,
    fontStyle: "italic",
    fontWeight: "400",
  },
  loginButton: {
    width: 200,
    height: 50,
    position: "absolute",
    top: "75%",
    borderWidth: 2,
    borderColor: "white",
    borderRadius: 8,
    justifyContent: "center",
    alignItems: "center",
  },
  loginText: {
    color: "white",
    fontSize: 20,
    fontWeight: "300",
  },
});

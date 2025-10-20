import React, { useRef, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  Image,
  TouchableOpacity,
  Animated,
  Switch,
  ScrollView,
} from "react-native";
import { useRouter } from "expo-router";
import Icon from "../../components/Icon";
import { Ionicons } from "@expo/vector-icons";

const icons = {
  mindfulness: require("../../assets/mindfulness-icon.png"),
  audio: require("../../assets/audio-icon.png"),
  visual: require("../../assets/visual-icon.png"),
  settings: require("../../assets/setting-icon.png"),
  avatar: require("../../assets/profile.png"),
};

type Tab = "mindfulness" | "audio" | "visual" | "settings";

export default function SettingsScreen() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>("settings");
  const dotLeft = useRef(new Animated.Value(300)).current;

  const animateAndNavigate = (tab: Tab, toPosition: number, route: string) => {
    setActiveTab(tab);

    Animated.timing(dotLeft, {
      toValue: toPosition,
      duration: 300,
      useNativeDriver: false,
    }).start();

    router.push(route);
  };

  // Settings state
  const [notifications, setNotifications] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [autoSave, setAutoSave] = useState(true);

  return (
    <View style={styles.container}>
      <View style={styles.background} />
      <View style={styles.headerShadow} />
      <View style={styles.header} />

      <Image source={icons.avatar} style={styles.avatarAbs} />
      <Text style={styles.greetingAbs}>Welcome, Krish</Text>

      <TouchableOpacity
        style={styles.backButton}
        onPress={() => router.push("/")}
      >
        <Ionicons name="chevron-back" size={28} color="white" />
      </TouchableOpacity>

      <ScrollView
        style={styles.scrollContainer}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.title}>Settings</Text>
        <Text style={styles.subtitle}>Preferences</Text>

        {/* Settings Options */}
        <View style={styles.settingItem}>
          <Text style={styles.settingLabel}>Notifications</Text>
          <Switch
            value={notifications}
            onValueChange={setNotifications}
            trackColor={{ false: "#E3E3E3", true: "#0F62FE" }}
            thumbColor="#fff"
          />
        </View>

        <View style={styles.settingItem}>
          <Text style={styles.settingLabel}>Dark Mode</Text>
          <Switch
            value={darkMode}
            onValueChange={setDarkMode}
            trackColor={{ false: "#E3E3E3", true: "#0F62FE" }}
            thumbColor="#fff"
          />
        </View>

        <View style={styles.settingItem}>
          <Text style={styles.settingLabel}>Auto-Save Progress</Text>
          <Switch
            value={autoSave}
            onValueChange={setAutoSave}
            trackColor={{ false: "#E3E3E3", true: "#0F62FE" }}
            thumbColor="#fff"
          />
        </View>

        <View style={styles.divider} />

        <Text style={styles.sectionTitle}>Account</Text>

        <TouchableOpacity style={styles.menuItem}>
          <Text style={styles.menuText}>Edit Profile</Text>
          <Ionicons name="chevron-forward" size={20} color="#161515" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.menuItem}>
          <Text style={styles.menuText}>Change Password</Text>
          <Ionicons name="chevron-forward" size={20} color="#161515" />
        </TouchableOpacity>

        <View style={styles.divider} />

        <Text style={styles.sectionTitle}>Support</Text>

        <TouchableOpacity style={styles.menuItem}>
          <Text style={styles.menuText}>Help Center</Text>
          <Ionicons name="chevron-forward" size={20} color="#161515" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.menuItem}>
          <Text style={styles.menuText}>Privacy Policy</Text>
          <Ionicons name="chevron-forward" size={20} color="#161515" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.menuItem}>
          <Text style={styles.menuText}>Terms of Service</Text>
          <Ionicons name="chevron-forward" size={20} color="#161515" />
        </TouchableOpacity>

        <View style={styles.divider} />

        <TouchableOpacity style={styles.logoutButton}>
          <Text style={styles.logoutText}>Log Out</Text>
        </TouchableOpacity>

        <Text style={styles.version}>Version 1.0.0</Text>
      </ScrollView>

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
          onPress={() => animateAndNavigate("visual", 216, "/(tabs)/visual")}
        >
          <Icon
            source={icons.visual}
            size={32}
            tint={activeTab === "visual" ? "#fff" : "#000"}
          />
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.navBtn, { left: 311 }]}
          onPress={() => {
            // Already on settings
          }}
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
    bottom: 100,
  },
  scrollContent: {
    paddingTop: 20,
    paddingBottom: 40,
    paddingHorizontal: 21,
  },

  title: {
    color: "#161515",
    fontSize: 24,
    fontFamily: "Gravity-Bold",
    marginBottom: 8,
  },
  subtitle: {
    color: "#161515",
    fontSize: 20,
    fontFamily: "Gravity-Regular",
    marginBottom: 30,
  },

  settingItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#E3E3E3",
  },
  settingLabel: {
    fontSize: 16,
    fontFamily: "Gravity-Regular",
    color: "#161515",
  },

  divider: {
    height: 1,
    backgroundColor: "#E3E3E3",
    marginVertical: 24,
  },

  sectionTitle: {
    fontSize: 18,
    fontFamily: "Gravity-Bold",
    color: "#161515",
    marginBottom: 16,
  },

  menuItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#E3E3E3",
  },
  menuText: {
    fontSize: 16,
    fontFamily: "Gravity-Regular",
    color: "#161515",
  },

  logoutButton: {
    backgroundColor: "#FF3B30",
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 24,
    marginBottom: 16,
  },
  logoutText: {
    color: "white",
    fontSize: 16,
    fontFamily: "Gravity-Bold",
  },

  version: {
    textAlign: "center",
    color: "#999",
    fontSize: 12,
    fontFamily: "Gravity-Regular",
    marginTop: 8,
  },

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

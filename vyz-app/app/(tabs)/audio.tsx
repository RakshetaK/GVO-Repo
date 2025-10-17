import React, { useState } from 'react';
import Icon from "../../components/Icon";
import {
  StyleSheet,
  View,
  Text,
  Image,
  FlatList,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
} from 'react-native';
import Slider from '@react-native-community/slider';
const icons = {
  mindfulness: require("../../assets/mindfulness-icon.png"),
  audio: require("../../assets/audio-icon.png"),
  visual: require("../../assets/visual-icon.png"),
  settings: require("../../assets/vyz-logo.png"),
  calm: require("../../assets/calm-icon.png"),
  avatar: require("../../assets/profile.png"),
};
import { Ionicons, MaterialIcons, Feather } from '@expo/vector-icons';

const soothingSounds = [
  { id: '1', title: 'White Noise' },
  { id: '2', title: 'Ocean Waves' },
  { id: '3', title: 'Gentle Rain' },
  { id: '4', title: 'Brown Noise' },
  { id: '5', title: 'Sunday Sunshine' },
  { id: '6', title: 'Calming Crickets' },
  { id: '7', title: 'Forest Wind' },
  { id: '8', title: 'Fireplace Crackle' },
  { id: '9', title: 'Soft Piano' },
];

export default function App() {
  const [noiseSuppression, setNoiseSuppression] = useState(0.5);

  const renderSoundItem = ({ item }) => (
    <View style={styles.soundItem}>
      <TouchableOpacity style={styles.soundButton}>
        <Ionicons name="play-circle" size={24} color="white" />
        <Text style={styles.soundText}>{item.title}</Text>
      </TouchableOpacity>
      <TouchableOpacity>
        <Feather name="volume-2" size={20} color="white" />
      </TouchableOpacity>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
      {/* Header */}
      <View style={styles.header}>
        <Image source={icons.avatar} style={styles.avatar} />
        <Text style={styles.greeting}>Welcome, Krish</Text>
      </View>

        {/* Audio Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Audio</Text>

          <Text style={styles.subTitle}>Noise Suppression</Text>
          <Text style={styles.description}>
            Adjust the amount which your auditory surroundings will be muffled
          </Text>
          <Slider
            style={{ width: '100%', height: 40 }}
            minimumValue={0}
            maximumValue={1}
            value={noiseSuppression}
            onValueChange={value => setNoiseSuppression(value)}
            minimumTrackTintColor="#1E90FF"
            maximumTrackTintColor="#ccc"
            thumbTintColor="#1E90FF"
          />
        </View>

        {/* Soothing Sounds */}
        <View style={styles.section}>
          <Text style={styles.subTitle}>Soothing Sounds</Text>
          <Text style={styles.description}>
            Pick a soothing sound from a playlist of noise types, or listen to a snippet of audio by clicking the volume icon
          </Text>

          {soothingSounds.map((item) => (
            <View key={item.id} style={styles.soundItem}>
              <TouchableOpacity style={styles.soundButton}>
                <Ionicons name="play-circle" size={24} color="white" />
                <Text style={styles.soundText}>{item.title}</Text>
              </TouchableOpacity>
              <TouchableOpacity>
                <Feather name="volume-2" size={20} color="white" />
              </TouchableOpacity>
            </View>
          ))}
        </View>
      </ScrollView>

<View style={styles.navBar}>
  <TouchableOpacity style={styles.navButton} onPress={() => console.log('Emotions')}>
    <MaterialIcons name="emoji-emotions" size={28} color="black" />
  </TouchableOpacity>
  <TouchableOpacity style={styles.navButton} onPress={() => console.log('Audio')}>
    <Ionicons name="volume-high" size={28} color="black" />
  </TouchableOpacity>
  <TouchableOpacity style={styles.navButton} onPress={() => console.log('Headphones')}>
    <Feather name="headphones" size={28} color="black" />
  </TouchableOpacity>
  <TouchableOpacity style={styles.navButton} onPress={() => console.log('Settings')}>
    <Ionicons name="settings-outline" size={28} color="black" />
  </TouchableOpacity>
</View>

    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  scrollContent: {
    paddingTop: 50,
    paddingHorizontal: 20,
    paddingBottom: 100, // Leave space for navbar
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    backgroundColor: '#1E90FF',
    padding: 15,
    borderRadius: 10,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    marginRight: 15,
  },
  welcomeText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  section: {
    marginTop: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
  },
  subTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginTop: 10,
  },
  description: {
    color: '#555',
    fontSize: 13,
    marginVertical: 5,
  },
  soundItem: {
    backgroundColor: '#1E90FF',
    padding: 15,
    marginVertical: 5,
    borderRadius: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  soundButton: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  soundText: {
    color: 'white',
    fontSize: 16,
    marginLeft: 10,
  },
  navBar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 15,
    borderTopWidth: 1,
    borderTopColor: '#ccc',
    backgroundColor: '#fff',
  },
});

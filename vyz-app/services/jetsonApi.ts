import axios from "axios";

const JETSON_BASE_URL = "http://192.168.1.100:5000"; // Replace with your Jetson's IP

export const jetsonApi = {
  // Brightness control
  setBrightness: async (level: number) => {
    return axios.post(`${JETSON_BASE_URL}/api/brightness`, { level });
  },

  // Audio control
  setNoiseSuppression: async (level: number) => {
    return axios.post(`${JETSON_BASE_URL}/api/audio/suppression`, { level });
  },

  playSoothingSound: async (soundType: string, volume: number) => {
    return axios.post(`${JETSON_BASE_URL}/api/audio/play`, {
      sound: soundType,
      volume,
    });
  },

  stopSound: async () => {
    return axios.post(`${JETSON_BASE_URL}/api/audio/stop`);
  },

  // Get device status
  getStatus: async () => {
    return axios.get(`${JETSON_BASE_URL}/api/status`);
  },
};

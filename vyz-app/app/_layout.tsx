import { Slot } from "expo-router";
import { useFonts } from "expo-font";
import * as SplashScreen from "expo-splash-screen";
import { useEffect } from "react";

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [loaded] = useFonts({
    "Gravity-Regular": require("../assets/fonts/Gravity-Regular.otf"),
    "Gravity-Bold": require("../assets/fonts/Gravity-Bold.otf"),
    "BaiJamjuree-Italic": require("../assets/fonts/BaiJamjuree-Italic.otf"),
  });

  useEffect(() => {
    if (loaded) SplashScreen.hideAsync();
  }, [loaded]);

  if (!loaded) return null;
  return <Slot />;
}

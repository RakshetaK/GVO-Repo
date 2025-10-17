import { Slot } from "expo-router";
import { useFonts } from "expo-font";
import * as SplashScreen from "expo-splash-screen";
import { useEffect } from "react";

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [loaded, error] = useFonts({
    // Gravity (OTF)
    "Gravity-Regular": require("../assets/fonts/Gravity-Regular.otf"),
    "Gravity-Bold": require("../assets/fonts/Gravity-Bold.otf"),
    "Gravity-Light": require("../assets/fonts/Gravity-Light.otf"),
    "Gravity-Book": require("../assets/fonts/Gravity-Book.otf"),
    "Gravity-UltraLight": require("../assets/fonts/Gravity-UltraLight.otf"),
    "Gravity-Italic": require("../assets/fonts/Gravity-Italic.otf"),
    "Gravity-BoldItalic": require("../assets/fonts/Gravity-BoldItalic.otf"),
    "Gravity-BookItalic": require("../assets/fonts/Gravity-BookItalic.otf"),
    "Gravity-LightItalic": require("../assets/fonts/Gravity-LightItalic.otf"),
    "Gravity-UltraLightItalic": require("../assets/fonts/Gravity-UltraLightItalic.otf"),

    // BaiJamjuree (TTF) — use .ttf, not .otf
    "BaiJamjuree-Regular": require("../assets/fonts/BaiJamjuree-Regular.ttf"),
    "BaiJamjuree-Bold": require("../assets/fonts/BaiJamjuree-Bold.ttf"),
    "BaiJamjuree-SemiBold": require("../assets/fonts/BaiJamjuree-SemiBold.ttf"),
    "BaiJamjuree-Medium": require("../assets/fonts/BaiJamjuree-Medium.ttf"),
    "BaiJamjuree-Light": require("../assets/fonts/BaiJamjuree-Light.ttf"),
    "BaiJamjuree-ExtraLight": require("../assets/fonts/BaiJamjuree-ExtraLight.ttf"),
    "BaiJamjuree-Italic": require("../assets/fonts/BaiJamjuree-Italic.ttf"),
    "BaiJamjuree-BoldItalic": require("../assets/fonts/BaiJamjuree-BoldItalic.ttf"),
    "BaiJamjuree-SemiBoldItalic": require("../assets/fonts/BaiJamjuree-SemiBoldItalic.ttf"),
    "BaiJamjuree-MediumItalic": require("../assets/fonts/BaiJamjuree-MediumItalic.ttf"),
    "BaiJamjuree-LightItalic": require("../assets/fonts/BaiJamjuree-LightItalic.ttf"),
    "BaiJamjuree-ExtraLightItalic": require("../assets/fonts/BaiJamjuree-ExtraLightItalic.ttf"),
  });

  useEffect(() => {
    if (loaded || error) SplashScreen.hideAsync();
  }, [loaded, error]);

  if (!loaded) return null;
  return <Slot />;
}

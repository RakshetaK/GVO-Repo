import { Image, ImageStyle, StyleProp } from "react-native";

type Props = {
  source: any;
  size?: number;
  style?: StyleProp<ImageStyle>;
  tint?: string;
};

export default function Icon({ source, size = 28, style, tint }: Props) {
  return (
    <Image
      source={source}
      style={[
        { width: size, height: size, resizeMode: "contain" },
        tint ? { tintColor: tint } : null,
        style,
      ]}
    />
  );
}

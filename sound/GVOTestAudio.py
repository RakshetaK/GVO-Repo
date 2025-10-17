#!/usr/bin/env python3
import numpy as np
from scipy import signal
import sounddevice as sd
import sys
import time
from dotenv import load_dotenv, set_key
import requests
import os

# Load settings
SETTINGS_ENV = "settings.env"
STORE_ENV = "store.env"

# Flask server URL
FLASK_URL = "http://localhost:5000/recommend"

# Threshold monitoring
API_COOLDOWN = 5.0  # minimum seconds between API calls

# Settings reload interval
SETTINGS_RELOAD_INTERVAL = 2.0  # reload settings every 2 seconds

def update_store_amplitude(normalized_amplitude):
    """Update AMPLITUDE in store.env"""
    try:
        set_key(STORE_ENV, "AMPLITUDE", f"{normalized_amplitude:.6f}")
    except Exception as e:
        print(f"✗ Error updating store: {e}")

def trigger_recommend_api():
    """Call Flask /recommend endpoint"""
    try:
        response = requests.post(FLASK_URL, timeout=3)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                rec = result.get("recommendation", {})
                print(f"✓ API Response - Audio: {rec.get('audio')}, Light: {rec.get('light')}")
        else:
            print(f"✗ API error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"✗ API call failed: Flask server not reachable at {FLASK_URL}")
    except Exception as e:
        print(f"✗ API call failed: {e}")

def load_settings():
    """Load settings from settings.env and return as dict"""
    load_dotenv(SETTINGS_ENV, override=True)
    return {
        'threshold_db': int(os.getenv("THRESHOLD_DB", -20)),
        'ratio': int(os.getenv("RATIO", 4)),
        'target_peak': float(os.getenv("TARGET_PEAK", 0.7)),
        'lowcut': int(os.getenv("LOWCUT", 200)),
        'highcut': int(os.getenv("HIGHCUT", 6000)),
        'white_noise_level': float(os.getenv("WHITE_NOISE_LEVEL", 0.08)),
        'amplitude_threshold': float(os.getenv("AMPLITUDE_THRESHOLD", 0.5)),
        'background_audio': os.getenv("BACKGROUND_AUDIO", "white_noise_calm")
    }

# ======================================================
#                   LiveMicCompressor
# ======================================================
class LiveMicCompressor:
    def __init__(self):
        # Audio stream settings
        self.CHUNK = 2048
        self.SAMPLE_RATE = 22050

        # Load initial settings
        settings = load_settings()
        

        # ===== Threshold tracking =====
        self.last_api_call = 0.0
        self.was_above_threshold = False
        self.amplitude_ema = 0.0

        # ===== Settings reload tracking =====
        self.last_settings_reload = 0.0

        # Internal filter state
        self.filter_b = None
        self.filter_a = None
        self.zi       = None
        self._apply_settings(settings)

    def _apply_settings(self, settings):
        """Apply settings dict to compressor parameters"""
        old_lowcut = getattr(self, 'lowcut', None)
        old_highcut = getattr(self, 'highcut', None)
        
        self.threshold_db = settings['threshold_db']
        self.ratio = settings['ratio']
        self.target_peak = settings['target_peak']
        self.lowcut = settings['lowcut']
        self.highcut = settings['highcut']
        self.white_noise_level = settings['white_noise_level']
        self.amplitude_threshold = settings['amplitude_threshold']
        self.background_audio = settings['background_audio']
        self.makeup_gain_db = 0
        
        # If filter frequencies changed, need to recalculate filter
        if old_lowcut != self.lowcut or old_highcut != self.highcut:
            if self.filter_b is not None:  # only if filter already initialized
                self._recalc_filter()

    def _reload_settings_if_due(self):
        """Reload settings from .env if enough time has passed"""
        now = time.time()
        if now - self.last_settings_reload > SETTINGS_RELOAD_INTERVAL:
            settings = load_settings()
            old_audio = self.background_audio
            self._apply_settings(settings)
            if old_audio != self.background_audio:
                print(f"⟳ Audio pattern changed: {old_audio} → {self.background_audio}")
            self.last_settings_reload = now

    def _recalc_filter(self):
        """Recalculate filter coefficients when frequencies change"""
        nyquist = self.SAMPLE_RATE / 2
        low  = self.lowcut  / nyquist
        high = self.highcut / nyquist
        self.filter_b, self.filter_a = signal.butter(4, [low, high], btype='band')
        # Reset filter state to avoid transients
        self.zi = signal.lfilter_zi(self.filter_b, self.filter_a) * 0

    def setup_filter(self):
        self._recalc_filter()

    def bandpass_filter_chunk(self, data):
        filtered, self.zi = signal.lfilter(self.filter_b, self.filter_a, data, zi=self.zi)
        return filtered

    def compress_chunk(self, data):
        threshold = 10 ** (self.threshold_db / 20)
        compressed = np.copy(data)
        for i in range(len(data)):
            amplitude = abs(data[i])
            if amplitude > threshold:
                over_db = 20 * np.log10(amplitude / threshold)
                compressed_over_db = over_db / self.ratio
                compressed_amplitude = threshold * (10 ** (compressed_over_db / 20))
                compressed[i] = np.sign(data[i]) * compressed_amplitude
        if self.makeup_gain_db != 0:
            compressed *= 10 ** (self.makeup_gain_db / 20)
        return compressed

    def normalize_chunk(self, data):
        current_peak = float(np.max(np.abs(data)))
        if current_peak > self.target_peak and current_peak > 0:
            data = data * (self.target_peak / current_peak)
        return data

    def generate_noise_chunk(self, length):
        """Generate different types of noise based on background_audio setting"""
        if "white" in self.background_audio:
            # White noise - equal energy across all frequencies
            return np.random.normal(0, self.white_noise_level, length)
        
        elif "pink" in self.background_audio:
            # Pink noise - 1/f noise (more bass)
            white = np.random.randn(length)
            # Simple pink noise approximation using running sum
            pink = np.cumsum(white)
            pink = pink - np.mean(pink)
            pink = pink / (np.max(np.abs(pink)) + 1e-9) * self.white_noise_level
            return pink
        
        elif "brown" in self.background_audio:
            # Brown noise - 1/f² noise (even more bass)
            white = np.random.randn(length)
            # Brownian noise using double integration
            brown = np.cumsum(np.cumsum(white))
            brown = brown - np.mean(brown)
            brown = brown / (np.max(np.abs(brown)) + 1e-9) * self.white_noise_level
            return brown
        
        else:
            # Default to white noise
            return np.random.normal(0, self.white_noise_level, length)

    def add_background_audio_chunk(self, data):
        """Add background audio/noise to chunk based on current setting"""
        if self.white_noise_level <= 0:
            return data
        
        noise = self.generate_noise_chunk(len(data))
        mixed = data + noise
        
        # Prevent clipping
        max_val = float(np.max(np.abs(mixed)))
        if max_val > 1.0:
            mixed = mixed / max_val
        
        return mixed

    def process_chunk(self, chunk):
        # Check if we should reload settings (time-based, lightweight check)
        self._reload_settings_if_due()
        
        if chunk.ndim > 1:
            chunk = chunk[:, 0]

        # 1) Filter
        filtered = self.bandpass_filter_chunk(chunk)

        # 2) Get peak for amplitude monitoring
        peak = float(np.max(np.abs(filtered)))

        # === AMPLITUDE THRESHOLD MONITORING ===
        normalized_amplitude = peak / max(self.target_peak, 1e-6)
        normalized_amplitude = min(1.0, normalized_amplitude)
        
        self.amplitude_ema = 0.8 * self.amplitude_ema + 0.2 * normalized_amplitude
        
        # Update store.env continuously
        update_store_amplitude(self.amplitude_ema)
        
        # Check threshold crossing
        now = time.time()
        is_above_threshold = self.amplitude_ema > self.amplitude_threshold
        crossed_threshold = is_above_threshold != self.was_above_threshold
        
        if crossed_threshold and (now - self.last_api_call) > API_COOLDOWN:
            print(f"\n🔔 Amplitude threshold crossed! {self.amplitude_ema:.3f} vs {self.amplitude_threshold:.3f}")
            trigger_recommend_api()
            self.last_api_call = now
        
        self.was_above_threshold = is_above_threshold

        # 3) Compress
        compressed = self.compress_chunk(filtered)
        # 4) Normalize
        normalized = self.normalize_chunk(compressed)
        # 5) Add background audio (type determined by background_audio setting)
        final = self.add_background_audio_chunk(normalized)
        return final

    def audio_callback(self, indata, outdata, frames, time_info, status):
        if status:
            print(f"Status: {status}")
        try:
            processed = self.process_chunk(indata[:, 0])
            outdata[:, 0] = processed
        except Exception as e:
            print(f"Error in callback: {e}")
            outdata.fill(0)

    def start_live_processing(self, input_device=None, output_device=None):
        if input_device is not None or output_device is not None:
            sd.default.device = (input_device, output_device)

        input_dev_info = sd.query_devices(sd.default.device[0])
        output_dev_info = sd.query_devices(sd.default.device[1])

        device_sample_rate = int(input_dev_info['default_samplerate'])
        if device_sample_rate != self.SAMPLE_RATE:
            print(f"\n⚠ Adjusting sample rate from {self.SAMPLE_RATE} to {device_sample_rate} Hz")
            self.SAMPLE_RATE = device_sample_rate

        print("\n" + "="*60)
        print("LIVE MICROPHONE COMPRESSOR (HOT-RELOAD ENABLED)")
        print("="*60)
        print(f"Sample Rate: {self.SAMPLE_RATE} Hz")
        print(f"Chunk Size: {self.CHUNK} samples")
        print(f"Settings reload: every {SETTINGS_RELOAD_INTERVAL}s")

        print("\n" + "="*60)
        print("INITIAL SETTINGS (from settings.env):")
        print("="*60)
        print(f"  Compression:")
        print(f"    - Threshold: {self.threshold_db} dB")
        print(f"    - Ratio: {self.ratio}:1")
        print(f"  Frequency Filter:")
        print(f"    - Low Cut: {self.lowcut} Hz")
        print(f"    - High Cut: {self.highcut} Hz")
        print(f"  Output:")
        print(f"    - Max Volume: {self.target_peak}")
        print(f"    - Background Audio: {self.background_audio}")
        print(f"    - Noise Level: {self.white_noise_level * 100:.1f}%")
        print(f"  Monitoring:")
        print(f"    - Amplitude Threshold: {self.amplitude_threshold}")
        print("="*60)

        self.setup_filter()

        print(f"\nUsing devices:")
        print(f"  Input:  {input_dev_info['name']}")
        print(f"  Output: {output_dev_info['name']}")
        print("\n🎤 Starting LIVE audio processing...  (Ctrl+C to stop)")
        print("⟳ Settings will auto-reload from settings.env\n")

        try:
            with sd.Stream(
                samplerate=self.SAMPLE_RATE,
                channels=1,
                callback=self.audio_callback,
                blocksize=self.CHUNK,
                dtype='float32'
            ):
                print("✓ Processing active - speak into your microphone!\n")
                while True:
                    sd.sleep(1000)
        except KeyboardInterrupt:
            print("\n\n✓ Stopped by user")
        except Exception as e:
            print(f"\n\nError: {e}")

def list_audio_devices():
    print("\n" + "="*60)
    print("AVAILABLE AUDIO DEVICES")
    print("="*60)
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        device_type = []
        if device['max_input_channels'] > 0:
            device_type.append('INPUT')
        if device['max_output_channels'] > 0:
            device_type.append('OUTPUT')
        print(f"\n[{i}] {device['name']}")
        print(f"    Type: {', '.join(device_type) if device_type else '—'}")
        print(f"    Channels: In={device['max_input_channels']}, Out={device['max_output_channels']}")
        print(f"    Sample Rate: {device['default_samplerate']} Hz")
    print("\n" + "="*60)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Live Microphone Audio Compressor (Hot-Reload)')
    parser.add_argument('--devices', action='store_true', help='List available audio devices')
    args = parser.parse_args()

    if args.devices:
        list_audio_devices()
        sys.exit(0)

    compressor = LiveMicCompressor()
    # Always use input=1, output=0 as requested
    compressor.start_live_processing(input_device=1, output_device=0)



#!/usr/bin/env python3
import numpy as np
from scipy import signal
import sounddevice as sd
import sys
import time
import glob
import serial
from serial.tools import list_ports

# -------- UART auto-detect (GPIO UART or USB) --------
def open_serial():
    # Preferred order: Pi UART symlinks → hardware nodes → USB serials
    candidates = [
        '/dev/serial0', '/dev/ttyAMA0', '/dev/ttyS0',
        '/dev/ttyACM0', '/dev/ttyUSB0'
    ]
    detected = [p.device for p in list_ports.comports()]
    for c in candidates + detected:
        try:
            if c and (glob.glob(c) or c in detected):
                s = serial.Serial(c, baudrate=9600, timeout=1)
                print(f"[UART] Connected on {c}")
                return s
        except Exception:
            pass
    print("[UART] No serial port available. Running without LEDs.")
    return None

ser = open_serial()
if ser:
    print(f"[UART] Using port: {ser.port} @ {ser.baudrate} "
          f"(bytesize={ser.bytesize}, parity={ser.parity}, stopbits={ser.stopbits})")
    time.sleep(2.0)          # Arduino auto-reset guard (if applicable)
    ser.reset_input_buffer()
else:
    print("[UART] No serial port — LED control disabled")

# ======================================================
#                   LiveMicCompressor
# ======================================================
class LiveMicCompressor:
    def __init__(self):
        # Audio stream settings
        self.CHUNK = 2048
        self.SAMPLE_RATE = 22050  # lower is lighter on Pi CPU

        # ===== Compressor & filter =====
        self.threshold_db    = -20
        self.ratio           = 4
        self.makeup_gain_db  = 0
        self.target_peak     = 0.7
        self.lowcut          = 200
        self.highcut         = 6000
        self.white_noise_level = 0.08

        # ===== LED / Serial signaling =====
        self.loud_hysteresis_db = 3.0     # dB hysteresis around threshold
        self.led_min_interval   = 0.05    # seconds; rate limit UART updates
        self.level_alpha        = 0.2     # EMA smoothing for LED level
        self._last_led_send = 0.0
        self._loud_state    = False       # True = loud, False = tame
        self._thr_up_lin    = None
        self._thr_down_lin  = None
        self._level_ema     = 0.0

        # Internal filter state
        self.filter_b = None
        self.filter_a = None
        self.zi       = None

    # ---------- Helpers ----------
    def _recalc_thresholds(self):
        thr_lin = 10 ** (self.threshold_db / 20.0)
        self._thr_up_lin   = thr_lin
        self._thr_down_lin = thr_lin * (10 ** (-self.loud_hysteresis_db / 20.0))

    def _decide_loud(self, peak_abs):
        if self._loud_state:
            # currently loud → require dropping below lower threshold to release
            return peak_abs > self._thr_down_lin
        else:
            # currently tame → require exceeding upper threshold to trigger
            return peak_abs > self._thr_up_lin

    def _level_to_rgb(self, lvl):
        """
        lvl in [0,1]: 0 = blue (calm), 0.5 = purple, 1 = red (loud).
        Slight green in middle for visibility.
        """
        lvl = max(0.0, min(1.0, lvl))
        r = int(255 *  lvl)
        g = int(80  * (1.0 - abs(2*lvl - 1.0)))
        b = int(255 * (1.0 -  lvl))
        return r, g, b

    def _rgb255_to_pct(self, r, g, b):
    # Convert 0..255 → 0..100 (rounded, clamped)
        to_pct = lambda x: max(0, min(100, int(round((x / 255.0) * 100))))
        return to_pct(r), to_pct(g), to_pct(b)

    def _send_rgb_if_due(self, r255, g255, b255):
        now = time.time()
        if not ser or (now - self._last_led_send < self.led_min_interval):
            return
        try:
            r, g, b = self._rgb255_to_pct(r255, g255, b255)
            # EXACT frame: !R.G.B#
            frame = f"!{r}.{g}.{b}#".encode("ascii")
            ser.write(frame)                 # no newline
            ser.flush()                      # push it out
        except Exception:
            pass
        self._last_led_send = now


    # ---------- DSP pipeline ----------
    def setup_filter(self):
        nyquist = self.SAMPLE_RATE / 2
        low  = self.lowcut  / nyquist
        high = self.highcut / nyquist
        self.filter_b, self.filter_a = signal.butter(4, [low, high], btype='band')
        self.zi = signal.lfilter_zi(self.filter_b, self.filter_a) * 0
        self._recalc_thresholds()

    def bandpass_filter_chunk(self, data):
        filtered, self.zi = signal.lfilter(self.filter_b, self.filter_a, data, zi=self.zi)
        return filtered

    def compress_chunk(self, data):
        threshold = 10 ** (self.threshold_db / 20)
        compressed = np.copy(data)
        # per-sample loop is fine at this rate
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

    def add_white_noise_chunk(self, data):
        if self.white_noise_level <= 0:
            return data
        white_noise = np.random.normal(0, self.white_noise_level, len(data))
        mixed = data + white_noise
        max_val = float(np.max(np.abs(mixed)))
        if max_val > 1.0:
            mixed = mixed / max_val
        return mixed

    def process_chunk(self, chunk):
        # Ensure mono
        if chunk.ndim > 1:
            chunk = chunk[:, 0]

        # 1) Filter
        filtered = self.bandpass_filter_chunk(chunk)

        # 2) LED logic tap (use filtered peak)
        peak = float(np.max(np.abs(filtered)))  # linear
        # Normalize peak versus compressor threshold for 0..1 display
        norm = min(1.0, peak / max(self._thr_up_lin or 1e-6, 1e-6))
        self._level_ema = (1 - self.level_alpha) * self._level_ema + self.level_alpha * norm

        # Hysteretic loud/tame decision
        new_loud = self._decide_loud(peak)
        self._loud_state = new_loud

        # Build RGB + send (throttled)
        r, g, b = self._level_to_rgb(self._level_ema)
        self._send_rgb_if_due(r, g, b)

        # 3) Compress
        compressed = self.compress_chunk(filtered)
        # 4) Normalize
        normalized = self.normalize_chunk(compressed)
        # 5) Add white noise
        final = self.add_white_noise_chunk(normalized)
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
        # Optional: set devices
        if input_device is not None or output_device is not None:
            sd.default.device = (input_device, output_device)

        # Resolve actual devices
        input_dev_info = sd.query_devices(sd.default.device[0])
        output_dev_info = sd.query_devices(sd.default.device[1])

        # Adopt the device native rate (avoids resampler stress)
        device_sample_rate = int(input_dev_info['default_samplerate'])
        if device_sample_rate != self.SAMPLE_RATE:
            print(f"\n⚠ Adjusting sample rate from {self.SAMPLE_RATE} to {device_sample_rate} Hz (device native rate)")
            self.SAMPLE_RATE = device_sample_rate

        print("\n" + "="*60)
        print("LIVE MICROPHONE COMPRESSOR")
        print("="*60)
        print(f"Sample Rate: {self.SAMPLE_RATE} Hz")
        print(f"Chunk Size: {self.CHUNK} samples")
        print(f"Latency: ~{(self.CHUNK / self.SAMPLE_RATE) * 1000:.1f} ms")

        print("\n" + "="*60)
        print("CURRENT SETTINGS:")
        print("="*60)
        print(f"  Compression:")
        print(f"    - Threshold: {self.threshold_db} dB")
        print(f"    - Ratio: {self.ratio}:1")
        print(f"    - Makeup Gain: {self.makeup_gain_db} dB")
        print(f"  Frequency Filter:")
        print(f"    - Low Cut: {self.lowcut} Hz")
        print(f"    - High Cut: {self.highcut} Hz")
        print(f"  Output:")
        print(f"    - Max Volume: {self.target_peak}")
        print(f"    - White Noise: {self.white_noise_level * 100:.1f}%")
        print("="*60)

        # Setup filter after finalizing SR
        self.setup_filter()

        print(f"\nUsing devices:")
        print(f"  Input:  {input_dev_info['name']}")
        print(f"  Output: {output_dev_info['name']}")
        print(f"UART: {'ENABLED' if ser else 'DISABLED'} (C R G B\\n @ 9600)\n")
        print("🎤 Starting LIVE audio processing...  (Ctrl+C to stop)\n")

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
            print("\nTroubleshooting:")
            print("  1. Run with --devices to see available devices")
            print("  2. Make sure no other app is using your microphone")
            print("  3. Check your system audio permissions")

# -------- Utilities --------
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
    print("CURRENT DEFAULT DEVICES:")
    print("="*60)
    try:
        print(f"  Input:  [{sd.default.device[0]}] {sd.query_devices(sd.default.device[0])['name']}")
        print(f"  Output: [{sd.default.device[1]}] {sd.query_devices(sd.default.device[1])['name']}")
    except Exception:
        print("  (Defaults not set)")
    print("\nTo use specific devices, run with: --input <num> --output <num>")

# -------- Main --------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Live Microphone Audio Compressor (with RGB UART)')
    parser.add_argument('--devices', action='store_true', help='List available audio devices')
    parser.add_argument('--input', type=int, help='Input device number (see --devices)', default=None)
    parser.add_argument('--output', type=int, help='Output device number (see --devices)', default=None)
    args = parser.parse_args()

    if args.devices:
        list_audio_devices()
        sys.exit(0)

    compressor = LiveMicCompressor()

    # === Tunables ===
    compressor.threshold_db = -20
    compressor.ratio = 4
    compressor.makeup_gain_db = 0

    compressor.lowcut = 200
    compressor.highcut = 6000

    compressor.target_peak = 0.7
    compressor.white_noise_level = 0.08

    # LED behavior
    compressor.loud_hysteresis_db = 3.0
    compressor.led_min_interval   = 0.05
    compressor.level_alpha        = 0.2

    compressor.start_live_processing(
        input_device=args.input,
        output_device=args.output
    )

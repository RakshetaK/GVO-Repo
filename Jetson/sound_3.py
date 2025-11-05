#!/usr/bin/env python3
import numpy as np
from scipy import signal
import sounddevice as sd
import serial
import sys
import threading
import queue
import time

SYNC_B1, SYNC_B2 = 0xAA, 0x55

class ArduinoMicCompressor:
    def __init__(self, serial_port='/dev/ttyACM0', baud_rate=115200):
        self.serial_port = serial_port
        self.baud_rate = baud_rate

        # Will be auto-calibrated before audio starts
        self.SAMPLE_RATE = 8000       # fallback; overwritten in calibrate
        self.CHUNK = 512              # audio block size

        # ---------- User settings ----------
        # Compression
        self.threshold_db = -20
        self.ratio = 4
        self.makeup_gain_db = 0

        # Volume limiting
        self.target_peak = 0.7

        # Band limits (guarded against Nyquist)
        self.lowcut = 200
        self.highcut = 3000

        # Comfort/dither noise (0.01–0.03 is subtle; 0.08 is obvious)
        self.white_noise_level = 0.02
        # -----------------------------------

        # Internal state
        self.filter_b = None
        self.filter_a = None
        self.zi = None
        self.ser = None
        self.audio_buffer = queue.Queue(maxsize=100)
        self.is_running = False

        # Reader accumulators
        self._accum = []
        self._aligned = False  # stream alignment (after seeing sync)
        self._bytebuf = bytearray()

    # ---------- Serial ----------
    def connect_arduino(self):
        try:
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            print(f"✓ Connected to Arduino on {self.serial_port}")
            time.sleep(2)  # wait for Arduino reset
            self.ser.reset_input_buffer()
            return True
        except serial.SerialException as e:
            print(f"✗ Serial error: {e}")
            print("Try: /dev/ttyACM0 or /dev/ttyUSB0, add your user to 'dialout', or use sudo.")
            return False

    def _append_to_queue(self, sample_float):
        self._accum.append(sample_float)
        if len(self._accum) >= self.CHUNK:
            chunk = np.asarray(self._accum[:self.CHUNK], dtype=np.float32)
            self._accum = self._accum[self.CHUNK:]
            try:
                self.audio_buffer.put_nowait(chunk)
            except queue.Full:
                # Drop oldest and push new
                try:
                    self.audio_buffer.get_nowait()
                except queue.Empty:
                    pass
                try:
                    self.audio_buffer.put_nowait(chunk)
                except queue.Full:
                    pass

    def _consume_sync(self):
        """
        Scan self._bytebuf to align on sync boundary (0xAA 0x55).
        After alignment, drop the sync bytes and set self._aligned = True.
        """
        buf = self._bytebuf
        i = 0
        found = False
        while i + 1 < len(buf):
            if buf[i] == SYNC_B1 and buf[i+1] == SYNC_B2:
                # discard up to and including the sync word
                del buf[:i+2]
                found = True
                break
            i += 1
        if found:
            self._aligned = True
            return True
        return False

    def _next_sample_from_buf(self):
        """
        Returns (sample_value:int or None). Handles sync words inline.
        Assumes we are aligned. Keeps alignment if extra syncs appear.
        """
        buf = self._bytebuf
        # ensure at least 2 bytes available
        while len(buf) >= 2:
            # if next two bytes are sync, drop them and continue
            if buf[0] == SYNC_B1 and buf[1] == SYNC_B2:
                del buf[:2]
                continue
            # otherwise read a 16-bit little-endian sample
            value = int.from_bytes(buf[:2], 'little', signed=False)
            del buf[:2]
            return value
        return None

    def read_arduino_samples(self):
        print("Starting Arduino reader thread…")
        sample_count, last_report = 0, time.time()

        while self.is_running:
            try:
                b = self.ser.read(512)
                if b:
                    self._bytebuf.extend(b)

                # align if not aligned yet
                if not self._aligned:
                    if not self._consume_sync():
                        # try to keep buffer bounded while searching
                        if len(self._bytebuf) > 4096:
                            del self._bytebuf[:2048]
                        continue

                # consume samples
                while True:
                    value = self._next_sample_from_buf()
                    if value is None:
                        break

                    # Map 0..1023 → approx [-1.0, +1.0)
                    normalized = (value / 512.0) - 1.0
                    self._append_to_queue(normalized)

                    sample_count += 1
                    now = time.time()
                    if now - last_report >= 1.0:
                        print(f"  Samples/sec ~ {sample_count:5d} | Queue {self.audio_buffer.qsize():3d} | Last {value:4d}")
                        sample_count = 0
                        last_report = now

            except Exception as e:
                print(f"Reader error: {e}")
                break

        print("Arduino reader thread stopped")

    def calibrate_sample_rate(self, seconds=1.5):
        """
        Estimate source sample rate before we open the audio stream.
        Ignores sync words while counting.
        """
        print("\nCalibrating incoming sample rate…")
        self.ser.reset_input_buffer()
        start = time.time()
        count = 0
        buf = bytearray()

        while time.time() - start < seconds:
            b = self.ser.read(512)
            if not b:
                continue
            buf.extend(b)
            # strip sync pairs and count samples
            while len(buf) >= 2:
                if buf[0] == SYNC_B1 and buf[1] == SYNC_B2:
                    del buf[:2]
                    continue
                # consume one sample
                del buf[:2]
                count += 1

        elapsed = time.time() - start
        rate = int(round(count / elapsed)) if elapsed > 0 else 8000
        # keep within sane bounds
        rate = max(3000, min(12000, rate))
        print(f"  Estimated Arduino rate: ~{rate} Hz over {elapsed:.2f}s")
        self.SAMPLE_RATE = rate

    # ---------- DSP ----------
    def setup_filter(self):
        nyq = self.SAMPLE_RATE / 2.0
        low = max(1.0, self.lowcut) / nyq
        high_hz = min(self.highcut, 0.45 * self.SAMPLE_RATE)  # clamp safely below Nyquist
        high = high_hz / nyq
        self.filter_b, self.filter_a = signal.butter(4, [low, high], btype='band')
        # start from zero state
        self.zi = signal.lfilter_zi(self.filter_b, self.filter_a) * 0.0

    def bandpass_filter_chunk(self, data):
        filtered, self.zi = signal.lfilter(self.filter_b, self.filter_a, data, zi=self.zi)
        return filtered

    def compress_chunk(self, data):
        threshold = 10 ** (self.threshold_db / 20.0)
        compressed = data.copy()
        # elementwise soft-knee-ish static curve
        amps = np.abs(compressed)
        over = amps > threshold
        if np.any(over):
            over_db = 20.0 * np.log10(amps[over] / threshold)
            comp_over_db = over_db / self.ratio
            comp_amp = threshold * (10.0 ** (comp_over_db / 20.0))
            compressed[over] = np.sign(compressed[over]) * comp_amp

        if self.makeup_gain_db != 0:
            makeup = 10 ** (self.makeup_gain_db / 20.0)
            compressed *= makeup
        return compressed

    def normalize_chunk(self, data):
        peak = np.max(np.abs(data))
        if peak > self.target_peak:
            data = data * (self.target_peak / peak)
        return data

    def add_white_noise_chunk(self, data):
        if self.white_noise_level <= 0:
            return data
        noise = np.random.normal(0.0, self.white_noise_level, size=data.shape).astype(np.float32)
        mixed = data + noise
        peak = np.max(np.abs(mixed))
        if peak > 1.0:
            mixed /= peak
        return mixed

    def process_chunk(self, chunk):
        x = self.bandpass_filter_chunk(chunk)
        x = self.compress_chunk(x)
        x = self.normalize_chunk(x)
        x = self.add_white_noise_chunk(x)
        return x

    # ---------- Audio ----------
    def audio_callback(self, outdata, frames, time_info, status):
        if status:
            print(f"Status: {status}")

        try:
            chunk = self.audio_buffer.get_nowait()
        except queue.Empty:
            outdata.fill(0)
            return

        # Single-pass processing here (no double-processing anywhere else)
        processed = self.process_chunk(chunk)

        n = min(len(processed), len(outdata))
        outdata[:n, 0] = processed[:n]
        if n < len(outdata):
            outdata[n:, 0] = 0.0

    def start_live_processing(self, output_device=None):
        print("\n" + "="*60)
        print("ARDUINO MICROPHONE COMPRESSOR")
        print("="*60)

        if not self.connect_arduino():
            return

        # One-time rate calibration
        self.calibrate_sample_rate(seconds=1.5)

        # Show settings
        print(f"\nSample Rate (playback): {self.SAMPLE_RATE} Hz")
        print(f"Chunk Size: {self.CHUNK}")
        print("\n" + "="*60)
        print("CURRENT SETTINGS")
        print("="*60)
        print(f"  Compression: threshold {self.threshold_db} dB, ratio {self.ratio}:1")
        print(f"  Bandpass: {self.lowcut}–{min(self.highcut, int(0.45*self.SAMPLE_RATE))} Hz")
        print(f"  Output: target_peak {self.target_peak}, white_noise {self.white_noise_level}")
        print("="*60)

        # Filter after we know the calibrated rate
        self.setup_filter()

        # Output device select (optional)
        if output_device is not None:
            sd.default.device = (None, output_device)

        # Friendly device print (guarded)
        try:
            dev = sd.default.device
            out_idx = dev[1] if isinstance(dev, (list, tuple)) else dev
            name = sd.query_devices(out_idx)['name']
            print(f"\nUsing output device: {name}")
        except Exception:
            print("\nUsing default output device")

        # Start the reader
        self.is_running = True
        t = threading.Thread(target=self.read_arduino_samples, daemon=True)
        t.start()

        print("\n🎤 Starting live audio…  (Ctrl+C to stop)\n")

        try:
            with sd.OutputStream(
                samplerate=self.SAMPLE_RATE,
                channels=1,
                callback=self.audio_callback,
                blocksize=self.CHUNK,
                dtype='float32'
            ):
                # Let the callback pull from the queue; keep main thread alive
                while self.is_running:
                    time.sleep(0.05)
        except KeyboardInterrupt:
            print("\n✓ Stopped by user")
        except Exception as e:
            print(f"\nAudio error: {e}")
        finally:
            self.is_running = False
            try:
                if self.ser:
                    self.ser.close()
            except:
                pass


def list_serial_ports():
    import serial.tools.list_ports
    print("\n" + "="*60)
    print("AVAILABLE SERIAL PORTS")
    print("="*60)
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No serial ports found.")
    for p in ports:
        print(f"\nPort: {p.device}\n  Description: {p.description}\n  HWID: {p.hwid}")
    print("\n" + "="*60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Arduino Microphone Audio Compressor")
    parser.add_argument('--ports', action='store_true', help='List serial ports and exit')
    parser.add_argument('--devices', action='store_true', help='List audio devices and exit')
    parser.add_argument('--port', type=str, default='/dev/ttyACM0', help='Serial port (e.g., /dev/ttyACM0, /dev/ttyUSB0, COM3)')
    parser.add_argument('--baud', type=int, default=115200, help='Baud rate')
    parser.add_argument('--output', type=int, default=None, help='Output device index')
    args = parser.parse_args()

    if args.ports:
        list_serial_ports()
        sys.exit(0)

    if args.devices:
        print("\n" + "="*60)
        print("AUDIO DEVICES")
        print("="*60)
        print(sd.query_devices())
        sys.exit(0)

    app = ArduinoMicCompressor(serial_port=args.port, baud_rate=args.baud)
    # tweakables (override defaults here if you want)
    app.threshold_db = -20
    app.ratio = 4
    app.lowcut = 200
    app.highcut = 3000
    app.white_noise_level = 0.02
    app.target_peak = 0.7

    app.start_live_process

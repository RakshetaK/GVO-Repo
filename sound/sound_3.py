import numpy as np
from scipy import signal
import sounddevice as sd
import serial
import sys
import threading
import queue

class ArduinoMicCompressor:
    def __init__(self, serial_port='/dev/ttyUSB0', baud_rate=115200):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        
        # Audio settings
        self.SAMPLE_RATE = 8000  # Try lowering to 4000 if issues
        self.CHUNK = 512  # Smaller chunks = less latency
        
        # ========== ADJUSTABLE SETTINGS ==========
        
        # COMPRESSION
        self.threshold_db = -20
        self.ratio = 4
        self.makeup_gain_db = 0
        
        # VOLUME LIMITING
        self.target_peak = 0.7
        
        # FREQUENCY FILTERING
        self.lowcut = 200
        self.highcut = 3000  # Lower because of low sample rate
        
        # WHITE NOISE
        self.white_noise_level = 0.08
        
        # ========================================
        
        # Internal state
        self.filter_b = None
        self.filter_a = None
        self.zi = None
        self.ser = None
        self.audio_buffer = queue.Queue(maxsize=100)
        self.is_running = False
        
    def setup_filter(self):
        """Pre-calculate filter coefficients"""
        nyquist = self.SAMPLE_RATE / 2
        low = self.lowcut / nyquist
        high = min(self.highcut / nyquist, 0.95)  # Don't exceed Nyquist
        
        self.filter_b, self.filter_a = signal.butter(4, [low, high], btype='band')
        self.zi = signal.lfilter_zi(self.filter_b, self.filter_a) * 0
        
    def connect_arduino(self):
        """Connect to Arduino via serial"""
        try:
            self.ser = serial.Serial(
                self.serial_port, 
                self.baud_rate,
                timeout=1
            )
            print(f"✓ Connected to Arduino on {self.serial_port}")
            
            # Wait for Arduino to reset
            import time
            time.sleep(2)
            
            # Flush any initial garbage
            self.ser.reset_input_buffer()
            
            return True
            
        except serial.SerialException as e:
            print(f"✗ Error connecting to Arduino: {e}")
            print("\nTroubleshooting:")
            print("  1. Check if Arduino is plugged in")
            print("  2. Try different port: /dev/ttyUSB0, /dev/ttyACM0, or COM3, COM4 (Windows)")
            print("  3. Check permissions: sudo usermod -a -G dialout $USER")
            print("     (then logout and login)")
            return False
    
    def read_arduino_samples(self):
        print("Starting Arduino reader thread...")
        buf = bytearray()
        import time
        sample_count, last_report = 0, time.time()
    
        while self.is_running:
            try:
                b = self.ser.read(256)  # read a chunk
                if not b:
                    continue
                buf.extend(b)
    
                # consume in 2-byte steps
                while len(buf) >= 2:
                    value = int.from_bytes(buf[:2], 'little', signed=False)
                    del buf[:2]
    
                    normalized = (value / 512.0) - 1.0
                    # build audio chunks
                    self._append_to_queue(normalized)
    
                    sample_count += 1
                    now = time.time()
                    if now - last_report >= 1:
                        print(f"  Samples/sec: {sample_count}, Queue: {self.audio_buffer.qsize()}, Last: {value}")
                        sample_count = 0
                        last_report = now
            except Exception as e:
                print(f"Error reading from Arduino: {e}")
                break
        print("Arduino reader thread stopped")

def _append_to_queue(self, sample):
    # accumulate into CHUNK-sized blocks
    if not hasattr(self, "_accum"):
        self._accum = []
    self._accum.append(sample)
    if len(self._accum) >= self.CHUNK:
        chunk = np.asarray(self._accum[:self.CHUNK], dtype=np.float32)
        self._accum = self._accum[self.CHUNK:]
        try:
            self.audio_buffer.put_nowait(chunk)
        except queue.Full:
            try:
                self.audio_buffer.get_nowait()
                self.audio_buffer.put_nowait(chunk)
            except:
                pass

    
    def bandpass_filter_chunk(self, data):
        """Apply bandpass filter to a chunk"""
        filtered, self.zi = signal.lfilter(self.filter_b, self.filter_a, data, zi=self.zi)
        return filtered
    
    def compress_chunk(self, data):
        """Apply dynamic range compression"""
        threshold = 10 ** (self.threshold_db / 20)
        compressed = np.copy(data)
        
        for i in range(len(data)):
            amplitude = np.abs(data[i])
            
            if amplitude > threshold:
                over_db = 20 * np.log10(amplitude / threshold)
                compressed_over_db = over_db / self.ratio
                compressed_amplitude = threshold * (10 ** (compressed_over_db / 20))
                compressed[i] = np.sign(data[i]) * compressed_amplitude
        
        if self.makeup_gain_db != 0:
            makeup_gain = 10 ** (self.makeup_gain_db / 20)
            compressed *= makeup_gain
            
        return compressed
    
    def normalize_chunk(self, data):
        """Soft normalization"""
        current_peak = np.abs(data).max()
        if current_peak > self.target_peak:
            data = data * (self.target_peak / current_peak)
        return data
    
    def add_white_noise_chunk(self, data):
        """Add white noise"""
        white_noise = np.random.normal(0, self.white_noise_level, len(data))
        mixed = data + white_noise
        
        max_val = np.abs(mixed).max()
        if max_val > 1.0:
            mixed = mixed / max_val
            
        return mixed
    
    def process_chunk(self, chunk):
        """Process a single chunk through pipeline"""
        filtered = self.bandpass_filter_chunk(chunk)
        compressed = self.compress_chunk(filtered)
        normalized = self.normalize_chunk(compressed)
        final = self.add_white_noise_chunk(normalized)
        return final
    
    def audio_callback(self, outdata, frames, time_info, status):
        """Callback for audio output"""
        if status:
            print(f"Status: {status}")
        
        try:
            # Get processed chunk from queue
            chunk = self.audio_buffer.get_nowait()
            
            # Process it here in callback
            processed = self.process_chunk(chunk)
            
            if len(processed) < len(outdata):
                outdata[:len(processed), 0] = processed
                outdata[len(processed):, 0] = 0
            else:
                outdata[:, 0] = processed[:len(outdata)]
                
        except queue.Empty:
            # No data - output silence
            outdata.fill(0)
    
    def start_live_processing(self, output_device=None):
        """Start live Arduino mic processing"""
        
        print("\n" + "="*60)
        print("ARDUINO MICROPHONE COMPRESSOR")
        print("="*60)
        
        # Connect to Arduino
        if not self.connect_arduino():
            return
        
        print(f"\nSample Rate: {self.SAMPLE_RATE} Hz (limited by Arduino)")
        print(f"Chunk Size: {self.CHUNK} samples")
        
        print(f"\n" + "="*60)
        print("CURRENT SETTINGS:")
        print("="*60)
        print(f"  Compression:")
        print(f"    - Threshold: {self.threshold_db} dB")
        print(f"    - Ratio: {self.ratio}:1")
        print(f"  Frequency Filter:")
        print(f"    - Low Cut: {self.lowcut} Hz")
        print(f"    - High Cut: {self.highcut} Hz")
        print(f"  Output:")
        print(f"    - Max Volume: {self.target_peak}")
        print(f"    - White Noise: {self.white_noise_level * 100:.1f}%")
        print("="*60)
        
        # Setup filter
        self.setup_filter()
        
        # Set output device
        if output_device is not None:
            sd.default.device = (None, output_device)
        
        print(f"\nUsing output device: {sd.query_devices(sd.default.device[1])['name']}")
        
        # Start Arduino reader thread
        self.is_running = True
        reader_thread = threading.Thread(target=self.read_arduino_samples)
        reader_thread.daemon = True
        reader_thread.start()
        
        print("\n🎤 Starting Arduino audio processing...")
        print("Press Ctrl+C to stop\n")
        
        try:
            # Start audio processing in main thread
            with sd.OutputStream(
                samplerate=self.SAMPLE_RATE,
                channels=1,
                callback=lambda outdata, frames, time, status: 
                    self.audio_callback(outdata, frames, time, status),
                blocksize=self.CHUNK,
                dtype='float32'
            ):
                # Process audio from queue
                while self.is_running:
                    try:
                        # Get chunk from Arduino buffer
                        chunk = self.audio_buffer.get(timeout=1)
                        
                        # Process it
                        processed = self.process_chunk(chunk)
                        
                        # Put back in queue for playback callback
                        self.audio_buffer.put(processed)
                        
                    except queue.Empty:
                        continue
                        
        except KeyboardInterrupt:
            print("\n\n✓ Stopped by user")
        except Exception as e:
            print(f"\n\nError: {e}")
        finally:
            self.is_running = False
            if self.ser:
                self.ser.close()

def list_serial_ports():
    """List available serial ports"""
    import serial.tools.list_ports
    
    print("\n" + "="*60)
    print("AVAILABLE SERIAL PORTS")
    print("="*60)
    
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("No serial ports found!")
        print("\nMake sure:")
        print("  1. Arduino is plugged in via USB")
        print("  2. Drivers are installed")
        print("  3. You have permissions (Linux: sudo usermod -a -G dialout $USER)")
        return
    
    for port in ports:
        print(f"\nPort: {port.device}")
        print(f"  Description: {port.description}")
        print(f"  Hardware ID: {port.hwid}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Arduino Microphone Audio Compressor')
    parser.add_argument('--ports', action='store_true', help='List available serial ports')
    parser.add_argument('--devices', action='store_true', help='List available audio output devices')
    parser.add_argument('--port', type=str, help='Serial port (e.g., /dev/ttyUSB0 or COM3)', default='/dev/ttyUSB0')
    parser.add_argument('--baud', type=int, help='Baud rate', default=115200)
    parser.add_argument('--output', type=int, help='Output device number', default=None)
    
    args = parser.parse_args()
    
    if args.ports:
        list_serial_ports()
        sys.exit(0)
    
    if args.devices:
        print("\n" + "="*60)
        print("AVAILABLE AUDIO OUTPUT DEVICES")
        print("="*60)
        print(sd.query_devices())
        sys.exit(0)
    
    # Create compressor
    compressor = ArduinoMicCompressor(
        serial_port=args.port,
        baud_rate=args.baud
    )
    
    # Adjust settings
    compressor.threshold_db = -20
    compressor.ratio = 4
    compressor.lowcut = 200
    compressor.highcut = 3000  # Lower due to low sample rate
    compressor.white_noise_level = 0.08
    compressor.target_peak = 0.7
    
    # Start processing
    compressor.start_live_processing(output_device=args.output)

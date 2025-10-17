# import numpy as np
# from scipy import signal
# import sounddevice as sd
# import soundfile as sf
# import sys
# import os
# import queue
# import threading

# class StreamingAudioCompressor:
#     def __init__(self, input_file=None):
#         self.input_file = input_file
        
#         # Audio stream settings
#         self.CHUNK = 2048  # Samples per chunk (larger = more latency, more stable)
        
#         # ========== ADJUSTABLE SETTINGS ==========
        
#         # COMPRESSION - Controls dynamic range (loud vs quiet sounds)
#         self.threshold_db = -20  # Start compressing above this (-30 to -10)
#         self.ratio = 4           # How much to compress (1 = off, 4 = moderate, 10 = heavy)
#         self.makeup_gain_db = 0  # Boost overall volume after compression (-10 to +10)
        
#         # VOLUME LIMITING - Maximum output level
#         self.target_peak = 0.7   # Max volume (0.5 = quiet, 0.9 = loud)
        
#         # FREQUENCY FILTERING - What frequencies to allow through
#         self.lowcut = 200        # Remove bass below this Hz (100-500)
#         self.highcut = 6000      # Remove treble above this Hz (4000-10000)
        
#         # WHITE NOISE - Background soothing sound
#         self.white_noise_level = 0.08  # Volume of white noise (0.0 to 0.2)
        
#         # ========================================
        
#         # Internal state
#         self.filter_b = None
#         self.filter_a = None
#         self.zi = None
#         self.audio_queue = queue.Queue(maxsize=50)
#         self.is_playing = False
        
#     def setup_filter(self, sample_rate):
#         """Pre-calculate filter coefficients"""
#         nyquist = sample_rate / 2
#         low = self.lowcut / nyquist
#         high = self.highcut / nyquist
        
#         self.filter_b, self.filter_a = signal.butter(4, [low, high], btype='band')
#         self.zi = signal.lfilter_zi(self.filter_b, self.filter_a) * 0
        
#     def bandpass_filter_chunk(self, data):
#         """Apply bandpass filter to a chunk"""
#         filtered, self.zi = signal.lfilter(self.filter_b, self.filter_a, data, zi=self.zi)
#         return filtered
    
#     def compress_chunk(self, data):
#         """Apply dynamic range compression to a chunk"""
#         threshold = 10 ** (self.threshold_db / 20)
#         compressed = np.copy(data)
        
#         for i in range(len(data)):
#             amplitude = np.abs(data[i])
            
#             if amplitude > threshold:
#                 over_db = 20 * np.log10(amplitude / threshold)
#                 compressed_over_db = over_db / self.ratio
#                 compressed_amplitude = threshold * (10 ** (compressed_over_db / 20))
#                 compressed[i] = np.sign(data[i]) * compressed_amplitude
        
#         if self.makeup_gain_db != 0:
#             makeup_gain = 10 ** (self.makeup_gain_db / 20)
#             compressed *= makeup_gain
            
#         return compressed
    
#     def normalize_chunk(self, data):
#         """Soft normalization to prevent clipping"""
#         current_peak = np.abs(data).max()
#         if current_peak > self.target_peak:
#             data = data * (self.target_peak / current_peak)
#         return data
    
#     def add_white_noise_chunk(self, data):
#         """Add white noise to chunk"""
#         white_noise = np.random.normal(0, self.white_noise_level, len(data))
#         mixed = data + white_noise
        
#         # Prevent clipping
#         max_val = np.abs(mixed).max()
#         if max_val > 1.0:
#             mixed = mixed / max_val
            
#         return mixed
    
#     def process_chunk(self, chunk):
#         """Process a single chunk through the pipeline"""
#         # 1. Frequency filter
#         filtered = self.bandpass_filter_chunk(chunk)
        
#         # 2. Compress
#         compressed = self.compress_chunk(filtered)
        
#         # 3. Normalize
#         normalized = self.normalize_chunk(compressed)
        
#         # 4. Add white noise
#         final = self.add_white_noise_chunk(normalized)
        
#         return final
    
#     def audio_callback(self, outdata, frames, time_info, status):
#         """Callback function for sounddevice stream"""
#         if status:
#             print(f"Status: {status}")
        
#         try:
#             # Get processed chunk from queue
#             data = self.audio_queue.get_nowait()
            
#             # If we got data, copy it to output
#             if len(data) < len(outdata):
#                 # Pad if necessary
#                 outdata[:len(data)] = data.reshape(-1, 1)
#                 outdata[len(data):] = 0
#             else:
#                 outdata[:] = data[:len(outdata)].reshape(-1, 1)
                
#         except queue.Empty:
#             # No data available - output silence
#             outdata.fill(0)
    
#     def reader_thread(self, audio, sample_rate):
#         """Read and process audio in background thread"""
#         print("Starting audio processing thread...")
        
#         for i in range(0, len(audio), self.CHUNK):
#             if not self.is_playing:
#                 break
                
#             chunk = audio[i:i + self.CHUNK]
            
#             # Pad last chunk if needed
#             if len(chunk) < self.CHUNK:
#                 chunk = np.pad(chunk, (0, self.CHUNK - len(chunk)))
            
#             # Process chunk
#             processed = self.process_chunk(chunk)
            
#             # Add to queue (blocks if queue is full)
#             self.audio_queue.put(processed)
            
#             # Progress indicator
#             progress = (i / len(audio)) * 100
#             print(f"\rProgress: {progress:.1f}%", end='', flush=True)
        
#         print("\n\nProcessing complete!")
    
#     def play_file_streaming(self):
#         """Stream and play file in real-time"""
#         if not self.input_file or not os.path.exists(self.input_file):
#             print(f"Error: File '{self.input_file}' not found!")
#             return
        
#         print(f"Loading: {self.input_file}")
        
#         # Load audio file
#         audio, sample_rate = sf.read(self.input_file, dtype='float32')
        
#         # Convert to mono if stereo
#         if len(audio.shape) > 1:
#             audio = np.mean(audio, axis=1)
        
#         print(f"\nAudio Info:")
#         print(f"  Sample rate: {sample_rate} Hz")
#         print(f"  Duration: {len(audio) / sample_rate:.2f} seconds")
#         print(f"  Peak amplitude: {np.abs(audio).max():.3f}")
        
#         print(f"\n" + "="*60)
#         print("CURRENT SETTINGS:")
#         print("="*60)
#         print(f"  Compression:")
#         print(f"    - Threshold: {self.threshold_db} dB (try -30 to -10)")
#         print(f"    - Ratio: {self.ratio}:1 (try 1 to 10)")
#         print(f"    - Makeup Gain: {self.makeup_gain_db} dB (try -10 to +10)")
#         print(f"  Frequency Filter:")
#         print(f"    - Low Cut: {self.lowcut} Hz (try 100-500)")
#         print(f"    - High Cut: {self.highcut} Hz (try 4000-10000)")
#         print(f"  Output:")
#         print(f"    - Max Volume: {self.target_peak} (try 0.5-0.9)")
#         print(f"    - White Noise: {self.white_noise_level * 100:.1f}% (try 0-20%)")
#         print("="*60)
        
#         # Setup filter
#         self.setup_filter(sample_rate)
        
#         # Start playback flag
#         self.is_playing = True
        
#         # Start reader thread
#         reader = threading.Thread(target=self.reader_thread, args=(audio, sample_rate))
#         reader.daemon = True
#         reader.start()
        
#         print("\nStarting REAL-TIME playback...")
#         print("Press Ctrl+C to stop\n")
        
#         try:
#             # Open output stream and start playing immediately
#             with sd.OutputStream(
#                 samplerate=sample_rate,
#                 channels=1,
#                 callback=self.audio_callback,
#                 blocksize=self.CHUNK
#             ):
#                 # Keep playing until reader finishes or user stops
#                 reader.join()
                
#                 # Wait for queue to empty
#                 while not self.audio_queue.empty():
#                     sd.sleep(100)
                
#                 print("\nPlayback complete!")
                
#         except KeyboardInterrupt:
#             print("\n\nStopped by user")
#             self.is_playing = False
#         except Exception as e:
#             print(f"\nError: {e}")
#             self.is_playing = False

# def list_audio_devices():
#     """List available audio devices"""
#     print("\n=== Available Audio Devices ===")
#     print(sd.query_devices())
#     print("\nCurrent default device:")
#     print(f"  Input: {sd.default.device[0]}")
#     print(f"  Output: {sd.default.device[1]}")

# if __name__ == "__main__":
#     # Show available audio devices
#     if len(sys.argv) > 1 and sys.argv[1] == "--devices":
#         list_audio_devices()
#         sys.exit(0)
    
#     if len(sys.argv) < 2:
#         print("Usage: python3 streaming_audio_compressor.py <input_audio.wav>")
#         print("       python3 streaming_audio_compressor.py --devices")
#         print("\nExample: python3 streaming_audio_compressor.py test.wav")
#         sys.exit(1)
    
#     input_file = sys.argv[1]
    
#     # Create compressor
#     compressor = StreamingAudioCompressor(input_file)
    
#     # ========== ADJUST THESE SETTINGS ==========
    
#     # COMPRESSION - Make loud sounds quieter
#     compressor.threshold_db = -30       # Lower = compress more sounds
#     compressor.ratio = 10                # Higher = more compression
#     compressor.makeup_gain_db = 0       # Increase to boost overall volume
    
#     # FREQUENCY FILTERING - Remove annoying frequencies
#     compressor.lowcut = 400             # Higher = remove more bass
#     compressor.highcut = 4000           # Lower = remove more treble
    
#     # OUTPUT LEVELS
#     compressor.target_peak = 0.5        # Higher = louder output
#     compressor.white_noise_level = 0.02 # Higher = more background noise
    
#     # ===========================================
    
#     # Process and play
#     compressor.play_file_streaming()

import numpy as np
from scipy import signal
import sounddevice as sd
import sys

class LiveMicCompressor:
    def __init__(self):
        # Audio stream settings
        self.CHUNK = 1024       # Samples per chunk (lower = less latency)
        self.SAMPLE_RATE = 44100  # Sample rate in Hz
        
        # ========== ADJUSTABLE SETTINGS ==========
        
        # COMPRESSION - Controls dynamic range (loud vs quiet sounds)
        self.threshold_db = -20  # Start compressing above this (-30 to -10)
        self.ratio = 4           # How much to compress (1 = off, 4 = moderate, 10 = heavy)
        self.makeup_gain_db = 0  # Boost overall volume after compression (-10 to +10)
        
        # VOLUME LIMITING - Maximum output level
        self.target_peak = 0.7   # Max volume (0.5 = quiet, 0.9 = loud)
        
        # FREQUENCY FILTERING - What frequencies to allow through
        self.lowcut = 200        # Remove bass below this Hz (100-500)
        self.highcut = 6000      # Remove treble above this Hz (4000-10000)
        
        # WHITE NOISE - Background soothing sound
        self.white_noise_level = 0.002  # Volume of white noise (0.0 to 0.2)
        
        # ========================================
        
        # Internal state
        self.filter_b = None
        self.filter_a = None
        self.zi = None
        
    def setup_filter(self):
        """Pre-calculate filter coefficients"""
        nyquist = self.SAMPLE_RATE / 2
        low = self.lowcut / nyquist
        high = self.highcut / nyquist
        
        self.filter_b, self.filter_a = signal.butter(4, [low, high], btype='band')
        self.zi = signal.lfilter_zi(self.filter_b, self.filter_a) * 0
        
    def bandpass_filter_chunk(self, data):
        """Apply bandpass filter to a chunk"""
        filtered, self.zi = signal.lfilter(self.filter_b, self.filter_a, data, zi=self.zi)
        return filtered
    
    def compress_chunk(self, data):
        """Apply dynamic range compression to a chunk"""
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
        """Soft normalization to prevent clipping"""
        current_peak = np.abs(data).max()
        if current_peak > self.target_peak:
            data = data * (self.target_peak / current_peak)
        return data
    
    def add_white_noise_chunk(self, data):
        """Add white noise to chunk"""
        white_noise = np.random.normal(0, self.white_noise_level, len(data))
        mixed = data + white_noise
        
        # Prevent clipping
        max_val = np.abs(mixed).max()
        if max_val > 1.0:
            mixed = mixed / max_val
            
        return mixed
    
    def process_chunk(self, chunk):
        """Process a single chunk through the pipeline"""
        # Convert to 1D if needed
        if len(chunk.shape) > 1:
            chunk = chunk[:, 0]  # Take first channel if stereo
        
        # 1. Frequency filter
        filtered = self.bandpass_filter_chunk(chunk)
        
        # 2. Compress
        compressed = self.compress_chunk(filtered)
        
        # 3. Normalize
        normalized = self.normalize_chunk(compressed)
        
        # 4. Add white noise
        final = self.add_white_noise_chunk(normalized)
        
        return final
    
    def audio_callback(self, indata, outdata, frames, time_info, status):
        """Callback function for sounddevice duplex stream"""
        if status:
            print(f"Status: {status}")
        
        try:
            # Process incoming audio
            processed = self.process_chunk(indata[:, 0])
            
            # Output processed audio
            outdata[:, 0] = processed
            
        except Exception as e:
            print(f"Error in callback: {e}")
            outdata.fill(0)
    
    def start_live_processing(self, input_device=None, output_device=None):
        """Start live microphone processing"""
        
        print("\n" + "="*60)
        print("LIVE MICROPHONE COMPRESSOR")
        print("="*60)
        print(f"Sample Rate: {self.SAMPLE_RATE} Hz")
        print(f"Chunk Size: {self.CHUNK} samples")
        print(f"Latency: ~{(self.CHUNK / self.SAMPLE_RATE) * 1000:.1f} ms")
        
        print(f"\n" + "="*60)
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
        
        # Setup filter
        self.setup_filter()
        
        # Set devices if specified
        if input_device is not None or output_device is not None:
            sd.default.device = (input_device, output_device)
        
        print(f"\nUsing devices:")
        print(f"  Input: {sd.query_devices(sd.default.device[0])['name']}")
        print(f"  Output: {sd.query_devices(sd.default.device[1])['name']}")
        
        print("\n🎤 Starting LIVE audio processing...")
        print("Press Ctrl+C to stop\n")
        
        try:
            # Open duplex stream (input and output simultaneously)
            with sd.Stream(
                samplerate=self.SAMPLE_RATE,
                channels=1,
                callback=self.audio_callback,
                blocksize=self.CHUNK,
                dtype='float32'
            ):
                print("✓ Processing active - speak into your microphone!")
                print("  (You should hear yourself with processing applied)\n")
                
                # Keep running until interrupted
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

def list_audio_devices():
    """List available audio devices"""
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
        print(f"    Type: {', '.join(device_type)}")
        print(f"    Channels: In={device['max_input_channels']}, Out={device['max_output_channels']}")
        print(f"    Sample Rate: {device['default_samplerate']} Hz")
    
    print("\n" + "="*60)
    print("CURRENT DEFAULT DEVICES:")
    print("="*60)
    print(f"  Input: [{sd.default.device[0]}] {sd.query_devices(sd.default.device[0])['name']}")
    print(f"  Output: [{sd.default.device[1]}] {sd.query_devices(sd.default.device[1])['name']}")
    print("\nTo use specific devices, run with: --input <num> --output <num>")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Live Microphone Audio Compressor')
    parser.add_argument('--devices', action='store_true', help='List available audio devices')
    parser.add_argument('--input', type=int, help='Input device number (see --devices)', default=None)
    parser.add_argument('--output', type=int, help='Output device number (see --devices)', default=None)
    
    args = parser.parse_args()
    
    # Show available audio devices
    if args.devices:
        list_audio_devices()
        sys.exit(0)
    
    # Create compressor
    compressor = LiveMicCompressor()
    
    # ========== ADJUST THESE SETTINGS ==========
    
    # COMPRESSION - Make loud sounds quieter
    compressor.threshold_db = -20       # Lower = compress more sounds
    compressor.ratio = 4                # Higher = more compression
    compressor.makeup_gain_db = 0       # Increase to boost overall volume
    
    # FREQUENCY FILTERING - Remove annoying frequencies
    compressor.lowcut = 200             # Higher = remove more bass
    compressor.highcut = 6000           # Lower = remove more treble
    
    # OUTPUT LEVELS
    compressor.target_peak = 0.7        # Higher = louder output
    compressor.white_noise_level = 0.002 # Higher = more background noise
    
    # ===========================================
    
    # Start live processing
    compressor.start_live_processing(
        input_device=args.input,
        output_device=args.output
    )

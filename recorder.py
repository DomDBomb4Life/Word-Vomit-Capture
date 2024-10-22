# recorder.py

import pyaudio
import wave
import threading
import time
import os

class Recorder:
    def __init__(self, output_directory):
        self.output_directory = output_directory
        self.frames = []
        self.recording = False
        self.chunk_duration = 240  # Maximum duration per chunk in seconds
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.current_chunk = 0
        self.start_time = None
        self.lock = threading.Lock()

    def record(self):
        self.recording = True
        self.start_time = time.time()
        self.frames = []
        self.current_chunk = 0
        self.stream = self.audio.open(format=pyaudio.paInt16,
                                      channels=1,
                                      rate=44100,
                                      input=True,
                                      frames_per_buffer=1024)
        print("Recording started.")
        while self.recording:
            try:
                data = self.stream.read(1024, exception_on_overflow=False)
            except Exception as e:
                print(f"Error reading audio stream: {e}")
                continue
            with self.lock:
                self.frames.append(data)
            elapsed_time = time.time() - self.start_time
            if elapsed_time >= self.chunk_duration:
                self.save_chunk()
                self.start_time = time.time()
                self.frames = []
        if self.frames:
            self.save_chunk()
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        print("Recording stopped.")

    def stop(self):
        self.recording = False

    def save_chunk(self):
        with self.lock:
            chunk_filename = f"recording_chunk_{self.current_chunk}.wav"
            chunk_path = os.path.join(self.output_directory, chunk_filename)
            with wave.open(chunk_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(44100)
                wf.writeframes(b''.join(self.frames))
            print(f"Saved chunk: {chunk_filename}")
            self.current_chunk += 1
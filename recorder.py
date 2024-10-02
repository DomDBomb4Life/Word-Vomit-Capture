# recorder.py

import pyaudio
import wave

class Recorder:
    def __init__(self, output_file):
        self.output_file = output_file
        self.frames = []
        self.recording = False

    def record(self):
        self.recording = True
        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=44100,
                            input=True,
                            frames_per_buffer=1024)
        print("Recording started.")
        while self.recording:
            data = stream.read(1024)
            self.frames.append(data)
        stream.stop_stream()
        stream.close()
        audio.terminate()
        self.save_audio()
        print("Recording stopped.")

    def stop(self):
        self.recording = False

    def save_audio(self):
        with wave.open(self.output_file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
            wf.setframerate(44100)
            wf.writeframes(b''.join(self.frames))
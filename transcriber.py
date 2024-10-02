# transcriber.py

import requests

class Transcriber:
    def __init__(self, api_key):
        self.api_key = api_key

    def transcribe(self, audio_file_path, language='en'):
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
        }
        files = {
            'file': open(audio_file_path, 'rb'),
            'model': (None, 'whisper-1'),
            'response_format': (None, 'verbose_json'),
            'language': (None, language),
            'timestamp_granularities[]': (None, 'segment'),
        }

        response = requests.post(url, headers=headers, files=files)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
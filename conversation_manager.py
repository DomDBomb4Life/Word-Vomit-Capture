# conversation_manager.py

import os
import shutil
import time

class ConversationManager:
    def __init__(self):
        self.conversations_dir = "conversations"
        os.makedirs(self.conversations_dir, exist_ok=True)
        self.selected_conversation = None

    def get_conversations(self):
        return [d for d in os.listdir(self.conversations_dir) if os.path.isdir(os.path.join(self.conversations_dir, d))]

    def create_conversation(self, name):
        path = os.path.join(self.conversations_dir, name)
        if os.path.exists(path):
            return False
        os.makedirs(path)
        self.select_conversation(name)
        return True

    def select_conversation(self, name):
        self.selected_conversation = name

    def deselect_conversation(self):
        self.selected_conversation = None

    def rename_conversation(self, old_name, new_name):
        old_path = os.path.join(self.conversations_dir, old_name)
        new_path = os.path.join(self.conversations_dir, new_name)
        if os.path.exists(new_path):
            return False
        os.rename(old_path, new_path)
        self.selected_conversation = new_name
        return True

    def delete_conversation(self, name):
        path = os.path.join(self.conversations_dir, name)
        try:
            shutil.rmtree(path)
            self.deselect_conversation()
            return True
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False

    def get_transcript_path(self):
        if not self.selected_conversation:
            return None
        return os.path.join(self.conversations_dir, self.selected_conversation, "transcript.txt")

    def get_transcript(self):
        transcript_path = self.get_transcript_path()
        if not transcript_path or not os.path.exists(transcript_path):
            return ""
        with open(transcript_path, 'r') as f:
            return f.read()

    def save_transcript(self, transcript):
        transcript_path = self.get_transcript_path()
        if transcript_path:
            with open(transcript_path, 'w') as f:
                f.write(transcript)

    def append_transcript(self, text):
        transcript_path = self.get_transcript_path()
        if transcript_path:
            with open(transcript_path, 'a') as f:
                f.write(f"{text}\n")

    def get_recording_path(self):
        if not self.selected_conversation:
            return None
        recordings_dir = os.path.join(self.conversations_dir, self.selected_conversation, "recordings")
        os.makedirs(recordings_dir, exist_ok=True)
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        return os.path.join(recordings_dir, f"recording_{timestamp}.wav")
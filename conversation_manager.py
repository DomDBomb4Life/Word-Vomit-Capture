# conversation_manager.py

import os
import shutil
import json
import time

class ConversationManager:
    def __init__(self):
        self.conversations_dir = "conversations"
        os.makedirs(self.conversations_dir, exist_ok=True)
        self.conversations_file = os.path.join(self.conversations_dir, "conversations.json")
        self.selected_conversation = None
        self.selected_conversation_path = None
        self.load_conversations()

    def load_conversations(self):
        if os.path.exists(self.conversations_file):
            with open(self.conversations_file, 'r') as f:
                self.conversations = json.load(f)
        else:
            self.conversations = {}

    def save_conversations(self):
        with open(self.conversations_file, 'w') as f:
            json.dump(self.conversations, f, indent=4)

    def get_conversations(self):
        # Returns the conversation hierarchy
        return self.conversations

    def create_folder(self, folder_name, parent_path=[]):
        node = self.conversations
        for part in parent_path:
            node = node.setdefault(part, {})
        if folder_name in node:
            return False
        node[folder_name] = {}
        self.save_conversations()
        return True

    def create_conversation(self, name, parent_path=[]):
        node = self.conversations
        for part in parent_path:
            node = node.setdefault(part, {})
        if name in node:
            return False
        node[name] = None  # Conversations are leaves with value None
        self.save_conversations()
        self.select_conversation(parent_path + [name])
        return True

    def select_conversation(self, path):
        self.selected_conversation = path[-1]
        self.selected_conversation_path = path

    def deselect_conversation(self):
        self.selected_conversation = None
        self.selected_conversation_path = None

    def rename_conversation(self, old_path, new_name):
        node = self.conversations
        for part in old_path[:-1]:
            node = node.get(part, {})
        if new_name in node:
            return False
        node[new_name] = node.pop(old_path[-1])
        self.save_conversations()
        self.selected_conversation = new_name
        self.selected_conversation_path = old_path[:-1] + [new_name]
        return True

    def delete_conversation(self, path):
        node = self.conversations
        for part in path[:-1]:
            node = node.get(part, {})
        try:
            del node[path[-1]]
            self.save_conversations()
            self.deselect_conversation()
            return True
        except KeyError:
            return False

    def get_transcript_path(self):
        if not self.selected_conversation_path:
            return None
        filename = "_".join(self.selected_conversation_path) + "_transcript.txt"
        return os.path.join(self.conversations_dir, filename)

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

    def get_recordings_dir(self):
        if not self.selected_conversation_path:
            return None
        dir_name = "_".join(self.selected_conversation_path) + "_recordings"
        recordings_dir = os.path.join(self.conversations_dir, dir_name)
        os.makedirs(recordings_dir, exist_ok=True)
        return recordings_dir

    def get_recording_path(self):
        recordings_dir = self.get_recordings_dir()
        if not recordings_dir:
            return None
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        return os.path.join(recordings_dir, f"recording_{timestamp}.wav")
    
    def get_conversation_last_modified(self, path):
        transcript_path = self.get_transcript_path_from_path(path)
        if os.path.exists(transcript_path):
            return os.path.getmtime(transcript_path)
        else:
            return 0  # Or some default value
    def get_transcript_path_from_path(self, path):
        filename = "_".join(path) + "_transcript.txt"
        return os.path.join(self.conversations_dir, filename)
    
    def get_transcripts(self):
        transcript_dir = self.get_transcript_dir()
        transcripts = []
        if os.path.exists(transcript_dir):
            for filename in sorted(os.listdir(transcript_dir)):
                if filename.endswith('.txt'):
                    filepath = os.path.join(transcript_dir, filename)
                    with open(filepath, 'r') as f:
                        text = f.read()
                    timestamp = filename.rstrip('.txt')
                    transcripts.append((timestamp, text))
        return transcripts

    def save_transcripts(self, transcripts):
        transcript_dir = self.get_transcript_dir()
        os.makedirs(transcript_dir, exist_ok=True)
        for timestamp, text in transcripts:
            filename = f"{timestamp}.txt"
            filepath = os.path.join(transcript_dir, filename)
            with open(filepath, 'w') as f:
                f.write(text)

    def get_transcript_dir(self):
        if not self.selected_conversation_path:
            return None
        dir_name = "_".join(self.selected_conversation_path) + "_transcripts"
        transcript_dir = os.path.join(self.conversations_dir, dir_name)
        return transcript_dir

    def append_transcript(self, text):
        transcripts = self.get_transcripts()
        transcripts.append((time.strftime('%Y-%m-%d %H:%M:%S'), text))
        self.save_transcripts(transcripts)
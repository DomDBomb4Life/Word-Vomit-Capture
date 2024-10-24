# conversation_manager.py

import os
import json
import time
import shutil

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
        return self.conversations

    def create_folder(self, folder_name, parent_path=[]):
        node = self.get_node(parent_path)
        if node is None:
            return False
        if folder_name in node:
            return False
        node[folder_name] = {}
        self.save_conversations()
        return True

    def create_conversation(self, name, parent_path=[]):
        node = self.get_node(parent_path)
        if node is None:
            return False
        if name in node:
            return False
        node[name] = None  # Conversations are leaves with value None
        self.save_conversations()
        self.select_conversation(parent_path + [name])
        return True

    def get_node(self, path):
        node = self.conversations
        for part in path:
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return None
        return node

    def select_conversation(self, path):
        self.selected_conversation = path[-1]
        self.selected_conversation_path = path

    def deselect_conversation(self):
        self.selected_conversation = None
        self.selected_conversation_path = None

    def rename_item(self, old_path, new_name):
        node = self.get_node(old_path[:-1])
        if node is None:
            return False
        if new_name in node:
            return False
        node[new_name] = node.pop(old_path[-1])
        self.save_conversations()
        # Also rename associated files and directories
        self.rename_associated_files(old_path, new_name)
        self.selected_conversation = new_name
        self.selected_conversation_path = old_path[:-1] + [new_name]
        return True

    def rename_associated_files(self, old_path, new_name):
        old_transcript_dir = self.get_transcript_dir_from_path(old_path)
        new_transcript_dir = self.get_transcript_dir_from_path(old_path[:-1] + [new_name])
        if os.path.exists(old_transcript_dir):
            os.rename(old_transcript_dir, new_transcript_dir)
        old_recordings_dir = self.get_recordings_dir_from_path(old_path)
        new_recordings_dir = self.get_recordings_dir_from_path(old_path[:-1] + [new_name])
        if os.path.exists(old_recordings_dir):
            os.rename(old_recordings_dir, new_recordings_dir)

    def delete_item(self, path):
        node = self.get_node(path[:-1])
        if node is None:
            return False
        try:
            del node[path[-1]]
            self.save_conversations()
            self.deselect_conversation()
            # Delete associated files and directories
            self.delete_associated_files(path)
            return True
        except KeyError:
            return False

    def delete_associated_files(self, path):
        # Delete transcripts and recordings
        transcript_dir = self.get_transcript_dir_from_path(path)
        if os.path.exists(transcript_dir):
            shutil.rmtree(transcript_dir)
        recordings_dir = self.get_recordings_dir_from_path(path)
        if os.path.exists(recordings_dir):
            shutil.rmtree(recordings_dir)

    def get_transcript_dir(self):
        return self.get_transcript_dir_from_path(self.selected_conversation_path)

    def get_transcript_dir_from_path(self, path):
        if not path:
            return None
        dir_name = "_".join(path) + "_transcripts"
        transcript_dir = os.path.join(self.conversations_dir, dir_name)
        return transcript_dir

    def get_recordings_dir(self):
        return self.get_recordings_dir_from_path(self.selected_conversation_path)

    def get_recordings_dir_from_path(self, path):
        if not path:
            return None
        dir_name = "_".join(path) + "_recordings"
        recordings_dir = os.path.join(self.conversations_dir, dir_name)
        return recordings_dir

    def append_transcript(self, text):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        transcripts = self.get_transcripts()
        transcripts.append((timestamp, text))
        self.save_transcripts(transcripts)

    def get_transcripts(self):
        transcript_dir = self.get_transcript_dir()
        transcripts = []
        if transcript_dir and os.path.exists(transcript_dir):
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
        if transcript_dir:
            os.makedirs(transcript_dir, exist_ok=True)
            # Clear existing transcripts
            for filename in os.listdir(transcript_dir):
                if filename.endswith('.txt'):
                    os.remove(os.path.join(transcript_dir, filename))
            # Save new transcripts
            for timestamp, text in transcripts:
                filename = f"{timestamp}.txt"
                filepath = os.path.join(transcript_dir, filename)
                with open(filepath, 'w') as f:
                    f.write(text)

    def get_conversation_last_modified(self, path):
        transcript_dir = self.get_transcript_dir_from_path(path)
        if os.path.exists(transcript_dir):
            return os.path.getmtime(transcript_dir)
        else:
            return 0
# ui_main.py

import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QInputDialog, QApplication
)
from PyQt5.QtCore import pyqtSignal, pyqtSlot
import os
import glob
import threading
from conversation_manager import ConversationManager
from conversation_tree import ConversationTree
from transcript_editor import TranscriptEditor
from recorder import Recorder
from transcriber import Transcriber
from config import OPENAI_API_KEY

class MainWindow(QMainWindow):
    transcription_complete = pyqtSignal(str)
    transcription_error = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conversation Recorder")
        self.resize(1000, 700)

        self.conversation_manager = ConversationManager()
        self.transcriber = Transcriber(OPENAI_API_KEY)
        self.recorder = None
        self.recording_thread = None
        self.recording = False

        self.setup_ui()

        # Connect signals for transcription results
        self.transcription_complete.connect(self.on_transcription_complete)
        self.transcription_error.connect(self.show_transcription_error)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()
        content_layout = QHBoxLayout()

        # Control Buttons
        self.new_folder_button = QPushButton("New Folder")
        self.new_conv_button = QPushButton("New Conversation")
        self.record_button = QPushButton("Start Recording")
        self.rename_button = QPushButton("Rename")
        self.delete_button = QPushButton("Delete")
        self.transcribe_file_button = QPushButton("Transcribe Audio File")

        control_layout.addWidget(self.new_folder_button)
        control_layout.addWidget(self.new_conv_button)
        control_layout.addWidget(self.record_button)
        control_layout.addWidget(self.rename_button)
        control_layout.addWidget(self.delete_button)
        control_layout.addWidget(self.transcribe_file_button)

        # Conversation Tree
        self.conversation_tree = ConversationTree(self.conversation_manager)
        self.conversation_tree.itemSelectionChanged.connect(self.on_conversation_select)

        # Transcript Editor
        self.transcript_editor = TranscriptEditor()
        self.transcript_editor.textChanged.connect(self.save_transcript)

        content_layout.addWidget(self.conversation_tree, 30)
        content_layout.addWidget(self.transcript_editor, 70)

        main_layout.addLayout(control_layout)
        main_layout.addLayout(content_layout)
        central_widget.setLayout(main_layout)

        # Disable buttons initially
        self.record_button.setEnabled(False)
        self.rename_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.transcribe_file_button.setEnabled(False)
        self.transcript_editor.setEnabled(False)

        # Connect signals
        self.new_folder_button.clicked.connect(self.create_new_folder)
        self.new_conv_button.clicked.connect(self.create_new_conversation)
        self.record_button.clicked.connect(self.toggle_recording)
        self.rename_button.clicked.connect(self.rename_item)
        self.delete_button.clicked.connect(self.delete_item)
        self.transcribe_file_button.clicked.connect(self.transcribe_audio_file)

    def create_new_folder(self):
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name:
            parent_path = self.conversation_tree.get_selected_path()
            success = self.conversation_manager.create_folder(folder_name, parent_path)
            if success:
                self.conversation_tree.refresh()
                QMessageBox.information(self, "Success", f"Folder '{folder_name}' created successfully.")
            else:
                QMessageBox.warning(self, "Error", "A folder with that name already exists.")
        elif not folder_name:
            QMessageBox.warning(self, "Invalid Name", "Folder name cannot be empty.")

    def create_new_conversation(self):
        conversation_name, ok = QInputDialog.getText(self, "New Conversation", "Enter conversation name:")
        if ok and conversation_name:
            parent_path = self.conversation_tree.get_selected_path()
            success = self.conversation_manager.create_conversation(conversation_name, parent_path)
            if success:
                self.conversation_tree.refresh()
                QMessageBox.information(self, "Success", f"Conversation '{conversation_name}' created successfully.")
            else:
                QMessageBox.warning(self, "Error", "A conversation with that name already exists.")
        elif not conversation_name:
            QMessageBox.warning(self, "Invalid Name", "Conversation name cannot be empty.")

    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        if not self.conversation_manager.selected_conversation_path:
            QMessageBox.warning(self, "No Conversation Selected", "Please select a conversation first.")
            return

        recordings_dir = self.conversation_manager.get_recordings_dir()
        self.recorder = Recorder(recordings_dir)
        self.recording_thread = threading.Thread(target=self.recorder.record, daemon=True)
        self.recording_thread.start()
        self.recording = True
        self.record_button.setText("Stop Recording")
        self.transcript_editor.setEnabled(False)

    def stop_recording(self):
        if self.recording:
            self.recorder.stop()
            self.recording_thread.join()
            self.recording = False
            self.record_button.setText("Start Recording")
            self.process_recording()

    def process_recording(self):
        threading.Thread(target=self.transcribe_audio, daemon=True).start()

    def transcribe_audio(self):
        recordings_dir = self.conversation_manager.get_recordings_dir()
        chunk_files = sorted(glob.glob(os.path.join(recordings_dir, "recording_chunk_*.wav")))

        def transcription_thread():
            all_transcripts = []
            for chunk_file in chunk_files:
                transcript_data = self.transcriber.transcribe(chunk_file)
                if transcript_data:
                    transcript_text = transcript_data.get('text', '')
                    all_transcripts.append(transcript_text)
                else:
                    self.transcription_error.emit()
                    return
            full_transcript = '\n'.join(all_transcripts)
            self.transcription_complete.emit(full_transcript)

        threading.Thread(target=transcription_thread, daemon=True).start()

    @pyqtSlot(str)
    def on_transcription_complete(self, transcript_text):
        self.conversation_manager.append_transcript(transcript_text)
        self.load_transcript()
        self.transcript_editor.setEnabled(True)

    @pyqtSlot()
    def show_transcription_error(self):
        QMessageBox.warning(self, "Transcription Failed", "Could not transcribe the audio.")
        self.transcript_editor.setEnabled(True)

    def rename_item(self):
        selected_path = self.conversation_tree.get_selected_path()
        if not selected_path:
            return
        new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=selected_path[-1])
        if ok and new_name and new_name != selected_path[-1]:
            success = self.conversation_manager.rename_conversation(selected_path, new_name)
            if success:
                self.conversation_tree.refresh()
                QMessageBox.information(self, "Success", f"Renamed to '{new_name}' successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to rename.")
        elif not new_name:
            QMessageBox.warning(self, "Invalid Name", "Name cannot be empty.")

    def delete_item(self):
        selected_item = self.conversation_tree.currentItem()
        if not selected_item:
            return
        item_name = selected_item.text(0)
        selected_path = self.conversation_tree.get_selected_path()
        reply = QMessageBox.question(
            self,
            "Delete",
            f"Are you sure you want to delete '{item_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success = self.conversation_manager.delete_conversation(selected_path)
            if success:
                self.conversation_tree.refresh()
                self.transcript_editor.clear()
                self.record_button.setEnabled(False)
                self.rename_button.setEnabled(False)
                self.delete_button.setEnabled(False)
                self.transcribe_file_button.setEnabled(False)
                self.transcript_editor.setEnabled(False)
                QMessageBox.information(self, "Success", f"Deleted '{item_name}' successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete.")

    def on_conversation_select(self):
        selected_path = self.conversation_tree.get_selected_path()
        if selected_path and self.conversation_tree.is_conversation(selected_path):
            self.conversation_manager.select_conversation(selected_path)
            self.load_transcript()
            self.record_button.setEnabled(True)
            self.rename_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.transcribe_file_button.setEnabled(True)
            self.transcript_editor.setEnabled(True)
        else:
            self.conversation_manager.deselect_conversation()
            self.transcript_editor.clear()
            self.record_button.setEnabled(False)
            self.rename_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.transcribe_file_button.setEnabled(False)
            self.transcript_editor.setEnabled(False)

    def load_transcript(self):
        transcripts = self.conversation_manager.get_transcripts()
        self.transcript_editor.set_transcripts(transcripts)

    def save_transcript(self):
        transcripts = self.transcript_editor.get_transcripts()
        self.conversation_manager.save_transcripts(transcripts)

    def transcribe_audio_file(self):
        # Implement as needed
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
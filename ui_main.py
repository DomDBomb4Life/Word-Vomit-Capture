# ui_main.py

import os
import threading
import glob
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QTextEdit, QMessageBox, QInputDialog, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from conversation_manager import ConversationManager
from recorder import Recorder
from transcriber import Transcriber
from config import OPENAI_API_KEY

class MainWindow(QMainWindow):
    # Define signals to handle background tasks
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
        self.load_conversations()

        # Connect signals for transcription results
        self.transcription_complete.connect(self.on_transcription_complete)
        self.transcription_error.connect(self.show_transcription_error)

    def setup_ui(self):
        # Main widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layouts
        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()
        content_layout = QHBoxLayout()
        transcript_control_layout = QHBoxLayout()

        # Control Buttons
        self.new_conv_button = QPushButton("New Conversation")
        self.record_button = QPushButton("Start Recording")
        self.rename_button = QPushButton("Rename Conversation")
        self.delete_button = QPushButton("Delete Conversation")
        self.transcribe_file_button = QPushButton("Transcribe Audio File")

        control_layout.addWidget(self.new_conv_button)
        control_layout.addWidget(self.record_button)
        control_layout.addWidget(self.rename_button)
        control_layout.addWidget(self.delete_button)
        control_layout.addWidget(self.transcribe_file_button)

        # Conversation List
        self.conversation_list = QListWidget()
        self.conversation_list.setMinimumWidth(200)

        # Transcript Editor
        self.transcript_editor = QTextEdit()
        self.transcript_editor.setAcceptRichText(False)
        self.transcript_editor.setUndoRedoEnabled(True)

        # Transcript Control Buttons (Optional: for additional functionalities)
        # For this example, we can leave it empty or add more buttons if needed

        content_layout.addWidget(self.conversation_list, 30)
        content_layout.addWidget(self.transcript_editor, 70)

        main_layout.addLayout(control_layout)
        main_layout.addLayout(content_layout)

        central_widget.setLayout(main_layout)

        # Disable buttons initially
        self.record_button.setEnabled(False)
        self.rename_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.transcribe_file_button.setEnabled(False)
        self.transcript_editor.setReadOnly(True)

        # Connect signals
        self.new_conv_button.clicked.connect(self.create_new_conversation)
        self.record_button.clicked.connect(self.toggle_recording)
        self.rename_button.clicked.connect(self.rename_conversation)
        self.delete_button.clicked.connect(self.delete_conversation)
        self.transcribe_file_button.clicked.connect(self.transcribe_audio_file)
        self.conversation_list.itemSelectionChanged.connect(self.on_conversation_select)
        self.transcript_editor.textChanged.connect(self.save_transcript)

    def load_conversations(self):
        self.conversation_list.clear()
        conversations = self.conversation_manager.get_conversations()
        self.conversation_list.addItems(conversations)
        if conversations:
            self.conversation_list.setCurrentRow(0)
            self.on_conversation_select()

    def create_new_conversation(self):
        conversation_name, ok = QInputDialog.getText(self, "New Conversation", "Enter conversation name:")
        if ok and conversation_name:
            success = self.conversation_manager.create_conversation(conversation_name)
            if success:
                self.load_conversations()
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
        if not self.conversation_manager.selected_conversation:
            QMessageBox.warning(self, "No Conversation Selected", "Please select or create a conversation first.")
            return

        recordings_dir = self.conversation_manager.get_recordings_dir()
        self.recorder = Recorder(recordings_dir)
        self.recording_thread = threading.Thread(target=self.recorder.record, daemon=True)
        self.recording_thread.start()
        self.recording = True
        self.record_button.setText("Stop Recording")
        self.transcript_editor.setReadOnly(True)

    def stop_recording(self):
        if self.recording:
            self.recorder.stop()
            self.recording_thread.join()
            self.recording = False
            self.record_button.setText("Start Recording")
            self.transcript_editor.setReadOnly(False)
            self.process_recording()

    def process_recording(self):
        # Run transcription in a separate thread
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
                    # Handle transcription failure
                    self.transcription_error.emit()
                    return
            # Combine all transcripts and emit the signal
            full_transcript = '\n'.join(all_transcripts)
            self.transcription_complete.emit(full_transcript)

        threading.Thread(target=transcription_thread, daemon=True).start()

    @pyqtSlot(str)
    def on_transcription_complete(self, transcript_text):
        self.conversation_manager.append_transcript(transcript_text)
        self.load_transcript()

    @pyqtSlot()
    def show_transcription_error(self):
        QMessageBox.warning(self, "Transcription Failed", "Could not transcribe the audio.")

    def rename_conversation(self):
        current_name = self.conversation_manager.selected_conversation
        if not current_name:
            return
        new_name, ok = QInputDialog.getText(self, "Rename Conversation", "Enter new name:", text=current_name)
        if ok and new_name and new_name != current_name:
            success = self.conversation_manager.rename_conversation(current_name, new_name)
            if success:
                self.load_conversations()
                QMessageBox.information(self, "Success", f"Conversation renamed to '{new_name}' successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to rename conversation.")
        elif not new_name:
            QMessageBox.warning(self, "Invalid Name", "Conversation name cannot be empty.")

    def delete_conversation(self):
        current_name = self.conversation_manager.selected_conversation
        if not current_name:
            return
        reply = QMessageBox.question(
            self,
            "Delete Conversation",
            f"Are you sure you want to delete '{current_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success = self.conversation_manager.delete_conversation(current_name)
            if success:
                self.load_conversations()
                self.transcript_editor.clear()
                self.record_button.setEnabled(False)
                self.rename_button.setEnabled(False)
                self.delete_button.setEnabled(False)
                self.transcribe_file_button.setEnabled(False)
                QMessageBox.information(self, "Success", f"Conversation '{current_name}' deleted successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete conversation.")

    def on_conversation_select(self):
        selected_items = self.conversation_list.selectedItems()
        if selected_items:
            conversation_name = selected_items[0].text()
            self.conversation_manager.select_conversation(conversation_name)
            self.load_transcript()
            self.record_button.setEnabled(True)
            self.rename_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.transcribe_file_button.setEnabled(True)
            # Check for untranscribed files
            self.check_untranscribed_files()
        else:
            self.conversation_manager.deselect_conversation()
            self.transcript_editor.clear()
            self.record_button.setEnabled(False)
            self.rename_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.transcribe_file_button.setEnabled(False)
            self.transcript_editor.setReadOnly(True)

    def load_transcript(self):
        transcript = self.conversation_manager.get_transcript()
        self.transcript_editor.blockSignals(True)
        self.transcript_editor.setPlainText(transcript)
        self.transcript_editor.blockSignals(False)

    def save_transcript(self):
        transcript = self.transcript_editor.toPlainText()
        self.conversation_manager.save_transcript(transcript)

    def transcribe_audio_file(self):
        if not self.conversation_manager.selected_conversation:
            QMessageBox.warning(self, "No Conversation Selected", "Please select a conversation first.")
            return

        recordings_dir = self.conversation_manager.get_recordings_dir()
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        audio_file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            recordings_dir,
            "Audio Files (*.wav)",
            options=options
        )
        if audio_file_path:
            # Transcribe the selected file
            threading.Thread(target=self.transcribe_selected_file, args=(audio_file_path,), daemon=True).start()

    def transcribe_selected_file(self, audio_file_path):
        def transcription_thread():
            transcript_data = self.transcriber.transcribe(audio_file_path)
            if transcript_data:
                transcript_text = transcript_data.get('text', '')
                self.transcription_complete.emit(transcript_text)
            else:
                self.transcription_error.emit()

        threading.Thread(target=transcription_thread, daemon=True).start()

    def check_untranscribed_files(self):
        recordings_dir = self.conversation_manager.get_recordings_dir()
        chunk_files = sorted(glob.glob(os.path.join(recordings_dir, "recording_chunk_*.wav")))

        if not chunk_files:
            return

        # For simplicity, assume any existing chunk files are untranscribed
        reply = QMessageBox.question(
            self,
            "Untranscribed Audio Files",
            "There are untranscribed audio files. Do you want to transcribe them now?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            threading.Thread(target=self.transcribe_audio, daemon=True).start()
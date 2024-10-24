# transcript_editor.py

from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QWidget, QTextEdit, QVBoxLayout, QAbstractItemView
from PyQt5.QtCore import Qt, pyqtSignal
import time

class TranscriptEditor(QWidget):
    textChanged = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.transcript_list = QListWidget()
        self.transcript_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.layout.addWidget(self.transcript_list)
        self.setLayout(self.layout)

    def clear(self):
        self.transcript_list.clear()

    def set_transcripts(self, transcripts):
        self.transcript_list.clear()
        for timestamp, text in transcripts:
            item = QListWidgetItem()
            item_widget = QTextEdit()
            item_widget.setPlainText(text)
            item_widget.setReadOnly(False)
            item_widget.setMinimumHeight(50)
            item_widget.setStyleSheet("background-color: #f0f0f0;")
            item.setSizeHint(item_widget.sizeHint())
            self.transcript_list.addItem(item)
            self.transcript_list.setItemWidget(item, item_widget)
            item.setData(Qt.UserRole, timestamp)
            # Add timestamp display
            item.setToolTip(f"Recorded on: {timestamp}")
            # Connect the textChanged signal
            item_widget.textChanged.connect(self.textChanged)

    def get_transcripts(self):
        transcripts = []
        for i in range(self.transcript_list.count()):
            item = self.transcript_list.item(i)
            widget = self.transcript_list.itemWidget(item)
            text = widget.toPlainText()
            timestamp = item.data(Qt.UserRole)
            transcripts.append((timestamp, text))
        return transcripts

    def append_transcript(self, text):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        item = QListWidgetItem()
        item_widget = QTextEdit()
        item_widget.setPlainText(text)
        item_widget.setReadOnly(False)
        item_widget.setMinimumHeight(50)
        item_widget.setStyleSheet("background-color: #f0f0f0;")
        item.setSizeHint(item_widget.sizeHint())
        self.transcript_list.addItem(item)
        self.transcript_list.setItemWidget(item, item_widget)
        item.setData(Qt.UserRole, timestamp)
        item.setToolTip(f"Recorded on: {timestamp}")
        item_widget.textChanged.connect(self.textChanged)

    def delete_selected_transcripts(self):
        selected_items = self.transcript_list.selectedItems()
        for item in selected_items:
            row = self.transcript_list.row(item)
            self.transcript_list.takeItem(row)
        self.textChanged.emit()
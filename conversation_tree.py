# conversation_tree.py

from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QAction
from PyQt5.QtCore import Qt

class ConversationTree(QTreeWidget):
    def __init__(self, conversation_manager):
        super().__init__()
        self.conversation_manager = conversation_manager
        self.setHeaderHidden(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)
        self.refresh()

    def refresh(self):
        self.clear()
        self.build_tree(self.conversation_manager.get_conversations(), self)

    def build_tree(self, data, parent, parent_path=[]):
        items = []
        for key, value in data.items():
            item = QTreeWidgetItem([key])
            full_path = parent_path + [key]
            if isinstance(value, dict):
                # Folder
                self.build_tree(value, item, full_path)
                # Get the latest modified time from children
                item_last_modified = max(
                    (child.data(0, 1) for child in self.iterate_children(item)),
                    default=0
                )
            else:
                # Conversation
                item_last_modified = self.conversation_manager.get_conversation_last_modified(full_path)
            item.setData(0, 1, item_last_modified)
            items.append((item_last_modified, item))
        # Sort items based on last modified time
        for _, item in sorted(items, key=lambda x: x[0], reverse=True):
            parent.addTopLevelItem(item) if parent == self else parent.addChild(item)

    def get_selected_path(self):
        item = self.currentItem()
        if item:
            path = []
            while item:
                path.insert(0, item.text(0))
                item = item.parent()
            return path
        return []

    def is_conversation(self, path):
        node = self.conversation_manager.get_node(path[:-1])
        return node.get(path[-1], {}) is None

    def iterate_children(self, item):
        for i in range(item.childCount()):
            child = item.child(i)
            yield child
            yield from self.iterate_children(child)

    def open_context_menu(self, position):
        indexes = self.selectedIndexes()
        if indexes:
            item = self.itemAt(position)
            if item:
                path = []
                while item:
                    path.insert(0, item.text(0))
                    item = item.parent()
                menu = QMenu()
                if self.is_conversation(path):
                    # Conversation context menu
                    delete_action = QAction('Delete', self)
                    rename_action = QAction('Rename', self)
                    transcribe_action = QAction('Transcribe Audio File', self)
                    menu.addAction(delete_action)
                    menu.addAction(rename_action)
                    menu.addAction(transcribe_action)
                    action = menu.exec_(self.viewport().mapToGlobal(position))
                    if action == delete_action:
                        self.parent().delete_item()
                    elif action == rename_action:
                        self.parent().rename_item()
                    elif action == transcribe_action:
                        self.parent().transcribe_audio_file()
                else:
                    # Folder context menu
                    new_folder_action = QAction('New Folder', self)
                    new_conv_action = QAction('New Conversation', self)
                    delete_action = QAction('Delete', self)
                    rename_action = QAction('Rename', self)
                    menu.addAction(new_folder_action)
                    menu.addAction(new_conv_action)
                    menu.addAction(rename_action)
                    menu.addAction(delete_action)
                    action = menu.exec_(self.viewport().mapToGlobal(position))
                    if action == new_folder_action:
                        self.parent().create_new_folder()
                    elif action == new_conv_action:
                        self.parent().create_new_conversation()
                    elif action == delete_action:
                        self.parent().delete_item()
                    elif action == rename_action:
                        self.parent().rename_item()
        else:
            # Blank space context menu
            menu = QMenu()
            new_folder_action = QAction('New Folder', self)
            menu.addAction(new_folder_action)
            action = menu.exec_(self.viewport().mapToGlobal(position))
            if action == new_folder_action:
                self.parent().create_new_folder()
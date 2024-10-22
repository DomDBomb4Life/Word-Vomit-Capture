# conversation_tree.py

from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem

class ConversationTree(QTreeWidget):
    def __init__(self, conversation_manager):
        super().__init__()
        self.conversation_manager = conversation_manager
        self.setHeaderHidden(True)
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
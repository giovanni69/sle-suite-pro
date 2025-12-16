from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QSplitter
)
from PySide6.QtCore import Qt
from gui.widgets.hex_editor import HexEditor


class CompareDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent

        # Window setup
        self.setWindowTitle(parent.tr("compare.title"))
        self.resize(1000, 600)

        # Hex editors
        self.left_editor = HexEditor()
        self.right_editor = HexEditor()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.left_editor)
        splitter.addWidget(self.right_editor)
        splitter.setSizes([500, 500])

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(splitter)

        # Controls
        controls = QHBoxLayout()
        layout.addLayout(controls)

        self.label_info = QLabel(parent.tr("compare.select_files"))
        controls.addWidget(self.label_info)

        self.btn_first = QPushButton(parent.tr("compare.select_first"))
        self.btn_first.clicked.connect(self.load_first_file)
        controls.addWidget(self.btn_first)

        self.btn_second = QPushButton(parent.tr("compare.select_second"))
        self.btn_second.clicked.connect(self.load_second_file)
        controls.addWidget(self.btn_second)

        self.btn_reset = QPushButton(parent.tr("compare.reset"))
        self.btn_reset.clicked.connect(self.reset_comparison)
        controls.addWidget(self.btn_reset)

        self.first_data = None
        self.second_data = None

    def load_first_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.parent_window.tr("compare.select_first"),
            "",
            self.parent_window.tr("compare.binary_files")
        )
        if path:
            with open(path, "rb") as f:
                self.first_data = f.read()
            self.left_editor.load_data(self.first_data)
            self.label_info.setText(self.parent_window.tr("compare.loaded_first").format(path=path))

    def load_second_file(self):
        if self.first_data is None:
            self.label_info.setText(self.parent_window.tr("compare.load_first_first"))
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            self.parent_window.tr("compare.select_second"),
            "",
            self.parent_window.tr("compare.binary_files")
        )
        if path:
            with open(path, "rb") as f:
                self.second_data = f.read()
            self.right_editor.load_data(self.second_data)
            self.label_info.setText(self.parent_window.tr("compare.loaded_second").format(path=path))
            self.highlight_differences()

    def highlight_differences(self):
        """Highlight differences between the two loaded dumps."""
        if not self.first_data or not self.second_data:
            return

        min_len = min(len(self.first_data), len(self.second_data))
        for idx in range(min_len):
            val_left = self.first_data[idx]
            val_right = self.second_data[idx]

            row = idx // 16
            col = idx % 16

            try:
                cell_right = self.right_editor.cells[row][col]
            except IndexError:
                continue

            if val_left != val_right:
                # Highlight difference in red text
                cell_right.setStyleSheet(
                    "background-color: #ffcccc; color: red; font-family: monospace;"
                )
                cell_right.setToolTip(f"{self.parent_window.tr('compare.original')}: {val_left:02X}")

        # Highlight extra bytes if second dump is longer
        for idx in range(len(self.first_data), len(self.second_data)):
            row = idx // 16
            col = idx % 16
            try:
                cell_right = self.right_editor.cells[row][col]
            except IndexError:
                continue
            cell_right.setStyleSheet("background-color: #ffcccc; color: red; font-family: monospace;")
            cell_right.setToolTip(self.parent_window.tr("compare.extra_byte"))

    def reset_comparison(self):
        """Reset both editors to original state."""
        if self.first_data:
            self.left_editor.load_data(self.first_data)
        if self.second_data:
            self.right_editor.load_data(self.second_data)
        self.label_info.setText(self.parent_window.tr("compare.reset_done"))

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

        self.setWindowTitle(parent.tr("compare.title"))
        self.resize(1000, 600)

        # Hex editors
        self.left_editor = HexEditor()
        self.right_editor = HexEditor()

        # Scrollbar sempre visibili se necessario
        self._show_scrollbars(self.left_editor)
        self._show_scrollbars(self.right_editor)

        self.left_editor.setEnabled(False)
        self.right_editor.setEnabled(False)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.left_editor)
        splitter.addWidget(self.right_editor)
        splitter.setSizes([500, 500])

        layout = QVBoxLayout(self)
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
        self.btn_second.setEnabled(False)
        controls.addWidget(self.btn_second)

        self.first_data = None
        self.second_data = None

    # -------------------------------------------------
    def _show_scrollbars(self, widget):
        """Mostra scrollbar verticali e orizzontali quando necessario."""
        for area in widget.findChildren(HexEditor):
            if hasattr(area, 'setHorizontalScrollBarPolicy'):
                area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            if hasattr(area, 'setVerticalScrollBarPolicy'):
                area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    # -------------------------------------------------
    def load_first_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.parent_window.tr("compare.select_first"),
            "",
            self.parent_window.tr("compare.binary_files")
        )
        if not path:
            return

        with open(path, "rb") as f:
            self.first_data = f.read()

        self.left_editor.clear()
        self.left_editor.setEnabled(True)
        self.left_editor.load_data(self.first_data)

        self.right_editor.clear()
        self.right_editor.setEnabled(False)
        self.second_data = None

        self.btn_second.setEnabled(True)
        self.label_info.setText(
            self.parent_window.tr("compare.loaded_first").format(path=path)
        )

    def load_second_file(self):
        if self.first_data is None:
            self.label_info.setText(
                self.parent_window.tr("compare.load_first_first")
            )
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            self.parent_window.tr("compare.select_second"),
            "",
            self.parent_window.tr("compare.binary_files")
        )
        if not path:
            return

        with open(path, "rb") as f:
            self.second_data = f.read()

        self.right_editor.clear()
        self.right_editor.setEnabled(True)
        self.right_editor.load_data(self.second_data)

        self.highlight_differences()

        self.label_info.setText(
            self.parent_window.tr("compare.loaded_second").format(path=path)
        )

    # -------------------------------------------------
    def highlight_differences(self):
        if not self.first_data or not self.second_data:
            return

        min_len = min(len(self.first_data), len(self.second_data))

        for idx in range(min_len):
            if self.first_data[idx] == self.second_data[idx]:
                continue

            row = idx // 16
            col = idx % 16

            try:
                cell = self.right_editor.cells[row][col]
            except Exception:
                continue

            cell.setStyleSheet(
                "background-color: #ffcccc; color: red; font-family: monospace;"
            )
            cell.setToolTip(
                f"{self.parent_window.tr('compare.original')}: {self.first_data[idx]:02X}"
            )

        for idx in range(len(self.first_data), len(self.second_data)):
            row = idx // 16
            col = idx % 16
            try:
                cell = self.right_editor.cells[row][col]
            except Exception:
                continue

            cell.setStyleSheet(
                "background-color: #ffcccc; color: red; font-family: monospace;"
            )
            cell.setToolTip(
                self.parent_window.tr("compare.extra_byte")
            )

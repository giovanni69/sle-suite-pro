from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QSplitter
)
from PySide6.QtCore import Qt
from gui.widgets.hex_editor import HexEditor


class CompareDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Compare Binary Dumps")
        self.resize(1000, 600)

        # Create two hex editors for left and right dumps
        self.left_editor = HexEditor()
        self.right_editor = HexEditor()

        # Splitter to show both editors side by side
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.left_editor)
        splitter.addWidget(self.right_editor)
        splitter.setSizes([500, 500])

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(splitter)

        # Controls layout
        controls = QHBoxLayout()
        layout.addLayout(controls)

        self.label_info = QLabel("Select two binary files to compare:")
        controls.addWidget(self.label_info)

        # Button to load the first file
        self.btn_first = QPushButton("Select First File")
        self.btn_first.clicked.connect(self.load_first_file)
        controls.addWidget(self.btn_first)

        # Button to load the second file
        self.btn_second = QPushButton("Select Second File")
        self.btn_second.clicked.connect(self.load_second_file)
        controls.addWidget(self.btn_second)

        # Button to reset the comparison
        self.btn_reset = QPushButton("Reset Comparison")
        self.btn_reset.clicked.connect(self.reset_comparison)
        controls.addWidget(self.btn_reset)

        self.first_data = None
        self.second_data = None

    def load_first_file(self):
        """Load the first binary file into the left hex editor."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select First File", "", "Binary Files (*.bin);;All Files (*)"
        )
        if path:
            with open(path, "rb") as f:
                self.first_data = f.read()
            self.left_editor.load_data(self.first_data)
            self.label_info.setText(f"Loaded first file: {path}")

    def load_second_file(self):
        """Load the second binary file into the right hex editor and highlight differences."""
        if self.first_data is None:
            self.label_info.setText("Load the first file before the second.")
            return

        path, _ = QFileDialog.getOpenFileName(
            self, "Select Second File", "", "Binary Files (*.bin);;All Files (*)"
        )
        if path:
            with open(path, "rb") as f:
                self.second_data = f.read()
            self.right_editor.load_data(self.second_data)
            self.label_info.setText(f"Loaded second file: {path}")
            self.highlight_differences()

    def highlight_differences(self):
        """Highlight only differing bytes in the right hex editor and make their text red."""
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
                # Highlight differences with red text and pink background
                cell_right.setStyleSheet(
                    "background-color: #ffcccc; color: red; font-weight: bold; font-family: monospace;"
                )
                cell_right.setToolTip(f"Original: {val_left:02X}")
            else:
                # Keep the default style (do not override black text)
                cell_right.setStyleSheet("font-family: monospace;")
                cell_right.setToolTip("")

        # Highlight extra bytes if the second dump is longer
        for idx in range(len(self.first_data), len(self.second_data)):
            row = idx // 16
            col = idx % 16
            try:
                cell_right = self.right_editor.cells[row][col]
            except IndexError:
                continue
            cell_right.setStyleSheet(
                "background-color: #ffcccc; color: red; font-weight: bold; font-family: monospace;"
            )
            cell_right.setToolTip("Extra byte")

    def reset_comparison(self):
        """Reset both editors to the original state, removing highlights."""
        if self.first_data:
            self.left_editor.load_data(self.first_data)
        if self.second_data:
            self.right_editor.load_data(self.second_data)
        self.label_info.setText("Comparison reset.")

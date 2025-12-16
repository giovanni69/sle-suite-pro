from PySide6.QtWidgets import QWidget, QGridLayout, QLineEdit, QLabel, QScrollArea, QVBoxLayout, QFrame
from PySide6.QtCore import Qt
import re


class HexEditor(QWidget):
    def __init__(self):
        super().__init__()

        self.data = bytearray()
        self.cells = []
        self.ascii_rows = []
        self.offset_labels = []

        self.header_color = "#e8e8e8"
        self.changed_bg_color = "#c8ffda"
        self.cell_width = 42

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.inner = QWidget()
        self.grid = QGridLayout()
        self.grid.setSpacing(2)
        self.grid.setContentsMargins(6, 6, 6, 6)
        self.grid.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.inner.setLayout(self.grid)

        self.scroll.setWidget(self.inner)

        wrapper = QVBoxLayout()
        wrapper.addWidget(self.scroll)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setLayout(wrapper)

    def clear(self):
        for row in self.cells:
            for cell in row:
                cell.deleteLater()

        for line in self.ascii_rows:
            line.deleteLater()

        for lbl in self.offset_labels:
            lbl.deleteLater()

        self.cells.clear()
        self.ascii_rows.clear()
        self.offset_labels.clear()
        self.data = bytearray()

        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def load_data(self, data: bytes):
        self.clear()

        self.data = bytearray(data)
        total = len(self.data)

        header_style = f"font-weight: bold; background:{self.header_color};"
        self.offset_headers = []

        # Vertical header "Offset"
        offset_header = QLabel("Offset")
        offset_header.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        offset_header.setStyleSheet(header_style + " padding-right:6px;")
        offset_header.setFixedWidth(60)
        self.grid.addWidget(offset_header, 0, 0)
        self.offset_headers.append(offset_header)

        # Numeric column headers (0..0F)
        for col in range(16):
            lbl = QLabel(f"{col:02X}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(header_style)
            lbl.setFixedWidth(self.cell_width)
            self.grid.addWidget(lbl, 0, col + 1)
            self.offset_headers.append(lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("color: #888888;")
        self.grid.addWidget(sep, 0, 17, 1, 1)

        ascii_header = QLabel("ASCII")
        ascii_header.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        ascii_header.setStyleSheet(header_style + " padding-left:8px;")
        self.grid.addWidget(ascii_header, 0, 18)
        self.ascii_header_label = ascii_header

        row = 1
        idx = 0

        while idx < total:
            offset_lbl = QLabel(f"{idx:04X}")
            offset_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            offset_lbl.setStyleSheet(header_style + " padding-right:6px;")
            offset_lbl.setFixedWidth(60)
            self.grid.addWidget(offset_lbl, row, 0)
            self.offset_labels.append(offset_lbl)

            row_cells = []

            for col in range(16):
                if idx >= total:
                    break

                val = self.data[idx]
                text = f"{val:02X}"

                cell = _HexCell(self, idx, text)
                cell.setAlignment(Qt.AlignCenter)
                cell.setFixedWidth(self.cell_width)
                cell.setMaxLength(2)
                cell.setStyleSheet("font-family: monospace;")
                self.grid.addWidget(cell, row, col + 1)
                row_cells.append(cell)

                idx += 1

            self.cells.append(row_cells)

            ascii_text = []
            base_index = (row - 1) * 16
            for col in range(16):
                byte_index = base_index + col
                if byte_index >= len(self.data):
                    break
                b = self.data[byte_index]
                ch = chr(b) if 32 <= b < 127 else "."
                ascii_text.append(ch)

            ascii_line = QLineEdit("".join(ascii_text))
            ascii_line.setReadOnly(True)
            ascii_line.setFrame(False)
            ascii_line.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            ascii_line.setStyleSheet(
                "font-family: monospace; padding-left:8px; background: transparent;"
            )
            self.grid.addWidget(ascii_line, row, 18)
            self.ascii_rows.append(ascii_line)

            row += 1

        # Force black color on all headers
        self.force_headers_black()

    def write_cell(self, index: int, new_text: str):
        row = index // 16
        col = index % 16

        try:
            cell = self.cells[row][col]
        except IndexError:
            return

        raw = new_text.strip()
        old_val = self.data[index] if index < len(self.data) else 0

        if raw == "":
            val = 0xFF
            normalized = "FF"
        else:
            try:
                val = int(raw, 16) & 0xFF
                normalized = f"{val:02X}"
            except ValueError:
                val = 0xFF
                normalized = "FF"

        cell.blockSignals(True)
        cell.setText(normalized)
        cell.blockSignals(False)

        if val != old_val:
            cell.setStyleSheet(
                f"background-color: {self.changed_bg_color}; "
                f"color: black; "
                f"font-weight: bold; "
                f"font-family: monospace;"
            )
        else:
            cell.setStyleSheet("font-family: monospace;")

        if index < len(self.data):
            self.data[index] = val

            try:
                ascii_line = self.ascii_rows[row]
            except IndexError:
                return

            ascii_chars = []
            base_index = row * 16
            for c in range(16):
                byte_index = base_index + c
                if byte_index >= len(self.data):
                    break
                b = self.data[byte_index]
                ch = chr(b) if 32 <= b < 127 else "."
                ascii_chars.append(ch)

            ascii_line.setText("".join(ascii_chars))

    def get_bytes(self) -> bytes:
        return bytes(self.data)

    def commit_all(self):
        for row_idx, row in enumerate(self.cells):
            for col_idx, cell in enumerate(row):
                index = row_idx * 16 + col_idx
                if index >= len(self.data):
                    break
                self.write_cell(index, cell.text())

    def clear_comparison(self):
        """Remove comparison highlights from all cells."""
        for row in self.cells:
            for cell in row:
                # Restore default style (keep monospace)
                cell.setStyleSheet("font-family: monospace;")
        # Show ASCII column again
        self.show_ascii()

    def compare_with(self, other_data: bytes):
        """
        Compare current data with another binary dump and highlight differences.
        Differences are shown with a red background.
        The ASCII column is hidden during comparison.
        """
        self.clear_comparison()  # Remove previous highlights
        self.hide_ascii()        # Hide ASCII column

        min_len = min(len(self.data), len(other_data))

        # Compare overlapping bytes
        for idx in range(min_len):
            current_val = self.data[idx]
            other_val = other_data[idx]

            row = idx // 16
            col = idx % 16

            try:
                cell = self.cells[row][col]
            except IndexError:
                continue

            if current_val != other_val:
                # Highlight differences with red background
                cell.setStyleSheet(
                    "background-color: #ffcccc; font-family: monospace;"
                )
            else:
                # Keep default style
                cell.setStyleSheet("font-family: monospace;")

        # Highlight extra bytes if other_data is longer
        if len(other_data) > len(self.data):
            for idx in range(len(self.data), len(other_data)):
                row = idx // 16
                col = idx % 16
                try:
                    cell = self.cells[row][col]
                except IndexError:
                    continue
                cell.setStyleSheet(
                    "background-color: #ffcccc; font-family: monospace;"
                )

    def hide_ascii(self):
        """Hide ASCII column during comparison."""
        if hasattr(self, "ascii_header_label"):
            self.ascii_header_label.hide()
        for line in self.ascii_rows:
            line.hide()


    def show_ascii(self):
        """Show ASCII column."""
        if hasattr(self, "ascii_header_label"):
            self.ascii_header_label.show()
        for line in self.ascii_rows:
            line.show()

    def force_headers_black(self):
        """
        Force black color on all headers:
        - Vertical and horizontal offset headers
        - 'ASCII' label
        Keeps other styles intact.
        """
        all_headers = self.offset_labels + getattr(self, "offset_headers", [])
        if hasattr(self, "ascii_header_label") and self.ascii_header_label:
            all_headers.append(self.ascii_header_label)

        for lbl in all_headers:
            current_style = lbl.styleSheet()
            if "color:" in current_style:
                new_style = re.sub(r"color:\s*[^;]+;", "color: black;", current_style)
            else:
                new_style = current_style + " color: black;"
            lbl.setStyleSheet(new_style)


class _HexCell(QLineEdit):
    def __init__(self, editor: HexEditor, index: int, text: str):
        super().__init__(text)
        self.editor = editor
        self.index = index

    def focusOutEvent(self, event):
        self.editor.write_cell(self.index, self.text())
        super().focusOutEvent(event)

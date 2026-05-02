import sys
import re
from PySide6.QtWidgets import (QApplication, QMainWindow, QSplitter,
                             QPlainTextEdit, QVBoxLayout, QWidget, QLabel)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import Qt

class PathDataViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LICGX PathData Viewer 1.0")
        self.resize(1100, 700)

        splitter = QSplitter(Qt.Horizontal)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Enter XML here...")
        self.editor.setStyleSheet("""
            QPlainTextEdit {
                font-family: 'Consolas', 'Cascadia Code', monospace;
                font-size: 14px;
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                padding: 15px;
            }
        """)
        self.editor.textChanged.connect(self.update_preview)

        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)

        self.svg_display = QSvgWidget()

        self.info_label = QLabel("Waiting for XML.")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("""
            color: #aaaaaa;
            font-family: sans-serif;
            font-size: 11px;
            background: #252526;
            padding: 5px;
        """)

        preview_container.setStyleSheet(
            "background-color: #2d2d2d; border-left: 1px solid #3e3e3e;"
        )

        preview_layout.addWidget(self.svg_display, stretch=1)
        preview_layout.addWidget(self.info_label)

        splitter.addWidget(self.editor)
        splitter.addWidget(preview_container)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

    def parse_android_xml(self, xml_text):
        """Parses VectorDrawable and translating it into bytecode."""
        try:
            v_w = re.search(r'android:viewportWidth="([\d.]+)"', xml_text)
            v_h = re.search(r'android:viewportHeight="([\d.]+)"', xml_text)

            if not v_w or not v_h:
                return None

            vw, vh = v_w.group(1), v_h.group(1)

            path_blocks = re.findall(r'<path.*?\/>', xml_text, re.DOTALL)
            svg_paths = []

            for block in path_blocks:
                d_match = re.search(r'android:pathData="([^"]+)"', block)

                if not d_match:
                    continue

                d = d_match.group(1)

                # Fill color.
                fill_match = re.search(r'android:fillColor="([^"]+)"', block)

                if fill_match:
                    fill = fill_match.group(1)
                else:
                    fill = "none"

                # Alpha.
                alpha_match = re.search(r'android:fillAlpha="([\d.]+)"', block)
                alpha = alpha_match.group(1) if alpha_match else "1"

                # Android Hex Alpha (#AARRGGBB -> #RRGGBB + opacity)
                if fill.startswith("#") and len(fill) == 9:
                    a = int(fill[1:3], 16) / 255
                    fill = "#" + fill[3:]
                    alpha = str(a)

                # Stroke color.
                stroke_match = re.search(r'android:strokeColor="([^"]+)"', block)

                if stroke_match:
                    stroke = stroke_match.group(1)
                else:
                    stroke = "none"

                # Stroke alpha.
                stroke_alpha_match = re.search(r'android:strokeAlpha="([\d.]+)"', block)
                stroke_alpha = stroke_alpha_match.group(1) if stroke_alpha_match else "1"

                # Android Hex Alpha (#AARRGGBB -> #RRGGBB + opacity)
                if stroke.startswith("#") and len(stroke) == 9:
                    a = int(stroke[1:3], 16) / 255
                    stroke = "#" + stroke[3:]
                    stroke_alpha = str(a)

                # Stroke width.
                stroke_width_match = re.search(r'android:strokeWidth="([\d.]+)"', block)
                stroke_width = stroke_width_match.group(1) if stroke_width_match else "0"

                # Stroke line cap.
                linecap_match = re.search(r'android:strokeLineCap="([^"]+)"', block)
                linecap = linecap_match.group(1) if linecap_match else "butt"

                svg_paths.append(
                    f'<path d="{d}" '
                    f'fill="{fill}" '
                    f'fill-opacity="{alpha}" '
                    f'stroke="{stroke}" '
                    f'stroke-width="{stroke_width}" '
                    f'stroke-opacity="{stroke_alpha}" '
                    f'stroke-linecap="{linecap}" />'
                )

            if not svg_paths:
                return None

            svg_template = f"""
            <svg viewBox="0 0 {vw} {vh}" xmlns="http://www.w3.org/2000/svg">
                {"".join(svg_paths)}
            </svg>
            """

            return svg_template.strip().encode('utf-8')

        except Exception as e:
            print(f"Parse failed: {e}")
            return None

    def update_preview(self):
        xml_content = self.editor.toPlainText()

        if not xml_content.strip():
            self.info_label.setText("Nothing here...")
            return

        svg_data = self.parse_android_xml(xml_content)

        if svg_data:
            self.svg_display.load(svg_data)
            self.info_label.setText("Succesful!")
        else:
            self.info_label.setText("No viewport or XML error.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    ui = PathDataViewer()
    ui.show()

    sys.exit(app.exec())

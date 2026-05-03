import sys
import re
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QSplitter,
    QPlainTextEdit, QVBoxLayout, QWidget,
    QLabel, QPushButton, QFileDialog,
    QHBoxLayout
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QImage, QPainter


class PathDataViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LICGX PathData Viewer 1.1")
        self.resize(1100, 700)

        self.current_svg_data = None

        splitter = QSplitter(Qt.Horizontal)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Enter XML here...")
        self.editor.setAcceptDrops(False)
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

        # Buttons.
        button_layout = QHBoxLayout()

        self.export_svg_btn = QPushButton("Export to SVG")
        self.export_png_btn = QPushButton("Export to PNG")

        self.export_svg_btn.clicked.connect(self.export_svg)
        self.export_png_btn.clicked.connect(self.export_png)

        self.export_svg_btn.setStyleSheet("""
            QPushButton {
                background: #3c3c3c;
                color: white;
                border: 1px solid #555;
                padding: 8px;
            }
            QPushButton:hover {
                background: #4a4a4a;
            }
        """)

        self.export_png_btn.setStyleSheet("""
            QPushButton {
                background: #3c3c3c;
                color: white;
                border: 1px solid #555;
                padding: 8px;
            }
            QPushButton:hover {
                background: #4a4a4a;
            }
        """)

        button_layout.addWidget(self.export_svg_btn)
        button_layout.addWidget(self.export_png_btn)

        preview_container.setStyleSheet(
            "background-color: #2d2d2d; border-left: 1px solid #3e3e3e;"
        )

        preview_layout.addLayout(button_layout)
        preview_layout.addWidget(self.svg_display, stretch=1)
        preview_layout.addWidget(self.info_label)

        splitter.addWidget(self.editor)
        splitter.addWidget(preview_container)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

        # Drag and drop.
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()

        if not urls:
            return

        file_path = urls[0].toLocalFile()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract vector drawable.
            vector_match = re.search(
                r'<vector.*?</vector>',
                content,
                re.DOTALL
            )

            if vector_match:
                self.editor.setPlainText(vector_match.group(0))
            else:
                self.editor.setPlainText(content)

            self.info_label.setText(f"Loaded: {file_path}")

        except Exception as e:
            self.info_label.setText(f"Drop failed: {e}")

    def parse_android_xml(self, xml_text):
        """Parses VectorDrawable and translating it into bytecode."""

        try:
            v_w = re.search(r'android:viewportWidth="([\d.]+)"', xml_text)
            v_h = re.search(r'android:viewportHeight="([\d.]+)"', xml_text)

            if not v_w or not v_h:
                return None

            vw, vh = v_w.group(1), v_h.group(1)

            path_blocks = re.findall(r'<path.*?/>', xml_text, re.DOTALL)
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

                # Stroke line join.
                linejoin_match = re.search(r'android:strokeLineJoin="([^"]+)"', block)
                linejoin = linejoin_match.group(1) if linejoin_match else "miter"

                # Trim path.
                trim_start_match = re.search(r'android:trimPathStart="([\d.]+)"', block)
                trim_end_match = re.search(r'android:trimPathEnd="([\d.]+)"', block)

                trim_start = float(trim_start_match.group(1)) if trim_start_match else 0
                trim_end = float(trim_end_match.group(1)) if trim_end_match else 1

                dash_array = ""

                if trim_start != 0 or trim_end != 1:
                    visible = max(trim_end - trim_start, 0.01)
                    hidden = 1 - visible
                    dash_array = f'stroke-dasharray="{visible * 100} {hidden * 100}"'

                # Gradient support.
                gradient_fill = ""

                gradient_match = re.search(r'<gradient.*?android:startColor="([^"]+)".*?android:endColor="([^"]+)".*?/>', block, re.DOTALL)

                if gradient_match:
                    start_color = gradient_match.group(1)
                    end_color = gradient_match.group(2)

                    gradient_fill = f'''
                    <defs>
                        <linearGradient id="grad">
                            <stop offset="0%" stop-color="{start_color}"/>
                            <stop offset="100%" stop-color="{end_color}"/>
                        </linearGradient>
                    </defs>
                    '''

                    fill = "url(#grad)"

                svg_paths.append(
                    f'''
                    {gradient_fill}
                    <path d="{d}"
                        fill="{fill}"
                        fill-opacity="{alpha}"
                        stroke="{stroke}"
                        stroke-width="{stroke_width}"
                        stroke-opacity="{stroke_alpha}"
                        stroke-linecap="{linecap}"
                        stroke-linejoin="{linejoin}"
                        {dash_array} />
                    '''
                )

            if not svg_paths:
                return None

            svg_template = f"""
            <svg viewBox="0 0 {vw} {vh}" xmlns="http://www.w3.org/2000/svg">
                {''.join(svg_paths)}
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
            self.current_svg_data = svg_data
            self.svg_display.load(svg_data)
            self.info_label.setText("Succesful!")
        else:
            self.info_label.setText("No viewport or XML error.")

    def export_svg(self):
        if not self.current_svg_data:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export SVG",
            "output.svg",
            "SVG Files (*.svg)"
        )

        if not file_path:
            return

        with open(file_path, "wb") as f:
            f.write(self.current_svg_data)

        self.info_label.setText(f"SVG exported: {file_path}")

    def export_png(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export PNG",
            "output.png",
            "PNG Files (*.png)"
        )

        if not file_path:
            return

        image = QImage(
            self.svg_display.size(),
            QImage.Format_ARGB32
        )

        image.fill(Qt.transparent)

        painter = QPainter(image)
        self.svg_display.renderer().render(painter)
        painter.end()

        image.save(file_path)

        self.info_label.setText(f"PNG exported: {file_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    ui = PathDataViewer()
    ui.show()

    sys.exit(app.exec())


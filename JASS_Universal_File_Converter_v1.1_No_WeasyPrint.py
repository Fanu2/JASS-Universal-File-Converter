#!/usr/bin/env python3
"""
JASS Universal File Converter
PySide6 desktop application for converting common document/text/image formats.

Core conversions:
- Markdown (.md/.markdown) <-> HTML / TXT
- Markdown -> PDF
- HTML -> PDF (WeasyPrint if installed, otherwise basic ReportLab fallback)
- TXT -> Markdown / HTML / PDF
- PDF -> TXT (pypdf)
- Images -> PDF (Pillow)
- DOCX / ODT / RTF / EPUB / DOC -> PDF/HTML/TXT/etc. through Pandoc when installed

Optional packages:
    pip install PySide6 markdown reportlab pypdf pillow
For broad format support:
    Install Pandoc: https://pandoc.org/installing.html
PDF engine:
    ReportLab (no GTK/WeasyPrint dependency)
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QCheckBox,
    QSplitter, QStatusBar, QVBoxLayout, QWidget
)

APP_NAME = "JASS Universal File Converter"


def import_optional():
    mods = {}
    try:
        import markdown
        mods["markdown"] = markdown
    except ImportError:
        mods["markdown"] = None
    try:
        import reportlab
        mods["reportlab"] = reportlab
    except ImportError:
        mods["reportlab"] = None
    try:
        import pypdf
        mods["pypdf"] = pypdf
    except ImportError:
        mods["pypdf"] = None
    try:
        from PIL import Image
        mods["PIL"] = Image
    except ImportError:
        mods["PIL"] = None
    return mods


def pandoc_path():
    return shutil.which("pandoc")


def markdown_to_html(md_text):
    mods = import_optional()
    if mods["markdown"]:
        return mods["markdown"].markdown(
            md_text,
            extensions=["extra", "tables", "fenced_code", "sane_lists", "toc"]
        )
    # Small built-in fallback for headings, lists and code.
    html = []
    in_code = False
    for line in md_text.splitlines():
        if line.startswith("```"):
            in_code = not in_code
            html.append("</code></pre>" if not in_code else "<pre><code>")
            continue
        if in_code:
            html.append(
                line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            )
            continue
        if not line.strip():
            html.append("<p></p>")
        elif re.match(r"^#{1,6}\s+", line):
            m = re.match(r"^(#{1,6})\s+(.*)", line)
            level = len(m.group(1))
            html.append(f"<h{level}>{m.group(2)}</h{level}>")
        elif re.match(r"^[-*]\s+", line):
            html.append("<li>" + re.sub(r"^[-*]\s+", "", line) + "</li>")
        else:
            # Basic inline formatting.
            x = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            x = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", x)
            x = re.sub(r"\*(.+?)\*", r"<em>\1</em>", x)
            html.append("<p>" + x + "</p>")
    return "\n".join(html)


def wrap_html(body, title="Converted Document"):
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
@page {{ size: A4; margin: 18mm; }}
body {{ font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.45; color:#202124; }}
h1,h2,h3,h4 {{ color:#163a5f; }}
h1 {{ font-size: 21pt; }}
h2 {{ font-size: 16pt; }}
h3 {{ font-size: 13pt; }}
table {{ border-collapse: collapse; width:100%; }}
th,td {{ border:1px solid #aaa; padding:5px; }}
pre {{ background:#f3f5f7; padding:8px; white-space:pre-wrap; }}
code {{ font-family: monospace; }}
blockquote {{ border-left:4px solid #8aa; padding-left:10px; color:#555; }}
</style>
</head>
<body>
{body}
</body>
</html>"""


def basic_pdf_from_text(text, output):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
    from reportlab.lib.units import mm
    from xml.sax.saxutils import escape

    styles = getSampleStyleSheet()
    normal = ParagraphStyle(
        "JASSNormal", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=10, leading=14, spaceAfter=5
    )
    h1 = ParagraphStyle("JASSH1", parent=normal, fontSize=18, leading=22,
                        spaceBefore=8, spaceAfter=8)
    h2 = ParagraphStyle("JASSH2", parent=normal, fontSize=14, leading=18,
                        spaceBefore=6, spaceAfter=5)
    story = []

    for line in text.splitlines():
        if line.startswith("# "):
            story.append(Paragraph(escape(line[2:]), h1))
        elif line.startswith("## "):
            story.append(Paragraph(escape(line[3:]), h2))
        elif line.startswith("### "):
            story.append(Paragraph(escape(line[4:]), normal))
        elif line.startswith("```"):
            continue
        elif not line.strip():
            story.append(Spacer(1, 4))
        else:
            x = escape(line)
            x = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", x)
            x = re.sub(r"\*(.+?)\*", r"<i>\1</i>", x)
            story.append(Paragraph(x, normal))

    doc = SimpleDocTemplate(
        str(output), pagesize=A4,
        rightMargin=18*mm, leftMargin=18*mm,
        topMargin=18*mm, bottomMargin=18*mm
    )
    doc.build(story)


def html_to_pdf(html, output):
    """Convert HTML to a readable PDF without WeasyPrint/GTK.

    ReportLab is used for the PDF. BeautifulSoup is optional; if unavailable,
    a simple tag stripper is used.
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Preserve basic structure by turning headings into Markdown-like
        # markers before feeding the text renderer.
        for tag in soup.find_all(["h1", "h2", "h3"]):
            prefix = {"h1": "# ", "h2": "## ", "h3": "### "}[tag.name]
            tag.insert_before(prefix)
            tag.append("\n")

        plain = soup.get_text("\n")
    except ImportError:
        plain = re.sub(r"<[^>]+>", "", html)
        plain = re.sub(r"\n\s*\n+", "\n\n", plain)

    basic_pdf_from_text(plain, output)
    return "ReportLab"


def convert_one(source, destination, target_ext):
    source = Path(source)
    destination = Path(destination)
    src_ext = source.suffix.lower()
    target_ext = target_ext.lower()

    destination.parent.mkdir(parents=True, exist_ok=True)

    # Same-format copy is useful for batch jobs.
    if src_ext == target_ext:
        shutil.copy2(source, destination)
        return "Copied"

    # Markdown / text family
    if src_ext in (".md", ".markdown") and target_ext == ".html":
        body = markdown_to_html(source.read_text(encoding="utf-8", errors="replace"))
        destination.write_text(
            wrap_html(body, source.stem), encoding="utf-8"
        )
        return "Markdown → HTML"

    if src_ext in (".md", ".markdown") and target_ext == ".txt":
        destination.write_text(
            source.read_text(encoding="utf-8", errors="replace"),
            encoding="utf-8"
        )
        return "Markdown → TXT"

    if src_ext in (".md", ".markdown") and target_ext == ".pdf":
        text = source.read_text(encoding="utf-8", errors="replace")
        # Deliberately use ReportLab only. No WeasyPrint/GTK dependency.
        basic_pdf_from_text(text, destination)
        return "Markdown → PDF (ReportLab)"

    if src_ext == ".txt" and target_ext == ".md":
        destination.write_text(
            source.read_text(encoding="utf-8", errors="replace"),
            encoding="utf-8"
        )
        return "TXT → Markdown"

    if src_ext == ".txt" and target_ext == ".html":
        from html import escape
        text = source.read_text(encoding="utf-8", errors="replace")
        body = "<pre>" + escape(text) + "</pre>"
        destination.write_text(wrap_html(body, source.stem), encoding="utf-8")
        return "TXT → HTML"

    if src_ext == ".txt" and target_ext == ".pdf":
        basic_pdf_from_text(
            source.read_text(encoding="utf-8", errors="replace"), destination
        )
        return "TXT → PDF"

    if src_ext in (".html", ".htm") and target_ext == ".pdf":
        return f"HTML → PDF ({html_to_pdf(source.read_text(encoding='utf-8', errors='replace'), destination)})"

    if src_ext in (".html", ".htm") and target_ext == ".txt":
        try:
            from bs4 import BeautifulSoup
            txt = BeautifulSoup(
                source.read_text(encoding="utf-8", errors="replace"), "html.parser"
            ).get_text("\n")
        except ImportError:
            txt = re.sub(r"<[^>]+>", "", source.read_text(encoding="utf-8", errors="replace"))
        destination.write_text(txt, encoding="utf-8")
        return "HTML → TXT"

    # PDF -> TXT
    if src_ext == ".pdf" and target_ext == ".txt":
        mods = import_optional()
        if not mods["pypdf"]:
            raise RuntimeError("PDF → TXT requires pypdf: pip install pypdf")
        reader = mods["pypdf"].PdfReader(str(source))
        txt = "\n\n".join(page.extract_text() or "" for page in reader.pages)
        destination.write_text(txt, encoding="utf-8")
        return "PDF → TXT"

    # Images -> PDF
    image_exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}
    if src_ext in image_exts and target_ext == ".pdf":
        mods = import_optional()
        if not mods["PIL"]:
            raise RuntimeError("Image → PDF requires Pillow: pip install pillow")
        im = mods["PIL"].open(source)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGB")
        im.save(destination, "PDF", resolution=150.0)
        return "Image → PDF"

    # Pandoc handles the broad document conversion matrix.
    if pandoc_path():
        cmd = [
            pandoc, str(source), "-o", str(destination),
            "--standalone"
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return "Pandoc"

    raise RuntimeError(
        f"No built-in converter for {src_ext} → {target_ext}. "
        "Install Pandoc for broader document formats."
    )


class Worker(QThread):
    progress = Signal(int)
    message = Signal(str)
    finished_ok = Signal(int, int)
    failed = Signal(str)

    def __init__(self, files, out_dir, target_ext):
        super().__init__()
        self.files = files
        self.out_dir = Path(out_dir)
        self.target_ext = target_ext

    def run(self):
        ok = failed = 0
        total = len(self.files)
        for i, source in enumerate(self.files, 1):
            src = Path(source)
            dest = self.out_dir / f"{src.stem}{self.target_ext}"
            # Avoid accidental overwrite by adding a number.
            if dest.resolve() == src.resolve():
                dest = self.out_dir / f"{src.stem}_converted{self.target_ext}"
            base = dest
            n = 2
            while dest.exists():
                dest = base.with_name(f"{base.stem}_{n}{base.suffix}")
                n += 1
            try:
                result = convert_one(src, dest, self.target_ext)
                ok += 1
                self.message.emit(f"✓ {src.name} → {dest.name}  [{result}]")
            except Exception as exc:
                failed += 1
                self.message.emit(f"✗ {src.name}: {exc}")
            self.progress.emit(int(i * 100 / total))
        self.finished_ok.emit(ok, failed)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1050, 720)
        self.files = []
        self.worker = None
        self.build_ui()
        self.refresh_status()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(9)

        header = QFrame()
        header.setObjectName("Header")
        hl = QVBoxLayout(header)
        title = QLabel("JASS Universal File Converter")
        title.setObjectName("Title")
        subtitle = QLabel(
            "Batch convert documents, text, Markdown, PDFs, HTML and images — "
            "with Pandoc integration for wider format support."
        )
        subtitle.setObjectName("Subtitle")
        hl.addWidget(title)
        hl.addWidget(subtitle)
        root.addWidget(header)

        controls = QGroupBox("1. Choose files")
        gl = QGridLayout(controls)
        self.add_btn = QPushButton("＋ Add Files")
        self.add_folder_btn = QPushButton("＋ Add Folder")
        self.clear_btn = QPushButton("Clear")
        self.add_btn.clicked.connect(self.add_files)
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.clear_btn.clicked.connect(self.clear_files)
        gl.addWidget(self.add_btn, 0, 0)
        gl.addWidget(self.add_folder_btn, 0, 1)
        gl.addWidget(self.clear_btn, 0, 2)
        self.file_count = QLabel("0 files")
        gl.addWidget(self.file_count, 0, 3)
        root.addWidget(controls)

        splitter = QSplitter(Qt.Horizontal)
        left = QWidget()
        ll = QVBoxLayout(left)
        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.ExtendedSelection)
        ll.addWidget(self.list)
        splitter.addWidget(left)

        right = QWidget()
        rl = QVBoxLayout(right)

        format_box = QGroupBox("2. Conversion")
        fg = QGridLayout(format_box)
        fg.addWidget(QLabel("Output format:"), 0, 0)
        self.format_combo = QComboBox()
        self.formats = [
            ("PDF", ".pdf"),
            ("Markdown", ".md"),
            ("HTML", ".html"),
            ("Plain Text", ".txt"),
            ("DOCX", ".docx"),
            ("ODT", ".odt"),
            ("RTF", ".rtf"),
            ("EPUB", ".epub"),
        ]
        for name, ext in self.formats:
            self.format_combo.addItem(f"{name}  ({ext})", ext)
        fg.addWidget(self.format_combo, 0, 1)
        self.output_btn = QPushButton("Choose Output Folder…")
        self.output_btn.clicked.connect(self.choose_output)
        fg.addWidget(self.output_btn, 1, 0, 1, 2)
        self.output_label = QLabel("Output: same folder as source")
        self.output_label.setWordWrap(True)
        fg.addWidget(self.output_label, 2, 0, 1, 2)
        self.auto_subfolder = QCheckBox("Create a 'converted' subfolder automatically")
        self.auto_subfolder.setChecked(True)
        fg.addWidget(self.auto_subfolder, 3, 0, 1, 2)
        rl.addWidget(format_box)

        tips = QGroupBox("Quick memory map")
        tl = QVBoxLayout(tips)
        tl.addWidget(QLabel(
            "Markdown → PDF: built in\n"
            "PDF → TXT: pypdf\n"
            "Images → PDF: Pillow\n"
            "DOCX/ODT/RTF/EPUB: Pandoc\n"
            "HTML → PDF: ReportLab"
        ))
        rl.addWidget(tips)
        rl.addStretch()
        splitter.addWidget(right)
        splitter.setSizes([620, 360])
        root.addWidget(splitter, 1)

        progress_row = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.convert_btn = QPushButton("▶  Convert Files")
        self.convert_btn.setObjectName("ConvertButton")
        self.convert_btn.clicked.connect(self.start_conversion)
        progress_row.addWidget(self.progress, 1)
        progress_row.addWidget(self.convert_btn)
        root.addLayout(progress_row)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(1000)
        root.addWidget(self.log, 0)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

        menu = self.menuBar().addMenu("Tools")
        refresh = QAction("Refresh dependency status", self)
        refresh.triggered.connect(self.refresh_status)
        menu.addAction(refresh)

        self.setStyleSheet("""
        QWidget { font-family: "DejaVu Sans", Arial; font-size: 10pt; }
        QMainWindow { background: #f4f6f8; }
        QGroupBox { font-weight: bold; border: 1px solid #c7d0d9; border-radius: 8px;
                    margin-top: 10px; padding: 10px; background: white; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        #Header { background: #183b56; border-radius: 10px; padding: 10px; }
        #Title { color: white; font-size: 18pt; font-weight: bold; }
        #Subtitle { color: #d9e8f2; }
        QPushButton { padding: 7px 12px; border-radius: 6px; }
        #ConvertButton { font-weight: bold; padding: 9px 18px; }
        QListWidget, QPlainTextEdit { background: white; border: 1px solid #c7d0d9;
                                      border-radius: 6px; }
        """)

    def refresh_status(self):
        bits = []
        bits.append("Pandoc: " + ("✓" if pandoc_path() else "✗"))
        mods = import_optional()
        bits.append("Markdown: " + ("✓" if mods["markdown"] else "✗"))
        bits.append("ReportLab: " + ("✓" if mods["reportlab"] else "✗"))
        bits.append("pypdf: " + ("✓" if mods["pypdf"] else "✗"))
        bits.append("Pillow: " + ("✓" if mods["PIL"] else "✗"))
        bits.append("PDF engine: ReportLab")
        self.statusBar().showMessage("   |   ".join(bits))

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select files", "", "All files (*.*)"
        )
        self.add_to_list(files)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select folder")
        if not folder:
            return
        paths = []
        for p in Path(folder).rglob("*"):
            if p.is_file():
                paths.append(str(p))
        self.add_to_list(paths)

    def add_to_list(self, paths):
        existing = set(self.files)
        for p in paths:
            if p not in existing:
                self.files.append(p)
                self.list.addItem(p)
                existing.add(p)
        self.update_count()

    def clear_files(self):
        self.files.clear()
        self.list.clear()
        self.update_count()
        self.log.clear()
        self.progress.setValue(0)

    def update_count(self):
        self.file_count.setText(f"{len(self.files)} file(s)")

    def choose_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose output folder")
        if folder:
            self.output_label.setText(f"Output: {folder}")
            self.output_label.setProperty("path", folder)

    def output_dir(self, source):
        chosen = self.output_label.property("path")
        if chosen:
            out = Path(chosen)
        else:
            out = Path(source).parent
        if self.auto_subfolder.isChecked():
            out = out / "converted"
        out.mkdir(parents=True, exist_ok=True)
        return out

    def start_conversion(self):
        if not self.files:
            QMessageBox.information(self, "No files", "Add one or more files first.")
            return

        ext = self.format_combo.currentData()
        # For a batch with a chosen folder, use the same destination.
        # Otherwise preserve each source's directory.
        chosen = self.output_label.property("path")
        if chosen:
            out_dir = Path(chosen)
            if self.auto_subfolder.isChecked():
                out_dir = out_dir / "converted"
        else:
            # Worker supports one output directory; use the first source folder
            # only when no destination was selected.
            out_dir = self.output_dir(self.files[0])

        self.convert_btn.setEnabled(False)
        self.add_btn.setEnabled(False)
        self.add_folder_btn.setEnabled(False)
        self.progress.setValue(0)
        self.log.appendPlainText(
            f"\n--- Converting {len(self.files)} file(s) → {ext} ---"
        )

        self.worker = Worker(self.files, str(out_dir), ext)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.message.connect(self.log.appendPlainText)
        self.worker.finished_ok.connect(self.conversion_finished)
        self.worker.start()

    def conversion_finished(self, ok, failed):
        self.convert_btn.setEnabled(True)
        self.add_btn.setEnabled(True)
        self.add_folder_btn.setEnabled(True)
        self.statusBar().showMessage(f"Finished: {ok} converted, {failed} failed.")
        QMessageBox.information(
            self, "Conversion complete",
            f"Converted: {ok}\nFailed: {failed}"
        )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

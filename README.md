# JASS Universal File Converter

A lightweight **PySide6 desktop application** for converting documents, Markdown, text, HTML, PDFs, and images between commonly used formats.

The application is designed to be **simple, local-first, offline-friendly, and dependency-conscious**.

## ✨ Features

- Markdown conversion
- Plain-text conversion
- HTML conversion
- PDF text extraction
- Image-to-PDF conversion
- Pandoc-based document conversion
- Batch conversion
- Add individual files or folders
- Custom output folder
- Automatic `converted` output folder
- Progress indicator
- Conversion log
- Windows and Linux friendly
- **No WeasyPrint dependency**

---

## 🔄 Supported Conversions

### Markdown

| Source | Target |
|---|---|
| `.md`, `.markdown` | `.html` |
| `.md`, `.markdown` | `.txt` |
| `.md`, `.markdown` | `.pdf` |

### Text

| Source | Target |
|---|---|
| `.txt` | `.md` |
| `.txt` | `.html` |
| `.txt` | `.pdf` |

### HTML

| Source | Target |
|---|---|
| `.html`, `.htm` | `.pdf` |
| `.html`, `.htm` | `.txt` |

### PDF

| Source | Target |
|---|---|
| `.pdf` | `.txt` |

### Images → PDF

Supported image formats include:

- PNG
- JPG / JPEG
- WebP
- BMP
- TIFF / TIF

### Pandoc Formats

When Pandoc is installed, the application can provide broader conversion support for formats such as:

- DOCX
- ODT
- RTF
- EPUB
- Markdown
- HTML
- TXT

Actual Pandoc conversions depend on the installed Pandoc version and its supported readers/writers.

---

# 🧠 PDF Conversion Without WeasyPrint

This version deliberately **does not use WeasyPrint**.

Markdown and HTML PDF generation use **ReportLab**, avoiding the GTK/Pango native-library problems that can occur with WeasyPrint on Windows.

### PDF engine

**ReportLab**

Benefits:

- No GTK installation
- No Pango DLL requirement
- No WeasyPrint dependency
- Local/offline PDF generation
- Suitable for everyday document conversion

---

# 🛠️ Requirements

## Python

Python **3.10 or newer** is recommended.

## Required packages

### Windows

```powershell
py -m pip install PySide6 markdown reportlab pypdf pillow
```

### Linux

```bash
python3 -m pip install PySide6 markdown reportlab pypdf pillow
```

---

# 📦 Optional: Pandoc

Pandoc enables additional document conversion capabilities.

### Windows

```powershell
winget install --id JohnMacFarlane.Pandoc
```

Verify:

```powershell
pandoc --version
```

### Debian / Ubuntu / MX Linux

```bash
sudo apt install pandoc
```

Verify:

```bash
pandoc --version
```

---

# 🚀 Running the Application

## Windows

```powershell
py .\JASS_Universal_File_Converter_v1.1_No_WeasyPrint.py
```

## Linux

```bash
python3 JASS_Universal_File_Converter_v1.1_No_WeasyPrint.py
```

---

# 🖥️ How to Use

### 1. Add files

Click **Add Files** to select one or more files.

Use **Add Folder** when you want to process files from a directory.

### 2. Select the target format

Choose the desired output format, for example:

```text
PDF
Markdown
HTML
TXT
DOCX
ODT
RTF
EPUB
```

### 3. Choose the output folder

Select a destination folder if required.

If no custom destination is selected, converted files are placed in a `converted` folder associated with the source location.

### 4. Start conversion

Click **Convert**.

The progress bar and log show the conversion status.

### 5. Review the log

The log reports successful conversions and failures, together with useful error information.

---

# 📄 Example: Markdown → PDF

Input:

```text
MyNotes.md
```

Select:

```text
Target Format → PDF
```

Output:

```text
MyNotes.pdf
```

The PDF is generated locally with **ReportLab**.

Example Markdown:

```markdown
# My Notes

This is my document.

- Item one
- Item two
- Item three
```

No WeasyPrint or GTK libraries are required.

---

# 🔧 Conversion Engines

| Conversion | Engine |
|---|---|
| Markdown → HTML | Python Markdown |
| Markdown → TXT | Built-in processing |
| Markdown → PDF | ReportLab |
| TXT → HTML | Built-in HTML generation |
| TXT → Markdown | Built-in processing |
| TXT → PDF | ReportLab |
| HTML → PDF | ReportLab |
| HTML → TXT | HTML parsing |
| PDF → TXT | pypdf |
| Image → PDF | Pillow |
| DOCX / ODT / RTF / EPUB etc. | Pandoc |

---

# 🔐 Privacy & Offline Use

JASS Universal File Converter is designed for **local file processing**.

Normal conversions do not require uploading files to a cloud service.

The application does not require:

- Cloud conversion services
- Remote document processing
- WeasyPrint
- Internet access during normal conversion

Pandoc also performs conversions locally once installed.

---

# ⚠️ Limitations

Conversion quality depends on the source and target formats.

For example:

- Complex PDF layouts may not convert perfectly to TXT.
- PDF-to-TXT extraction depends on the PDF's internal text structure.
- Complex HTML/CSS styling is not reproduced completely by the ReportLab PDF engine.
- Scanned/image-only PDFs require OCR and are not automatically converted into editable text.
- Pandoc conversions depend on Pandoc's supported formats and installed components.
- Image-to-PDF conversion does not perform OCR.

For highly complex documents, specialized conversion software may preserve the original layout better.

---

# 🧩 Troubleshooting

## Python / pip

If `pip` is not recognized directly on Windows, use:

```powershell
py -m pip --version
```

Then install packages with:

```powershell
py -m pip install PySide6 markdown reportlab pypdf pillow
```

## PySide6 missing

```powershell
py -m pip install PySide6
```

## ReportLab missing

```powershell
py -m pip install reportlab
```

## pypdf missing

```powershell
py -m pip install pypdf
```

## Pillow missing

```powershell
py -m pip install pillow
```

## Pandoc conversions fail

Check:

```powershell
pandoc --version
```

If Pandoc is not found, install it and restart the application.

---

# 🏗️ Project Structure

Typical layout:

```text
JASS Universal File Converter/
│
├── JASS_Universal_File_Converter_v1.1_No_WeasyPrint.py
├── README.md
└── converted/
```

The application is intentionally maintained as a single Python GUI application, making it easy to copy, run, and maintain.

---

# 📌 Version

## v1.1 — No WeasyPrint

Highlights:

- Removed WeasyPrint
- Removed GTK/Pango dependency
- Markdown → PDF uses ReportLab
- HTML → PDF uses ReportLab
- Improved Windows compatibility
- Pandoc support retained
- Local-first conversion workflow

---

# 📜 License

If no license file is included with the repository, all rights remain with the project author.

---

# 👤 JASS

**JASS Universal File Converter**

A practical local-first utility for working with documents, Markdown, PDFs, images, and other digital content.

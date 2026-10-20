import csv
import json
from pathlib import Path

# Optional light dependencies handled gracefully
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import docx
except ImportError:
    docx = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf", ".docx", ".doc", ".html", ".htm", ".json", ".csv"}

class FileExtractor:
    @staticmethod
    def extract_text(file_path: Path) -> str:
        """Extracts plain text content from various file formats."""
        ext = file_path.suffix.lower()

        if ext in [".md", ".txt"]:
            return FileExtractor._extract_plain(file_path)
        elif ext == ".pdf":
            return FileExtractor._extract_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return FileExtractor._extract_docx(file_path)
        elif ext in [".html", ".htm"]:
            return FileExtractor._extract_html(file_path)
        elif ext == ".json":
            return FileExtractor._extract_json(file_path)
        elif ext == ".csv":
            return FileExtractor._extract_csv(file_path)
        else:
            return ""

    @staticmethod
    def _extract_plain(path: Path) -> str:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()

    @staticmethod
    def _extract_pdf(path: Path) -> str:
        if not PdfReader:
            raise ImportError("pypdf is required to parse PDF files. Install it with: pip install pypdf")
        reader = PdfReader(str(path))
        text_chunks = [page.extract_text() for page in reader.pages if page.extract_text()]
        return "\n\n".join(text_chunks).strip()

    @staticmethod
    def _extract_docx(path: Path) -> str:
        if not docx:
            raise ImportError("python-docx is required to parse DOCX files. Install it with: pip install python-docx")
        doc = docx.Document(str(path))
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()]).strip()

    @staticmethod
    def _extract_html(path: Path) -> str:
        if not BeautifulSoup:
            raise ImportError("beautifulsoup4 is required to parse HTML files. Install it with: pip install beautifulsoup4")
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            return soup.get_text(separator="\n", strip=True)

    @staticmethod
    def _extract_json(path: Path) -> str:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
            return json.dumps(data, indent=2)

    @staticmethod
    def _extract_csv(path: Path) -> str:
        lines = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            for row in reader:
                lines.append(" | ".join(row))
        return "\n".join(lines).strip()
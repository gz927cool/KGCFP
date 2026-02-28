"""Text parser for reading and segmenting Markdown files."""
import re
from pathlib import Path
from typing import Iterator


class TextParser:
    """Parser for Chinese painting history texts."""

    def __init__(self, data_dir: str = "data/books"):
        self.data_dir = Path(data_dir)

    def list_markdown_files(self) -> list[Path]:
        """List all Markdown files in the data directory."""
        return sorted(self.data_dir.glob("**/*.md"))

    def read_file(self, file_path: Path) -> str:
        """Read a Markdown file and return its content."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def segment_by_headings(self, content: str) -> Iterator[tuple[str, str]]:
        """
        Segment content by markdown headings.

        Yields tuples of (heading_text, section_content).
        """
        lines = content.split("\n")
        current_heading = ""
        current_content = []

        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")

        for line in lines:
            match = heading_pattern.match(line)
            if match:
                # Yield previous section
                if current_heading and current_content:
                    yield current_heading, "\n".join(current_content).strip()

                current_heading = match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        # Yield last section
        if current_heading and current_content:
            yield current_heading, "\n".join(current_content).strip()

    def extract_biographies(self, content: str) -> Iterator[str]:
        """
        Extract potential biography sections from text.

        Looks for patterns like:
        - "XXX，字XX，号XX"
        - Sections about specific painters
        """
        # Simple heuristic: split by double newlines and look for name patterns
        paragraphs = content.split("\n\n")

        name_pattern = re.compile(r"^[^#\n]+?(?:，|字|号|朝|代|画家|书法家)")

        for para in paragraphs:
            if name_pattern.search(para) and len(para) > 50:
                yield para.strip()

    def get_file_info(self, file_path: Path) -> dict:
        """Extract metadata from file path."""
        filename = file_path.stem

        # Try to extract book info from filename
        # Pattern: number-title.md or just title.md
        match = re.match(r"(\d+)[-_](.+)", filename)
        if match:
            return {
                "order": match.group(1),
                "title": match.group(2),
                "filename": filename
            }

        return {
            "order": None,
            "title": filename,
            "filename": filename
        }

    def chunk_text(self, text: str, chunk_size: int = 2000, overlap: int = 200) -> Iterator[str]:
        """
        Split text into chunks for LLM processing.

        Args:
            text: Input text
            chunk_size: Maximum characters per chunk
            overlap: Overlap between chunks

        Yields:
            Text chunks
        """
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size

            # Try to break at paragraph boundary
            if end < text_length:
                # Find last newline before end
                last_newline = text.rfind("\n", start, end)
                if last_newline > start:
                    end = last_newline

            yield text[start:end]
            start = end - overlap

            if start < 0:
                start = 0

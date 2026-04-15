#!/usr/bin/env python3
from __future__ import annotations
"""
从英文 PDF 提取纯文本。
用法: python extract_pdf.py <input.pdf> [--max-chars N]

只处理文本型 PDF(有文本层的),不做 OCR。
遇到扫描件会明确报错而不是返回乱码。
"""

import sys
import argparse
from pathlib import Path


def extract_text(pdf_path: Path, max_chars: int | None = None) -> str:
    """提取 PDF 文本层。优先用 pypdf,它是最轻量的选择。"""
    try:
        from pypdf import PdfReader
    except ImportError:
        print("ERROR: pypdf not installed. Run: pip install pypdf --break-system-packages",
              file=sys.stderr)
        sys.exit(1)

    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    reader = PdfReader(str(pdf_path))
    pages_text = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages_text.append(text)

    full_text = "\n\n".join(pages_text).strip()

    # 检测扫描件:文本极少但页数很多,基本可以判定是图片型 PDF
    if len(full_text) < 100 and len(reader.pages) > 2:
        print(
            "ERROR: This PDF appears to be a scanned image with no text layer. "
            "Literpod v1 does not support OCR. Please use a text-based PDF.",
            file=sys.stderr
        )
        sys.exit(2)

    if max_chars and len(full_text) > max_chars:
        full_text = full_text[:max_chars] + "\n\n[... truncated for length ...]"

    return full_text


def main():
    parser = argparse.ArgumentParser(description="Extract text from an English PDF")
    parser.add_argument("pdf", type=Path, help="Path to the PDF file")
    parser.add_argument("--max-chars", type=int, default=30000,
                        help="Max chars to extract (default: 30000, ~5000 English words)")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output text file path (default: stdout)")
    args = parser.parse_args()

    text = extract_text(args.pdf, args.max_chars)

    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(f"Extracted {len(text)} chars to {args.output}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()

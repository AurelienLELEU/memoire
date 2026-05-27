"""
Chunk a Markdown file using the same chunking method as the current PDF parser.

Usage:
    python markdown_chunker.py input.md
    python markdown_chunker.py input.md --output chunks.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

# Default configuration values
DEFAULT_MAX_CHUNK_LENGTH = 1000
DEFAULT_MIN_CHUNK_LENGTH = 100
DEFAULT_SEARCH_WINDOW = 200


def split_long_chunk(
    chunk: str, max_length: int = DEFAULT_MAX_CHUNK_LENGTH
) -> List[str]:
    """
    Splits a chunk into smaller chunks, ensuring it splits at the end of a sentence.

    Args:
        chunk (str): The text to split.
        max_length (int): The maximum allowed length for each chunk.

    Returns:
        List[str]: A list of split chunks.
    """
    if len(chunk) <= max_length:
        return [chunk]

    chunks = []
    start = 0
    search_window = min(
        DEFAULT_SEARCH_WINDOW, max_length // 5
    )  # Adaptive search window

    while start < len(chunk):
        end = start + max_length
        if end >= len(chunk):
            chunks.append(chunk[start:])
            break

        # Look for sentence ending in the last part of the chunk
        endstart = max(start, end - search_window)
        split_point = chunk.find(". ", endstart, end)

        if split_point == -1:
            # If no sentence ending found, try other delimiters
            for delimiter in ["! ", "? ", ": ", "; "]:
                split_point = chunk.find(delimiter, endstart, end)
                if split_point != -1:
                    break

        if split_point == -1:
            split_point = end
        else:
            split_point += 1

        chunks.append(chunk[start:split_point].strip())
        start = split_point

    return [chunk for chunk in chunks if chunk.strip()]  # Filter empty chunks


def merge_short_chunks(
    chunks: List[dict], min_length: int = DEFAULT_MIN_CHUNK_LENGTH
) -> List[dict]:
    """
    Merges chunks shorter than `min_length` with the next chunk,
    while preserving the page number of the first chunk.

    Args:
        chunks (List[dict]): A list of chunks to merge, each chunk being a dictionary
                             containing "text" and "page_number".
        min_length (int): The minimum allowed length for a chunk.

    Returns:
        List[dict]: A list of merged chunks with their page numbers.
    """
    if not chunks:
        return []

    merged_chunks = []
    buffer = {"text": "", "page_number": None}

    for chunk in chunks:
        text = chunk["text"]
        page_number = chunk["page_number"]

        if len(text) < min_length:
            if not buffer["text"]:
                buffer["page_number"] = page_number
            buffer["text"] += " " + text if buffer["text"] else text
        else:
            if buffer["text"]:
                # Merge buffer with current chunk
                merged_text = buffer["text"] + " " + text
                merged_chunks.append(
                    {"text": merged_text.strip(), "page_number": buffer["page_number"]}
                )
                buffer = {"text": "", "page_number": None}
            else:
                merged_chunks.append(chunk)

    # Handle remaining buffer
    if buffer["text"].strip():
        merged_chunks.append(
            {"text": buffer["text"].strip(), "page_number": buffer["page_number"]}
        )

    return merged_chunks


def markdown_to_conversion_result(markdown_text: str) -> List[dict]:
    """
    Build a conversion_result-like structure so the downstream chunking pipeline
    stays identical to PDFParser.process_pdf.
    """
    return [{"text": markdown_text, "page_number": 1}]


def chunk_markdown_text(
    markdown_text: str,
    max_chunk_length: int = DEFAULT_MAX_CHUNK_LENGTH,
    min_length: int = DEFAULT_MIN_CHUNK_LENGTH,
) -> List[dict]:
    """Apply the exact same split/merge processing as PDFParser.process_pdf."""
    conversion_result = markdown_to_conversion_result(markdown_text)

    processed_chunks = []
    for item in conversion_result:
        chunk_text = item["text"]
        page_number = item["page_number"]

        # Skip very small chunks early
        if len(chunk_text.strip()) < 3:
            continue

        split_chunks = split_long_chunk(chunk_text, max_length=max_chunk_length)

        # Add page number to each split chunk
        chunk_dicts = [
            {"text": sub_chunk, "page_number": page_number}
            for sub_chunk in split_chunks
        ]

        processed_chunks.extend(chunk_dicts)

    # Merge short chunks
    final_chunks = merge_short_chunks(processed_chunks, min_length=min_length)

    return final_chunks


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Chunk a Markdown file with the same algorithm used in bytp_scribbert PDF parsing."
        )
    )
    parser.add_argument("input", type=Path, help="Path to the input markdown file")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSON file path. If omitted, prints JSON to stdout.",
    )
    parser.add_argument(
        "--max-chunk-length",
        type=int,
        default=DEFAULT_MAX_CHUNK_LENGTH,
        help=f"Maximum chunk length before split (default: {DEFAULT_MAX_CHUNK_LENGTH})",
    )
    parser.add_argument(
        "--min-chunk-length",
        type=int,
        default=DEFAULT_MIN_CHUNK_LENGTH,
        help=f"Minimum chunk length after merge (default: {DEFAULT_MIN_CHUNK_LENGTH})",
    )

    args = parser.parse_args()

    if not args.input.exists() or not args.input.is_file():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    markdown_text = args.input.read_text(encoding="utf-8")
    chunks = chunk_markdown_text(
        markdown_text,
        max_chunk_length=args.max_chunk_length,
        min_length=args.min_chunk_length,
    )

    output = json.dumps(chunks, ensure_ascii=False, indent=2)
    if args.output is None:
        print(output)
    else:
        args.output.write_text(output, encoding="utf-8")
        print(f"Wrote {len(chunks)} chunks to {args.output}")


if __name__ == "__main__":
    main()

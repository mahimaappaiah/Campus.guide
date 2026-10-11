"""
tests/test_core.py - Unit tests for chunking logic, document loader filters, and refusal mechanics.
"""

import os
import pytest
from pathlib import Path
from common import (
    chunk_text_by_characters,
    CHUNK_SIZE_CHARS,
    CHUNK_OVERLAP_CHARS,
    REFUSAL_RESPONSE,
    SYSTEM_PROMPT
)
from ingest import load_and_index_documents
from ask import answer_query, retrieve_relevant_chunks


def test_chunking_character_limits():
    """Verify that chunk_text_by_characters produces chunks within requested character limits."""
    text = "A" * 2500
    chunk_size = 500
    overlap = 50
    chunks = chunk_text_by_characters(text, chunk_size=chunk_size, overlap=overlap)
    
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= chunk_size


def test_chunking_empty_text():
    """Verify handling of empty or whitespace-only text."""
    assert chunk_text_by_characters("") == []
    assert chunk_text_by_characters("   \n\n  ") == []


def test_ingest_skips_sources_and_readme(tmp_path):
    """Verify that document loader strictly excludes SOURCES.md and README.md."""
    # Create test dummy docs directory
    test_docs = tmp_path / "docs"
    test_docs.mkdir()
    
    (test_docs / "SOURCES.md").write_text("# Sources Index\nURL info", encoding="utf-8")
    (test_docs / "README.md").write_text("# Project Readme", encoding="utf-8")
    (test_docs / "readme_notes.txt").write_text("Notes", encoding="utf-8")
    (test_docs / "valid_policy.md").write_text("# Policy Document\nReal policy text here.", encoding="utf-8")
    
    test_chroma = str(tmp_path / "test_chroma")
    stats = load_and_index_documents(
        docs_dir=test_docs,
        collection_name="test_filter_collection",
        persist_dir=test_chroma
    )
    
    assert "SOURCES.md" not in stats["per_file_chunks"]
    assert "README.md" not in stats["per_file_chunks"]
    assert "readme_notes.txt" not in stats["per_file_chunks"]
    assert "valid_policy.md" in stats["per_file_chunks"]
    assert stats["files_indexed"] == 1


def test_out_of_scope_refusal():
    """Verify that ask.py refuses out-of-scope query with the exact refusal phrase."""
    res = answer_query("What is the capital of France?")
    assert res["answer"] == REFUSAL_RESPONSE


def test_system_prompt_structure():
    """Verify system prompt includes refusal instructions and placeholder formatting."""
    formatted = SYSTEM_PROMPT.format(
        refusal=REFUSAL_RESPONSE,
        context="Sample context",
        question="Sample question"
    )
    assert REFUSAL_RESPONSE in formatted
    assert "Sample context" in formatted
    assert "Sample question" in formatted

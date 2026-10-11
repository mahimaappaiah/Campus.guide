"""
common.py - Shared configuration, constants, and utilities for the Mount Carmel College RAG pipeline.

CHUNK SIZE UNITS:
All chunk sizes and overlaps in this system are strictly defined in CHARACTERS (not words or tokens).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables if .env exists
load_dotenv()

# ==============================================================================
# BASE CONFIGURATION PATHS & CONSTANTS
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
CHROMA_DIR = str(BASE_DIR / "chroma_db")
COLLECTION_NAME = "mcc_handbook_knowledge"

# v2 Tuned Chunking Parameters (Units: CHARACTERS)
CHUNK_SIZE_CHARS: int = 500        # Tuned chunk size in characters (from 1000 in baseline)
CHUNK_OVERLAP_CHARS: int = 80      # Tuned overlap in characters (from 150 in baseline)
TOP_K_RETRIEVAL: int = 4           # Default number of chunks to retrieve for context

# Standard Grounding Refusal Response
REFUSAL_RESPONSE: str = "I don't know based on the provided documents."

# System Prompt Template for Strict Grounding
SYSTEM_PROMPT = """You are an official Mount Carmel College document assistant.
Answer the user's question strictly and exclusively based on the provided context passages below.
Follow these rules strictly:
1. Ground your answer completely in the facts from the context. Do not invent, assume, or bring in outside information.
2. If the context does not contain enough information to answer the question, output EXACTLY:
"{refusal}"
3. Cite the source document file name for every fact mentioned, in the format [Source: <filename>].
4. If the question is outside the scope of Mount Carmel College handbook documents, output the exact refusal phrase.

Context:
{context}

Question: {question}

Answer:"""


def chunk_text_by_characters(text: str, chunk_size: int = CHUNK_SIZE_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> list[str]:
    """
    Splits text into chunks where chunk size and overlap are measured in CHARACTERS.
    Attempts to split along paragraph or sentence boundaries when feasible, otherwise falls back to character slicing.
    
    Args:
        text: The raw document text to split.
        chunk_size: Maximum character count per chunk.
        overlap: Character overlap between consecutive chunks.
        
    Returns:
        List of text chunks, each adhering to the character length limits.
    """
    if not text or not text.strip():
        return []
        
    text = text.strip()
    if len(text) <= chunk_size:
        return [text]
        
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        if end >= text_len:
            chunks.append(text[start:].strip())
            break
            
        # Try to break at a natural newline or period within the overlap window
        split_idx = text.rfind("\n\n", start, end)
        if split_idx == -1 or split_idx <= start + (chunk_size // 2):
            split_idx = text.rfind("\n", start, end)
        if split_idx == -1 or split_idx <= start + (chunk_size // 2):
            split_idx = text.rfind(". ", start, end)
            if split_idx != -1:
                split_idx += 1
                
        if split_idx == -1 or split_idx <= start:
            split_idx = end
            
        chunk_content = text[start:split_idx].strip()
        if chunk_content:
            chunks.append(chunk_content)
            
        start = max(start + 1, split_idx - overlap)
        
    return chunks


def get_chroma_collection(collection_name: str = COLLECTION_NAME, persist_directory: str = CHROMA_DIR):
    """
    Initializes and returns a persistent ChromaDB collection using local ONNX embeddings.
    """
    import chromadb
    from chromadb.utils import embedding_functions

    emb_fn = embedding_functions.DefaultEmbeddingFunction()
    client = chromadb.PersistentClient(path=persist_directory)
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=emb_fn,
        metadata={"hnsw:space": "cosine"}
    )
    return collection

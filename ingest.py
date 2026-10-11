"""
ingest.py - Ingests and indexes documents from docs/ into the Chroma vector database.

Explicitly ignores SOURCES.md and README files so only true policy content is embedded.
"""

import sys
from pathlib import Path
from common import (
    DOCS_DIR,
    CHROMA_DIR,
    COLLECTION_NAME,
    CHUNK_SIZE_CHARS,
    CHUNK_OVERLAP_CHARS,
    chunk_text_by_characters,
    get_chroma_collection
)


def load_and_index_documents(
    docs_dir: Path = DOCS_DIR,
    collection_name: str = COLLECTION_NAME,
    persist_dir: str = CHROMA_DIR,
    chunk_size: int = CHUNK_SIZE_CHARS,
    chunk_overlap: int = CHUNK_OVERLAP_CHARS
) -> dict:
    """
    Scans docs_dir, chunks valid documents, and stores them in ChromaDB.
    Returns summary statistics of the ingestion process.
    """
    if not docs_dir.exists():
        raise FileNotFoundError(f"Documents directory not found: {docs_dir}")

    # Initialize Chroma collection
    collection = get_chroma_collection(collection_name=collection_name, persist_directory=persist_dir)
    
    # Clear existing collection data to ensure fresh indexing
    existing_count = collection.count()
    if existing_count > 0:
        all_ids = collection.get()["ids"]
        if all_ids:
            collection.delete(ids=all_ids)

    doc_files = sorted(list(docs_dir.glob("*.md")) + list(docs_dir.glob("*.txt")))
    
    documents = []
    metadatas = []
    ids = []
    stats = {}

    for doc_file in doc_files:
        filename = doc_file.name
        
        # Explicit Rule Check: Skip SOURCES.md and any README / metadata files
        if filename.lower() in ("sources.md", "readme.md") or filename.lower().startswith("readme"):
            continue
            
        with open(doc_file, "r", encoding="utf-8") as f:
            raw_text = f.read()

        file_chunks = chunk_text_by_characters(raw_text, chunk_size=chunk_size, overlap=chunk_overlap)
        stats[filename] = len(file_chunks)

        for idx, chunk in enumerate(file_chunks):
            chunk_id = f"{filename}_chunk_{idx:03d}"
            documents.append(chunk)
            metadatas.append({
                "source": filename,
                "chunk_index": idx,
                "char_length": len(chunk)
            })
            ids.append(chunk_id)

    # Batch add to ChromaDB
    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    total_chunks = len(documents)
    return {
        "files_indexed": len(stats),
        "total_chunks": total_chunks,
        "per_file_chunks": stats
    }


def main():
    print("=" * 70)
    print("Mount Carmel College RAG Knowledge Base Ingestion")
    print(f"Docs Directory: {DOCS_DIR}")
    print(f"Chunk Size:     {CHUNK_SIZE_CHARS} characters")
    print(f"Chunk Overlap:  {CHUNK_OVERLAP_CHARS} characters")
    print("=" * 70)

    results = load_and_index_documents()

    print("\n--- INGESTION SUMMARY ---")
    print(f"{'Filename':<40} | {'Chunk Count':<12}")
    print("-" * 55)
    for filename, count in results["per_file_chunks"].items():
        print(f"{filename:<40} | {count:<12}")
    print("-" * 55)
    print(f"{'TOTAL CHUNKS INDEXED':<40} | {results['total_chunks']:<12}")
    print("=" * 70)


if __name__ == "__main__":
    main()

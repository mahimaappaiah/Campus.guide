"""
ask.py - Query retrieval and grounded answer synthesis for the Mount Carmel College RAG system.

Retrieves the top-k most similar chunks from ChromaDB, then asks an OpenAI-compatible LLM
to answer strictly from those chunks and cite the source filename.

Raises EnvironmentError if OPENAI_API_KEY is not set in the environment / .env file.
There is NO offline fallback; every answer comes from the LLM.
"""

import os
import sys
import time
import argparse
import openai
from dotenv import load_dotenv
from common import TOP_K_RETRIEVAL, REFUSAL_RESPONSE, SYSTEM_PROMPT, get_chroma_collection

load_dotenv()


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def retrieve_relevant_chunks(query: str, top_k: int = TOP_K_RETRIEVAL,
                              collection_name: str = None) -> list[dict]:
    """Return the top_k most similar chunks from ChromaDB."""
    collection = (get_chroma_collection() if collection_name is None
                  else get_chroma_collection(collection_name=collection_name))

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []
    if results and results.get("documents") and results["documents"]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0] if results.get("distances") else [0.0] * len(results["documents"][0]),
        ):
            retrieved.append({
                "content": doc,
                "source": meta.get("source", "unknown"),
                "chunk_index": meta.get("chunk_index", 0),
                "distance": dist,
            })
    return retrieved


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------

def _get_llm_client():
    """Return a configured openai.OpenAI client, or raise EnvironmentError."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "your_openai_api_key_here":
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key. "
            "There is no offline fallback."
        )
    base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return openai.OpenAI(**kwargs)


def _call_llm(context_text: str, question: str) -> str:
    """Build the grounded prompt and call the LLM. Returns the answer string."""
    client = _get_llm_client()
    model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()

    prompt = SYSTEM_PROMPT.format(
        refusal=REFUSAL_RESPONSE,
        context=context_text,
        question=question,
    )
    for attempt in range(6):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a factual document QA assistant."},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.0,
            )
            return response.choices[0].message.content.strip()
        except openai.RateLimitError as e:
            if attempt < 5:
                wait_sec = 35
                print(f"[RateLimit] 429 hit. Waiting {wait_sec}s before retry (attempt {attempt+1}/5)...", flush=True)
                time.sleep(wait_sec)
            else:
                raise


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def answer_query(query: str, top_k: int = TOP_K_RETRIEVAL) -> dict:
    """
    Retrieve context chunks, call the LLM, and return a structured result dict.

    Keys: question, answer, sources, retrieved_chunks
    Raises EnvironmentError if OPENAI_API_KEY is missing.
    """
    chunks = retrieve_relevant_chunks(query, top_k=top_k)

    if not chunks:
        # Nothing in the DB — call LLM anyway with empty context so it refuses cleanly.
        context_text = "(no documents available)"
    else:
        context_text = "\n\n".join(
            f"--- [Document: {c['source']}] ---\n{c['content']}" for c in chunks
        )

    answer = _call_llm(context_text, query)
    sources = list(dict.fromkeys(c["source"] for c in chunks))

    return {
        "question": query,
        "answer": answer,
        "sources": sources,
        "retrieved_chunks": chunks,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Query the Mount Carmel College RAG System")
    parser.add_argument("query",  type=str, help="The question to ask")
    parser.add_argument("--top_k", type=int, default=TOP_K_RETRIEVAL,
                        help="Number of chunks to retrieve")
    args = parser.parse_args()

    result = answer_query(args.query, top_k=args.top_k)
    print("=" * 70)
    print(f"QUESTION: {result['question']}")
    print("-" * 70)
    print(f"ANSWER:\n{result['answer']}")
    print("-" * 70)
    print("SOURCES:")
    for src in result["sources"]:
        print(f"  - {src}")
    print("=" * 70)


if __name__ == "__main__":
    main()

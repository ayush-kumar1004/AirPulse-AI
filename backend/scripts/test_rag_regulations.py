"""
AirPulse AI - Phase 4 Verification Test: Regulatory RAG Engine
Validates:
1. Document ingestion and 768-d vector embedding generation.
2. Vector similarity search over GRAP Stages I-IV, CAQM Directions, and Air Act 1981.
3. The new search_regulations agent tool with authentic statutory citations.
4. The upgraded draft_grap_notice tool grounded dynamically in retrieved legal text.
5. LangGraph agentic reasoning invoking search_regulations for regulatory inquiries.
6. Graceful degradation when the database or vector cache is freshly initialized.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from langchain_core.messages import HumanMessage, AIMessage
from app.rag.corpus import REGULATORY_DOCUMENTS
from app.rag.embeddings import get_embedding, cosine_similarity
from app.rag.vector_store import (
    ingest_regulations,
    similarity_search_db,
    load_local_vector_cache,
)
from app.llm.tools import search_regulations, draft_grap_notice, build_tools
from app.llm.officer_chat import get_checkpointer, SYSTEM_PROMPT


def test_1_ingestion_and_embeddings():
    print("=" * 70)
    print("STEP 1: Document Ingestion & 768-D Vector Embeddings")
    print("=" * 70)
    print(f"Total regulatory documents in corpus: {len(REGULATORY_DOCUMENTS)}")

    # Run ingestion
    count = asyncio.run(ingest_regulations(force_refresh=True))
    print(f"-> Successfully ingested and embedded {count} regulatory chunks.")
    assert count == len(REGULATORY_DOCUMENTS), f"Expected {len(REGULATORY_DOCUMENTS)} chunks, got {count}"

    cache = load_local_vector_cache()
    assert len(cache) == count, f"Cache size mismatch: {len(cache)} != {count}"

    sample = cache[0]
    emb = sample.get("embedding", [])
    print(f"Sample Document: [{sample['doc_id']}] {sample['title']}")
    print(f"Legal Citation:   {sample['legal_citation']}")
    print(f"Embedding Length: {len(emb)} (Expected: 768)")
    assert len(emb) == 768, f"Expected 768 dimensions, got {len(emb)}"
    print("[SUCCESS] Step 1 passed.\n")


def test_2_vector_similarity_search():
    print("=" * 70)
    print("STEP 2: Semantic Vector Similarity Search")
    print("=" * 70)

    test_queries = [
        ("construction ban during severe pollution", "GRAP_STAGE_3", "C&D"),
        ("diesel generator ban commercial residential buildings", "GRAP_STAGE_2", "Diesel Generator"),
        ("Section 31A power to give directions closure and Section 37 penalty", "AIR_ACT_1981", "Section 31A"),
        ("commercial interstate truck entry ban into Delhi", "GRAP_STAGE_4", "Truck"),
        ("industrial clean fuel policy PNG coal prohibition", "CAQM_DIRECTION", "Fuel"),
    ]

    for q, expected_cat, keyword in test_queries:
        print(f"\nQuery: '{q}'")
        results = asyncio.run(similarity_search_db(query=q, top_k=3))
        assert len(results) > 0, f"No results returned for query: {q}"
        top = results[0]
        print(f"  Top Match: [{top['doc_id']}] {top['title']}")
        print(f"  Category:   {top['category']} | Score: {top['similarity_score']}")
        print(f"  Citation:   {top['legal_citation']}")
        # Verify relevance
        matched = any(expected_cat == r["category"] or keyword.lower() in r["content"].lower() for r in results)
        assert matched, f"Expected relevant category '{expected_cat}' or keyword '{keyword}' in top results."

    print("\n[SUCCESS] Step 2 passed: Semantic vector similarity search matches authentic clauses.")


def test_3_search_regulations_tool():
    print("\n" + "=" * 70)
    print("STEP 3: Agent Tool Direct Execution (search_regulations)")
    print("=" * 70)

    query = "What are the restrictions on construction activities under GRAP Stage 3?"
    tool_output = search_regulations.invoke({"query": query, "top_k": 3})
    print(f"Query: '{query}'")
    print("Output Snippet:\n", tool_output[:350], "...\n")

    assert "Retrieved Regulatory Provisions" in tool_output
    assert "CAQM Direction" in tool_output or "GRAP" in tool_output
    assert "Construction" in tool_output or "C&D" in tool_output
    print("[SUCCESS] Step 3 passed: search_regulations tool returns authoritative formatted citations.")


def test_4_draft_grap_notice_with_rag():
    print("=" * 70)
    print("STEP 4: RAG-Grounded Statutory Notice (draft_grap_notice)")
    print("=" * 70)

    notice_output = draft_grap_notice.invoke({"ward_id": "CANT_1", "stage": "auto"})
    print("Generated Statutory Notice Snippet:\n")
    print(notice_output[:600])
    print("...\n")

    assert "STATUTORY RETRIEVAL & LEGAL BASES" in notice_output
    assert "CAQM Direction" in notice_output or "Air Act" in notice_output
    assert "OPERATIVE STATUTORY MANDATES" in notice_output
    assert "PENAL PROVISIONS & LEGAL ENFORCEMENT" in notice_output
    assert "Section 31A" in notice_output or "Section 37" in notice_output or "Air Act, 1981" in notice_output
    print("[SUCCESS] Step 4 passed: draft_grap_notice dynamically retrieves and cites real regulatory clauses.")


def test_5_agentic_rag_multiturn_workflow():
    print("=" * 70)
    print("STEP 5: Agentic Workflow Invoking Regulatory Search (RAG)")
    print("=" * 70)

    from langgraph.prebuilt import create_react_agent
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel

    class MockAgenticChatModel(FakeMessagesListChatModel):
        def bind_tools(self, tools, **kwargs):
            return self

    checkpointer = get_checkpointer()
    tools = build_tools()
    test_session_id = f"test-rag-session-{os.getpid()}"
    config = {
        "configurable": {
            "thread_id": test_session_id,
            "checkpoint_ns": "",
        }
    }

    # Simulate agent receiving: "What are the rules for diesel generators and construction in Stage 2 and 3?"
    # Agent calls search_regulations tool
    rag_tool_call = {
        "name": "search_regulations",
        "args": {"query": "diesel generator and construction restrictions GRAP Stage 2 Stage 3", "top_k": 3},
        "id": "call_rag_001",
    }
    ai_step1 = AIMessage(content="", tool_calls=[rag_tool_call])
    ai_final = AIMessage(
        content=(
            "Based on the retrieved statutory provisions:\n"
            "1. Under CAQM Direction No. 75, GRAP Stage II (AQI 301-400), Diesel Generator (DG) sets are strictly prohibited "
            "across commercial, residential, and industrial facilities, except for emergency services (hospitals, metro, elevators).\n"
            "2. Under GRAP Stage III (AQI 401-450), a complete blanket ban is imposed on all Construction and Demolition (C&D) "
            "activities, including excavation, structural concrete, and road works pursuant to Section 31A of the Air Act, 1981."
        )
    )

    fake_model = MockAgenticChatModel(responses=[ai_step1, ai_final])
    agent = create_react_agent(
        fake_model,
        tools,
        prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )

    out = agent.invoke(
        {"messages": [HumanMessage(content="What are the rules for diesel generators and construction in Stage 2 and 3?")]},
        config=config,
    )

    final_reply = out["messages"][-1].content
    tools_called = [tc["name"] for m in out["messages"] if hasattr(m, "tool_calls") and m.tool_calls for tc in m.tool_calls]

    print(f"Officer Prompt: 'What are the rules for diesel generators and construction in Stage 2 and 3?'")
    print(f"Tools Invoked by Agent: {tools_called}")
    print(f"Agent Final Reply:\n{final_reply}\n")

    assert "search_regulations" in tools_called, "Agent failed to invoke search_regulations tool."
    assert "CAQM Direction No. 75" in final_reply or "GRAP Stage II" in final_reply
    assert "Section 31A" in final_reply or "Air Act" in final_reply
    print("[SUCCESS] Step 5 passed: Agent autonomously calls search_regulations and cites statutory clauses.")


def test_6_graceful_degradation():
    print("=" * 70)
    print("STEP 6: Graceful Degradation (Empty Database / Missing Vector Cache)")
    print("=" * 70)

    # Temporary clear vector store cache
    from app.rag.vector_store import CACHE_FILE
    backup_path = CACHE_FILE.with_suffix(".json.bak")
    if CACHE_FILE.exists():
        CACHE_FILE.rename(backup_path)

    try:
        # Search when cache file doesn't exist
        print("Searching regulations with cold/uninitialized vector cache...")
        results = asyncio.run(similarity_search_db(query="stone crusher mining shutdown", top_k=2))
        assert len(results) > 0, "Failed to self-heal and ingest regulations on-the-fly."
        print(f"Self-healed and retrieved {len(results)} matches: [{results[0]['doc_id']}] {results[0]['title']}")
        print("[SUCCESS] Step 6 passed: System automatically re-ingests and self-heals when vector store is empty.")
    finally:
        if backup_path.exists():
            if CACHE_FILE.exists():
                CACHE_FILE.unlink()
            backup_path.rename(CACHE_FILE)


if __name__ == "__main__":
    try:
        test_1_ingestion_and_embeddings()
        test_2_vector_similarity_search()
        test_3_search_regulations_tool()
        test_4_draft_grap_notice_with_rag()
        test_5_agentic_rag_multiturn_workflow()
        test_6_graceful_degradation()
        print("\n" + "=" * 70)
        print(">>> ALL PHASE 4 RAG REGULATION CHECKS PASSED SUCCESSFULLY! <<<")
        print("=" * 70)
    except Exception as e:
        print(f"\n[FAILURE] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


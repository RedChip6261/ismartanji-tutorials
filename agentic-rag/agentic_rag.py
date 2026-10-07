from typing import List, TypedDict
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

class AgenticRAGState(TypedDict):
    question: str
    generation: str
    documents: List[str]
    iteration_count: int
    retrieval_status: str

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

MOCK_KNOWLEDGE_BASE = {
    "mcp": "Model Context Protocol (MCP) is an open standard created by Anthropic in late 2024 to connect AI models directly to tools and data sources.",
    "vector": "Vector databases store high-dimensional mathematical embeddings to perform approximate nearest neighbor similarity searches.",
    "langgraph": "LangGraph is a framework for building stateful, multi-actor applications with LLMs using cyclic computational graphs."
}

def retrieve_node(state: AgenticRAGState) -> dict:
    query = state["question"].lower()
    retrieved = []
    for key, doc in MOCK_KNOWLEDGE_BASE.items():
        if key in query or any(word in doc.lower() for word in query.split()):
            retrieved.append(doc)
    if not retrieved:
        retrieved.append("No directly matching documents found in the primary enterprise knowledge base.")
    return {"documents": retrieved, "iteration_count": state.get("iteration_count", 0) + 1}

def grade_documents_node(state: AgenticRAGState) -> dict:
    question = state["question"]
    documents = state["documents"]
    filtered_docs = []
    grader_prompt = "Assess whether the retrieved document is relevant. Respond with exactly YES or NO."
    for doc in documents:
        user_prompt = f"Question: {question}\nDocument: {doc}\nRelevant?"
        response = llm.invoke([SystemMessage(content=grader_prompt), HumanMessage(content=user_prompt)])
        if "YES" in response.content.upper():
            filtered_docs.append(doc)
    status = "relevant" if filtered_docs else "needs_rewrite"
    return {"documents": filtered_docs, "retrieval_status": status}

def rewrite_query_node(state: AgenticRAGState) -> dict:
    original_question = state["question"]
    rewrite_prompt = f"The question failed to retrieve relevant documents: '{original_question}'. Rewrite it to be clearer and optimized for vector search."
    response = llm.invoke([HumanMessage(content=rewrite_prompt)])
    return {"question": response.content.strip(), "retrieval_status": "rewritten"}

def generate_node(state: AgenticRAGState) -> dict:
    question = state["question"]
    context = "\n\n".join(state["documents"])
    synthesis_prompt = f"Answer based strictly on context.\n\nContext:\n{context}\n\nQuestion: {question}"
    response = llm.invoke([HumanMessage(content=synthesis_prompt)])
    return {"generation": response.content}

def route_after_grading(state: AgenticRAGState) -> str:
    if state["retrieval_status"] == "relevant" or state.get("iteration_count", 0) >= 2:
        return "generate"
    return "rewrite_query"

workflow = StateGraph(AgenticRAGState)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("grade_documents", grade_documents_node)
workflow.add_node("rewrite_query", rewrite_query_node)
workflow.add_node("generate", generate_node)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges("grade_documents", route_after_grading, {"generate": "generate", "rewrite_query": "rewrite_query"})
workflow.add_edge("rewrite_query", "retrieve")
workflow.add_edge("generate", END)

rag_agent = workflow.compile()

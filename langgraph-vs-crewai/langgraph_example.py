from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# 1. Define the Central State Schema
class WorkflowState(TypedDict):
    research_topic: str
    raw_data: str
    final_summary: str
    iteration_count: int

# 2. Define Node Functions
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

def researcher_node(state: WorkflowState) -> dict:
    prompt = f"Analyze the core architectural benefits of: {state['research_topic']}"
    response = llm.invoke([
        SystemMessage(content="You are a senior systems researcher."),
        HumanMessage(content=prompt)
    ])
    return {
        "raw_data": response.content,
        "iteration_count": state.get("iteration_count", 0) + 1
    }

def editor_node(state: WorkflowState) -> dict:
    prompt = f"Format and refine these research notes into three concise executive bullet points:\n{state['raw_data']}"
    response = llm.invoke([
        SystemMessage(content="You are a strict technical editor."),
        HumanMessage(content=prompt)
    ])
    return {"final_summary": response.content}

# 3. Construct and Compile the StateGraph
workflow = StateGraph(WorkflowState)
workflow.add_node("researcher", researcher_node)
workflow.add_node("editor", editor_node)

workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "editor")
workflow.add_edge("editor", END)

app = workflow.compile()

# 4. Execute the Graph
if __name__ == "__main__":
    initial_input = {"research_topic": "Model Context Protocol in Enterprise Stacks"}
    result = app.invoke(initial_input)
    print("--- LANGGRAPH FINAL RESULT ---")
    print(result["final_summary"])

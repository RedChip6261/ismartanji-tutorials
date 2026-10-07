import os
import asyncio
from mem0 import Memory

# 1. Configure the Persistent Memory Engine
config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "localhost",
            "port": 6333,
        }
    },
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gpt-4o-mini",
            "temperature": 0.1
        }
    }
}

memory_engine = Memory.from_config(config)

async def process_user_turn(user_id: str, session_id: str, incoming_message: str):
    # Step A: Retrieve relevant context snippets
    relevant_memories = memory_engine.search(
        query=incoming_message,
        user_id=user_id,
        limit=5
    )
    
    # Step B: Format memory context for the prompt
    context_str = "\n".join([f"- {m['memory']}" for m in relevant_memories])
    
    system_prompt = f"""You are an autonomous engineering assistant.

Known User Preferences & State:
{context_str}
"""
    print(f"Injected Context:\n{context_str}")
    
    # Step C: Dispatch background write to update state without blocking
    asyncio.create_task(persist_interaction(user_id, session_id, incoming_message))
    return system_prompt

async def persist_interaction(user_id: str, session_id: str, message: str):
    # Automatically extracts entities, updates conflict nodes, and writes to storage
    memory_engine.add(
        message,
        user_id=user_id,
        metadata={"session_id": session_id}
    )

# Execution Demo
if __name__ == "__main__":
    test_user = "developer_402"
    test_session = "sess_prod_09"
    
    # Store an initial fact
    memory_engine.add("I deploy our backend microservices using FastAPI and Docker on AWS ECS.", user_id=test_user)
    
    # Retrieve on a new turn
    asyncio.run(process_user_turn(test_user, test_session, "How should I structure my new deployment script?"))

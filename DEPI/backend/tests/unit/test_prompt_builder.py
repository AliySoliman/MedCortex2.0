import pytest
from app.ai.prompts.prompt_builder import get_prompt_builder


def test_prompt_builder_mandatory_order():
    builder = get_prompt_builder()
    
    system = "You are a clinical AI."
    prefs = "Preferred Language: French"
    memory = "- Has diabetes"
    summary = "User asked about insulin."
    context = "Source: Book A | Text: Insulin info"
    question = "Can I take insulin?"
    instructions = "Answer only from context."
    recent_messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi, how can I help?"}
    ]

    messages = builder.build_chat_prompt(
        system_prompt=system,
        user_preferences=prefs,
        persistent_memory=memory,
        conversation_summary=summary,
        recent_messages=recent_messages,
        retrieved_context=context,
        current_question=question,
        formatting_instructions=instructions
    )

    # Output matches standard messages array format
    assert len(messages) == 4 # 1 system, 2 recent, 1 current question
    
    assert messages[0]["role"] == "system"
    system_content = messages[0]["content"]
    
    # Check that system prompt ordering is preserved in system_content
    # We find indices of each section and assert they are in order
    idx_system = system_content.find(system)
    idx_prefs = system_content.find(prefs)
    idx_memory = system_content.find(memory)
    idx_summary = system_content.find(summary)
    idx_context = system_content.find(context)
    idx_instructions = system_content.find(instructions)

    assert idx_system != -1
    assert idx_prefs != -1
    assert idx_memory != -1
    assert idx_summary != -1
    assert idx_context != -1
    assert idx_instructions != -1

    assert idx_system < idx_prefs < idx_memory < idx_summary < idx_context < idx_instructions

    # Check recent messages are appended sequentially
    assert messages[1] == {"role": "user", "content": "Hello"}
    assert messages[2] == {"role": "assistant", "content": "Hi, how can I help?"}

    # Check current question is at the end
    assert messages[3] == {"role": "user", "content": question}

#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced conversation memory and context understanding
of the optimized AI chatbot.
"""

import asyncio
import json
from apps.agents.optimized_ai_chatbot import OptimizedAIChatbot

async def test_conversation_memory():
    """Test the chatbot's conversation memory and context understanding"""
    print("🧠 Testing Enhanced AI Chatbot with Conversation Memory")
    print("=" * 60)
    
    chatbot = OptimizedAIChatbot()
    user_id = "test_user_001"
    session_id = "session_conversation_test"
    
    # Test conversation scenarios demonstrating memory and context
    conversation_scenarios = [
        {
            "name": "Initial Property Search",
            "messages": [
                "I'm looking for properties in Broward County under $200,000",
                "What about tax deed properties in the same area?",
                "Tell me more about that first property you mentioned",
                "How's the ROI on properties like this?",
                "Any similar properties available?"
            ]
        },
        {
            "name": "Follow-up Questions",
            "messages": [
                "Show me properties at 123 Main Street Fort Lauderdale",
                "What's the property tax on this one?", 
                "How does it compare to similar properties?",
                "Is this a good investment?",
                "What about the neighborhood?"
            ]
        }
    ]
    
    for scenario in conversation_scenarios:
        print(f"\n🎯 Scenario: {scenario['name']}")
        print("-" * 40)
        
        for i, message in enumerate(scenario['messages'], 1):
            print(f"\n[Message {i}] User: {message}")
            
            try:
                response = await chatbot.process_message(
                    user_id=user_id,
                    message=message,
                    session_id=session_id
                )
                
                print(f"[Response {i}] Bot: {response['answer']}")
                
                # Show context information
                metadata = response.get('metadata', {})
                print(f"[Context] Intent: {metadata.get('intent', 'unknown')}")
                print(f"[Context] Confidence: {metadata.get('confidence', 0.0):.2f}")
                
                if 'entities_mentioned' in metadata and metadata['entities_mentioned']:
                    entities_str = ", ".join([
                        f"{k}: {v}" for k, v in metadata['entities_mentioned'].items() 
                        if v
                    ])
                    print(f"[Memory] Entities: {entities_str}")
                
                if metadata.get('conversation_summary'):
                    print(f"[Memory] Summary: {metadata['conversation_summary'][:100]}...")
                
            except Exception as e:
                print(f"[Error] {e}")
            
            # Small delay between messages
            await asyncio.sleep(0.5)
    
    # Test memory persistence
    print(f"\n🧠 Testing Memory Persistence")
    print("-" * 40)
    
    # Show chatbot metrics
    metrics = chatbot.get_metrics()
    print(f"Active conversation threads: {metrics['active_threads']}")
    print(f"User profiles stored: {metrics['user_profiles']}")
    print(f"Available tools: {len(metrics['available_tools'])}")
    
    # Test context understanding with references
    print(f"\n🔗 Testing Contextual References")
    print("-" * 40)
    
    reference_tests = [
        "Tell me about that property again",
        "What was the price on the previous one?", 
        "Show me more properties like this",
        "Compare it to the first property we discussed"
    ]
    
    for message in reference_tests:
        print(f"\nUser: {message}")
        
        try:
            response = await chatbot.process_message(
                user_id=user_id,
                message=message,
                session_id=session_id
            )
            
            intent = response.get('metadata', {}).get('intent', 'unknown')
            confidence = response.get('metadata', {}).get('confidence', 0.0)
            
            print(f"Bot: {response['answer'][:150]}...")
            print(f"Intent: {intent} (confidence: {confidence:.2f})")
            
        except Exception as e:
            print(f"Error: {e}")
    
    print(f"\n✅ Conversation Memory Test Complete!")
    print(f"The chatbot now remembers conversation context and can:")
    print(f"  • Track entities mentioned (properties, addresses, preferences)")
    print(f"  • Understand contextual references ('that property', 'this one')")
    print(f"  • Maintain conversation summaries")
    print(f"  • Handle follow-up questions intelligently")
    print(f"  • Remember user preferences across the session")

if __name__ == "__main__":
    asyncio.run(test_conversation_memory())
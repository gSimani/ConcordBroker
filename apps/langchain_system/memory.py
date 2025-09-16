"""
Memory Systems for LangChain Agents
Manages conversation history and context retention
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import pickle

from langchain.memory import (
    ConversationBufferMemory,
    ConversationBufferWindowMemory,
    ConversationSummaryMemory,
    ConversationSummaryBufferMemory,
    VectorStoreRetrieverMemory
)
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.memory.chat_memory import BaseChatMemory

logger = logging.getLogger(__name__)

class ConversationMemory:
    """
    Enhanced conversation memory system for ConcordBroker agents
    """
    
    def __init__(self, llm=None, embeddings=None):
        self.llm = llm
        self.embeddings = embeddings
        
        # Different memory types for different purposes
        self.memories = {}
        
        # Session storage
        self.sessions = {}
        
        # Persistence directory
        self.persistence_dir = Path("./memory_storage")
        self.persistence_dir.mkdir(exist_ok=True)
        
        # Initialize default memories
        self._initialize_default_memories()
    
    def _initialize_default_memories(self):
        """Initialize default memory systems"""
        
        # Short-term memory (last 10 exchanges)
        self.memories["short_term"] = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=10,
            return_messages=True
        )
        
        # Long-term buffer memory (all conversations)
        self.memories["long_term"] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Summary memory (if LLM is available)
        if self.llm:
            self.memories["summary"] = ConversationSummaryMemory(
                llm=self.llm,
                memory_key="chat_history",
                return_messages=True
            )
            
            # Summary buffer memory (hybrid approach)
            self.memories["summary_buffer"] = ConversationSummaryBufferMemory(
                llm=self.llm,
                memory_key="chat_history",
                max_token_limit=2000,
                return_messages=True
            )
    
    def create_session(self, session_id: str, memory_type: str = "short_term") -> BaseChatMemory:
        """
        Create a new conversation session
        
        Args:
            session_id: Unique session identifier
            memory_type: Type of memory to use
        
        Returns:
            Memory instance for the session
        """
        
        if memory_type == "short_term":
            memory = ConversationBufferWindowMemory(
                memory_key="chat_history",
                k=10,
                return_messages=True
            )
        elif memory_type == "long_term":
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
        elif memory_type == "summary" and self.llm:
            memory = ConversationSummaryMemory(
                llm=self.llm,
                memory_key="chat_history",
                return_messages=True
            )
        else:
            # Default to buffer memory
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
        
        self.sessions[session_id] = {
            "memory": memory,
            "created_at": datetime.now(),
            "last_active": datetime.now(),
            "memory_type": memory_type,
            "metadata": {}
        }
        
        logger.info(f"Created session {session_id} with {memory_type} memory")
        return memory
    
    def get_session(self, session_id: str) -> Optional[BaseChatMemory]:
        """
        Get an existing session's memory
        
        Args:
            session_id: Session identifier
        
        Returns:
            Memory instance or None
        """
        
        if session_id in self.sessions:
            self.sessions[session_id]["last_active"] = datetime.now()
            return self.sessions[session_id]["memory"]
        
        # Try to load from disk
        memory = self.load_session(session_id)
        if memory:
            return memory
        
        return None
    
    def add_message(self, session_id: str, message: str, is_human: bool = True):
        """
        Add a message to a session's memory
        
        Args:
            session_id: Session identifier
            message: Message content
            is_human: Whether the message is from a human
        """
        
        memory = self.get_session(session_id)
        if not memory:
            memory = self.create_session(session_id)
        
        if is_human:
            memory.chat_memory.add_user_message(message)
        else:
            memory.chat_memory.add_ai_message(message)
        
        # Update session activity
        if session_id in self.sessions:
            self.sessions[session_id]["last_active"] = datetime.now()
    
    def add_exchange(self, session_id: str, human_message: str, ai_message: str):
        """
        Add a complete exchange to memory
        
        Args:
            session_id: Session identifier
            human_message: Human's message
            ai_message: AI's response
        """
        
        self.add_message(session_id, human_message, is_human=True)
        self.add_message(session_id, ai_message, is_human=False)
    
    def get_history(self, session_id: str, format: str = "messages") -> Any:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session identifier
            format: Output format (messages, string, dict)
        
        Returns:
            Conversation history in requested format
        """
        
        memory = self.get_session(session_id)
        if not memory:
            return [] if format == "messages" else ""
        
        if format == "messages":
            return memory.chat_memory.messages
        elif format == "string":
            return memory.buffer if hasattr(memory, 'buffer') else str(memory.chat_memory.messages)
        elif format == "dict":
            messages = []
            for msg in memory.chat_memory.messages:
                messages.append({
                    "type": "human" if isinstance(msg, HumanMessage) else "ai",
                    "content": msg.content
                })
            return messages
        else:
            return memory.chat_memory.messages
    
    def clear_session(self, session_id: str):
        """
        Clear a session's memory
        
        Args:
            session_id: Session identifier
        """
        
        if session_id in self.sessions:
            self.sessions[session_id]["memory"].clear()
            logger.info(f"Cleared memory for session {session_id}")
    
    def save_session(self, session_id: str):
        """
        Save a session to disk
        
        Args:
            session_id: Session identifier
        """
        
        if session_id not in self.sessions:
            logger.warning(f"Session {session_id} not found")
            return
        
        session_data = self.sessions[session_id]
        
        # Prepare data for saving
        save_data = {
            "created_at": session_data["created_at"].isoformat(),
            "last_active": session_data["last_active"].isoformat(),
            "memory_type": session_data["memory_type"],
            "metadata": session_data["metadata"],
            "messages": []
        }
        
        # Extract messages
        memory = session_data["memory"]
        if hasattr(memory, 'chat_memory'):
            for msg in memory.chat_memory.messages:
                save_data["messages"].append({
                    "type": "human" if isinstance(msg, HumanMessage) else "ai",
                    "content": msg.content
                })
        
        # Save to file
        file_path = self.persistence_dir / f"{session_id}.json"
        with open(file_path, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        logger.info(f"Saved session {session_id} to {file_path}")
    
    def load_session(self, session_id: str) -> Optional[BaseChatMemory]:
        """
        Load a session from disk
        
        Args:
            session_id: Session identifier
        
        Returns:
            Loaded memory or None
        """
        
        file_path = self.persistence_dir / f"{session_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                save_data = json.load(f)
            
            # Create memory based on type
            memory = self.create_session(session_id, save_data.get("memory_type", "long_term"))
            
            # Restore messages
            for msg in save_data.get("messages", []):
                if msg["type"] == "human":
                    memory.chat_memory.add_user_message(msg["content"])
                else:
                    memory.chat_memory.add_ai_message(msg["content"])
            
            # Update metadata
            if session_id in self.sessions:
                self.sessions[session_id]["metadata"] = save_data.get("metadata", {})
                self.sessions[session_id]["created_at"] = datetime.fromisoformat(save_data["created_at"])
            
            logger.info(f"Loaded session {session_id} from {file_path}")
            return memory
            
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None
    
    def cleanup_old_sessions(self, days: int = 30):
        """
        Clean up sessions older than specified days
        
        Args:
            days: Number of days to keep sessions
        """
        
        cutoff_date = datetime.now() - timedelta(days=days)
        sessions_to_remove = []
        
        for session_id, session_data in self.sessions.items():
            if session_data["last_active"] < cutoff_date:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            # Save before removing
            self.save_session(session_id)
            del self.sessions[session_id]
            logger.info(f"Cleaned up session {session_id}")
    
    def get_context_for_property(self, property_id: str) -> Dict[str, Any]:
        """
        Get all context related to a specific property
        
        Args:
            property_id: Property identifier
        
        Returns:
            Aggregated context for the property
        """
        
        context = {
            "property_id": property_id,
            "conversations": [],
            "summary": "",
            "key_points": []
        }
        
        # Search through all sessions for property mentions
        for session_id, session_data in self.sessions.items():
            messages = self.get_history(session_id, format="dict")
            
            property_mentioned = False
            relevant_messages = []
            
            for msg in messages:
                if property_id in msg["content"]:
                    property_mentioned = True
                    relevant_messages.append(msg)
            
            if property_mentioned:
                context["conversations"].append({
                    "session_id": session_id,
                    "messages": relevant_messages,
                    "timestamp": session_data["last_active"].isoformat()
                })
        
        # Generate summary if LLM is available
        if self.llm and context["conversations"]:
            try:
                all_messages = []
                for conv in context["conversations"]:
                    all_messages.extend([m["content"] for m in conv["messages"]])
                
                summary_prompt = f"""Summarize the key points about property {property_id} 
                from these conversations: {' '.join(all_messages[:5000])}"""
                
                context["summary"] = self.llm.predict(summary_prompt)
            except Exception as e:
                logger.error(f"Error generating summary: {e}")
        
        return context
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        
        stats = {
            "active_sessions": len(self.sessions),
            "total_messages": 0,
            "memory_types": {},
            "oldest_session": None,
            "newest_session": None
        }
        
        for session_id, session_data in self.sessions.items():
            # Count messages
            messages = self.get_history(session_id, format="messages")
            stats["total_messages"] += len(messages)
            
            # Count memory types
            memory_type = session_data["memory_type"]
            stats["memory_types"][memory_type] = stats["memory_types"].get(memory_type, 0) + 1
            
            # Track oldest/newest
            created_at = session_data["created_at"]
            if not stats["oldest_session"] or created_at < stats["oldest_session"]:
                stats["oldest_session"] = created_at
            if not stats["newest_session"] or created_at > stats["newest_session"]:
                stats["newest_session"] = created_at
        
        # Convert dates to strings
        if stats["oldest_session"]:
            stats["oldest_session"] = stats["oldest_session"].isoformat()
        if stats["newest_session"]:
            stats["newest_session"] = stats["newest_session"].isoformat()
        
        return stats
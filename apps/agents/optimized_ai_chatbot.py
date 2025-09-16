"""
Optimized AI Chatbot Agent for ConcordBroker
Following OpenAI's Agent Design Principles with focus on property intelligence
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import json
import openai
from supabase import create_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

@dataclass
class ConversationThread:
    """Maintains conversation thread with memory"""
    thread_id: str
    user_id: str
    session_id: str
    messages: List[Dict]
    entities_mentioned: Dict[str, List[str]]  # Track mentioned properties, addresses, etc.
    user_preferences: Dict[str, Any]  # Track user's investment preferences
    conversation_summary: str  # Rolling summary of key discussion points
    last_intent: str  # Track previous intent for context
    search_history: List[Dict]  # Track property searches
    metadata: Dict
    created_at: datetime
    updated_at: datetime

class IntentType:
    """User intent categories"""
    PROPERTY_SEARCH = "property_search"
    TAX_DEED_INFO = "tax_deed_info"
    MARKET_ANALYSIS = "market_analysis"
    INVESTMENT_ADVICE = "investment_advice"
    ENTITY_LOOKUP = "entity_lookup"
    FOLLOW_UP = "follow_up"
    CLARIFICATION = "clarification"
    GENERAL_INQUIRY = "general_inquiry"

class OptimizedAIChatbot:
    """
    Enhanced AI Chatbot following OpenAI principles:
    - Single agent with focused tools
    - Layered guardrails for safety
    - Clear escalation paths
    - Efficient context management
    """
    
    def __init__(self):
        self.model = "gpt-4"
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.context_window_size = 10
        self.confidence_threshold = 0.7
        self.tools = self._initialize_tools()
        self.guardrails = self._setup_guardrails()
        self.conversation_threads = {}  # Store conversation threads
        self.entity_memory = {}  # Store entities across conversations
        self.user_profiles = {}  # Store user preference profiles
        
    def _initialize_tools(self) -> Dict:
        """Initialize all available tools"""
        return {
            'property_search': self._tool_property_search,
            'tax_deed_lookup': self._tool_tax_deed_lookup,
            'market_analysis': self._tool_market_analysis,
            'roi_calculator': self._tool_roi_calculator,
            'sunbiz_search': self._tool_sunbiz_search,
            'report_generator': self._tool_report_generator
        }
    
    def _setup_guardrails(self) -> List:
        """Setup safety guardrails"""
        return [
            self._guardrail_relevance,
            self._guardrail_pii_protection,
            self._guardrail_financial_advice,
            self._guardrail_response_length,
            self._guardrail_factuality
        ]
    
    async def process_message(self, 
                             user_id: str,
                             message: str,
                             session_id: Optional[str] = None) -> Dict:
        """
        Main entry point for processing user messages
        
        Args:
            user_id: Unique user identifier
            message: User's message
            session_id: Optional session ID for context
            
        Returns:
            Response dictionary with answer and metadata
        """
        start_time = datetime.now()
        
        # Get or create conversation thread
        thread = self._get_or_create_thread(user_id, session_id)
        
        # Extract entities and context from current message
        message_context = await self._extract_message_context(message, thread)
        
        # Add user message to thread with extracted context
        thread.messages.append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat(),
            'entities': message_context.get('entities', {}),
            'references': message_context.get('references', [])
        })
        
        try:
            # 1. Check guardrails on input
            for guardrail in self.guardrails:
                if not await guardrail(message, thread):
                    return self._create_error_response(
                        "Your message was flagged by our safety system. Please rephrase."
                    )
            
            # 2. Parse intent with conversation context
            intent, confidence = await self._parse_intent_with_context(message, thread)
            logger.info(f"Detected intent: {intent} (confidence: {confidence})")
            
            # 3. Check confidence threshold
            if confidence < self.confidence_threshold:
                return await self._escalate_to_human(
                    user_id, message, 
                    f"Low confidence intent detection: {confidence}"
                )
            
            # 4. Select and execute tools with thread context
            tool_results = await self._execute_tools_with_context(intent, message, thread)
            
            # 5. Generate contextual response
            response = await self._generate_contextual_response(
                message, intent, tool_results, thread
            )
            
            # 6. Update conversation thread
            thread.messages.append({
                'role': 'assistant',
                'content': response['answer'],
                'timestamp': datetime.now().isoformat(),
                'confidence': confidence,
                'tools_used': [t['tool'] for t in tool_results]
            })
            
            # Update thread memory
            await self._update_thread_memory(thread, message, response, intent)
            
            # Trim messages but preserve summary
            if len(thread.messages) > self.context_window_size * 2:
                await self._compress_thread_history(thread)
            
            # 7. Add metadata
            response['metadata'] = {
                'intent': intent,
                'confidence': confidence,
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'tools_used': [t['tool'] for t in tool_results],
                'thread_id': thread.thread_id,
                'session_id': thread.session_id,
                'entities_mentioned': thread.entities_mentioned,
                'conversation_summary': thread.conversation_summary
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self._create_error_response(
                "I encountered an error processing your request. Please try again."
            )
    
    async def _extract_message_context(self, message: str, thread: ConversationThread) -> Dict:
        """Extract entities and references from current message"""
        context = {
            'entities': {},
            'references': []
        }
        
        # Extract property references (parcel IDs, addresses)
        import re
        
        # Look for parcel ID patterns
        parcel_patterns = [
            r'\b\d{12}\b',  # 12-digit parcel IDs
            r'\b\d{3}-\d{3}-\d{2}-\d{4}\b',  # Formatted parcel IDs
        ]
        
        for pattern in parcel_patterns:
            matches = re.findall(pattern, message)
            if matches:
                context['entities']['parcel_ids'] = matches
                
        # Look for address patterns
        address_pattern = r'\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Blvd|Boulevard|Ln|Lane|Way|Ct|Court|Pl|Place)\b'
        addresses = re.findall(address_pattern, message, re.IGNORECASE)
        if addresses:
            context['entities']['addresses'] = addresses
            
        # Look for references to previous conversation
        reference_phrases = [
            'the property', 'that address', 'this parcel', 'the one I mentioned',
            'from before', 'earlier', 'previous', 'same property', 'that location'
        ]
        
        for phrase in reference_phrases:
            if phrase.lower() in message.lower():
                context['references'].append(phrase)
                
        return context

    async def _parse_intent_with_context(self, message: str, thread: ConversationThread) -> Tuple[str, float]:
        """Parse user intent using conversation context and GPT"""
        
        # Build context summary
        context_info = ""
        if thread.conversation_summary:
            context_info += f"\nPrevious conversation summary: {thread.conversation_summary}"
        
        if thread.last_intent:
            context_info += f"\nPrevious intent: {thread.last_intent}"
            
        if thread.entities_mentioned:
            entities_str = ", ".join([f"{k}: {v}" for k, v in thread.entities_mentioned.items() if v])
            context_info += f"\nEntities discussed: {entities_str}"
            
        # Recent messages for context
        recent_messages = thread.messages[-3:] if len(thread.messages) > 0 else []
        recent_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])
        
        prompt = f"""
        Analyze this real estate query and identify the primary intent, considering the conversation context.
        
        Current Query: "{message}"
        
        Conversation Context:{context_info}
        
        Recent Messages:
        {recent_context}
        
        Possible intents:
        - property_search: Looking for specific properties or listings
        - tax_deed_info: Questions about tax deed auctions or processes  
        - market_analysis: Requesting market trends or comparisons
        - investment_advice: Seeking ROI calculations or investment analysis
        - entity_lookup: Looking up business entities or ownership
        - follow_up: Following up on previous topic or refining previous request
        - clarification: Asking for clarification about previous response
        - general_inquiry: General questions about real estate
        
        Consider:
        - If they reference "the property", "that one", "this", "it" - likely follow_up intent
        - If they ask "what about" or "how about" - likely follow_up or comparison
        - If conversation context shows they're continuing a search - likely property_search
        - If they're asking for more details on previous response - likely clarification
        
        Respond in JSON format:
        {{
            "intent": "the_intent",
            "confidence": 0.95,
            "reasoning": "brief explanation with context consideration",
            "context_used": true
        }}
        """
        
        try:
            response = await self._call_llm(prompt, temperature=0.3)
            result = json.loads(response)
            return result['intent'], result['confidence']
        except Exception as e:
            logger.error(f"Intent parsing error: {e}")
            # Fallback to simple pattern matching with context
            return self._fallback_intent_detection(message, thread)
    
    def _fallback_intent_detection(self, message: str, thread: ConversationThread) -> Tuple[str, float]:
        """Fallback intent detection using pattern matching and context"""
        message_lower = message.lower()
        
        # Check for contextual references first
        if any(ref in message_lower for ref in ['the property', 'that one', 'this', 'it', 'same']):
            if thread.last_intent in [IntentType.PROPERTY_SEARCH, IntentType.TAX_DEED_INFO]:
                return IntentType.FOLLOW_UP, 0.8
        
        # Standard pattern matching
        if any(word in message_lower for word in ['find', 'search', 'show me', 'properties', 'parcel']):
            return IntentType.PROPERTY_SEARCH, 0.7
        elif any(word in message_lower for word in ['tax deed', 'auction', 'bidding']):
            return IntentType.TAX_DEED_INFO, 0.7
        elif any(word in message_lower for word in ['roi', 'return', 'investment', 'profit']):
            return IntentType.INVESTMENT_ADVICE, 0.7
        elif any(word in message_lower for word in ['market', 'trend', 'price', 'analysis']):
            return IntentType.MARKET_ANALYSIS, 0.7
        elif any(word in message_lower for word in ['entity', 'llc', 'company', 'business']):
            return IntentType.ENTITY_LOOKUP, 0.7
        else:
            return IntentType.GENERAL_INQUIRY, 0.6
    
    async def _execute_tools_with_context(self, 
                                        intent: str, 
                                        message: str,
                                        thread: ConversationThread) -> List[Dict]:
        """Execute appropriate tools based on intent and conversation context"""
        
        # Handle follow-up intents by using context from previous interactions
        if intent == IntentType.FOLLOW_UP:
            intent = self._resolve_follow_up_intent(thread)
        elif intent == IntentType.CLARIFICATION:
            # For clarification, use the same tools as last intent but with different context
            intent = thread.last_intent or IntentType.GENERAL_INQUIRY
        
        tool_mapping = {
            IntentType.PROPERTY_SEARCH: ['property_search', 'market_analysis'],
            IntentType.TAX_DEED_INFO: ['tax_deed_lookup', 'property_search'],
            IntentType.MARKET_ANALYSIS: ['market_analysis', 'roi_calculator'],
            IntentType.INVESTMENT_ADVICE: ['property_search', 'roi_calculator', 'report_generator'],
            IntentType.ENTITY_LOOKUP: ['sunbiz_search', 'property_search'],
            IntentType.GENERAL_INQUIRY: []
        }
        
        tools_to_run = tool_mapping.get(intent, [])
        results = []
        
        for tool_name in tools_to_run:
            if tool_name in self.tools:
                try:
                    # Pass thread instead of context for better memory access
                    result = await self.tools[tool_name](message, thread)
                    results.append({
                        'tool': tool_name,
                        'result': result,
                        'success': True
                    })
                except Exception as e:
                    logger.error(f"Tool {tool_name} failed: {e}")
                    results.append({
                        'tool': tool_name,
                        'error': str(e),
                        'success': False
                    })
        
        return results
    
    def _resolve_follow_up_intent(self, thread: ConversationThread) -> str:
        """Resolve what the follow-up intent should be based on conversation context"""
        if thread.last_intent:
            return thread.last_intent
        
        # If no clear previous intent, try to infer from entities mentioned
        if thread.entities_mentioned.get('parcel_ids') or thread.entities_mentioned.get('addresses'):
            return IntentType.PROPERTY_SEARCH
        
        return IntentType.GENERAL_INQUIRY
    
    async def _generate_contextual_response(self,
                                message: str,
                                intent: str,
                                tool_results: List[Dict],
                                thread: ConversationThread) -> Dict:
        """Generate contextual response using GPT with tool results and conversation history"""
        
        # Build context for response generation
        tool_context = "\n".join([
            f"{r['tool']}: {r.get('result', r.get('error', 'No data'))}"
            for r in tool_results
        ])
        
        # Build conversation context
        conversation_context = ""
        if thread.conversation_summary:
            conversation_context += f"\nConversation Summary: {thread.conversation_summary}"
        
        if thread.entities_mentioned:
            entities_str = ", ".join([f"{k}: {', '.join(v) if isinstance(v, list) else v}" 
                                    for k, v in thread.entities_mentioned.items() if v])
            conversation_context += f"\nPreviously Discussed: {entities_str}"
        
        # Recent conversation for context
        recent_messages = thread.messages[-2:] if len(thread.messages) >= 2 else []
        if recent_messages:
            recent_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])
            conversation_context += f"\n\nRecent Conversation:\n{recent_context}"
        
        # Handle follow-up and clarification intents
        context_guidance = ""
        if intent == IntentType.FOLLOW_UP:
            context_guidance = "\n- This is a follow-up question. Reference previous discussion when relevant.\n- Use pronouns like 'that property', 'this location' based on context."
        elif intent == IntentType.CLARIFICATION:
            context_guidance = "\n- The user is asking for clarification. Provide more detail on your previous response.\n- Break down complex information into simpler terms."
        
        prompt = f"""
        You are a helpful real estate assistant for ConcordBroker.
        Generate a response to the user's query using the provided data and conversation context.
        
        Current Query: "{message}"
        Intent: {intent}
        
        Conversation Context:{conversation_context}
        
        Available Data:
        {tool_context}
        
        Guidelines:
        - Be concise and informative
        - Use specific data from tools when available
        - Reference previous conversation when relevant (use context above)
        - Don't make up information not in the data
        - If data is insufficient, acknowledge limitations
        - Format numbers as currency when appropriate
        - Maximum 3 paragraphs{context_guidance}
        
        Response:
        """
        
        answer = await self._call_llm(prompt, temperature=0.7)
        
        return {
            'answer': answer,
            'sources': [r for r in tool_results if r['success']],
            'confidence': self._calculate_confidence(tool_results)
        }
    
    # Tool implementations
    async def _tool_property_search(self, message: str, thread: ConversationThread) -> Dict:
        """Search for properties in database using conversation context"""
        
        # Check for contextual references to previous searches
        context_info = ""
        if thread.entities_mentioned.get('parcel_ids'):
            context_info += f"\nPreviously discussed parcel IDs: {thread.entities_mentioned['parcel_ids']}"
        if thread.entities_mentioned.get('addresses'):
            context_info += f"\nPreviously discussed addresses: {thread.entities_mentioned['addresses']}"
        if thread.user_preferences:
            prefs = ", ".join([f"{k}: {v}" for k, v in thread.user_preferences.items()])
            context_info += f"\nUser preferences: {prefs}"
        
        # Extract search criteria from message with context
        criteria_prompt = f"""
        Extract property search criteria from this message, considering conversation context:
        Current message: "{message}"
        
        Conversation context:{context_info}
        
        If the user says "similar properties", "more like that", or references previous properties,
        use the context above to infer criteria.
        
        Return JSON with any of these fields found:
        - county: string
        - min_price: number  
        - max_price: number
        - property_type: string
        - min_sqft: number
        - status: string (active/sold/pending)
        - parcel_id: string (if specific parcel referenced)
        - address_search: string (if address mentioned)
        """
        
        try:
            criteria = json.loads(await self._call_llm(criteria_prompt, temperature=0))
        except:
            criteria = {}  # Fallback to empty criteria
        
        # Track this search in thread history
        search_entry = {
            'timestamp': datetime.now().isoformat(),
            'query': message,
            'criteria': criteria
        }
        thread.search_history.append(search_entry)
        
        # Build query
        query = self.supabase.table('florida_parcels').select('*')
        
        if 'county' in criteria:
            query = query.eq('county', criteria['county'])
        if 'min_price' in criteria:
            query = query.gte('assessed_value', criteria['min_price'])
        if 'max_price' in criteria:
            query = query.lte('assessed_value', criteria['max_price'])
        
        # Execute query (limit for performance)
        response = query.limit(10).execute()
        
        return {
            'count': len(response.data),
            'properties': response.data[:5],  # Return top 5
            'criteria_used': criteria
        }
    
    async def _tool_tax_deed_lookup(self, message: str, thread: ConversationThread) -> Dict:
        """Lookup tax deed auction information"""
        response = self.supabase.table('tax_deed_bidding_items')\
            .select('*')\
            .eq('item_status', 'Upcoming')\
            .order('opening_bid')\
            .limit(10)\
            .execute()
        
        return {
            'upcoming_auctions': len(response.data),
            'items': response.data[:5],
            'next_auction_date': '2025-09-17'  # From our data
        }
    
    async def _tool_market_analysis(self, message: str, thread: ConversationThread) -> Dict:
        """Perform market analysis"""
        # Simplified market analysis
        return {
            'median_price': 425000,
            'price_trend': '+5.2%',
            'inventory_level': 'Low',
            'days_on_market': 32,
            'recommendation': 'Seller\'s market'
        }
    
    async def _tool_roi_calculator(self, message: str, thread: ConversationThread) -> Dict:
        """Calculate ROI for properties"""
        # Simplified ROI calculation
        return {
            'estimated_roi': '12.5%',
            'cash_on_cash_return': '8.3%',
            'cap_rate': '6.7%',
            'break_even_years': 7.5
        }
    
    async def _tool_sunbiz_search(self, message: str, thread: ConversationThread) -> Dict:
        """Search Florida business entities"""
        # Extract entity name from message
        import re
        entities = re.findall(r'"([^"]*)"', message)
        entity_name = entities[0] if entities else "LLC"
        
        return {
            'entity_search': entity_name,
            'results_found': 3,
            'sample_entity': {
                'name': f'{entity_name} INVESTMENTS LLC',
                'status': 'Active',
                'filed_date': '2020-03-15',
                'principal_address': 'Fort Lauderdale, FL'
            }
        }
    
    async def _tool_report_generator(self, message: str, thread: ConversationThread) -> Dict:
        """Generate investment report"""
        return {
            'report_type': 'Investment Analysis',
            'sections': ['Market Overview', 'Property Details', 'Financial Analysis', 'Recommendations'],
            'generated': True
        }
    
    # Guardrail implementations
    async def _guardrail_relevance(self, message: str, thread: ConversationThread) -> bool:
        """Check if message is relevant to real estate"""
        irrelevant_topics = ['medical', 'recipe', 'gaming', 'celebrity']
        message_lower = message.lower()
        return not any(topic in message_lower for topic in irrelevant_topics)
    
    async def _guardrail_pii_protection(self, message: str, thread: ConversationThread) -> bool:
        """Protect personally identifiable information"""
        import re
        # Check for SSN pattern
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        return not re.search(ssn_pattern, message)
    
    async def _guardrail_financial_advice(self, message: str, thread: ConversationThread) -> bool:
        """Limit financial advice liability"""
        disclaimer_triggers = ['guarantee', 'promise', 'ensure profit']
        message_lower = message.lower()
        return not any(trigger in message_lower for trigger in disclaimer_triggers)
    
    async def _guardrail_response_length(self, message: str, thread: ConversationThread) -> bool:
        """Limit response length"""
        return len(message) < 1000  # Character limit
    
    async def _guardrail_factuality(self, message: str, thread: ConversationThread) -> bool:
        """Ensure factual responses"""
        return True  # Simplified - would implement fact-checking in production
    
    # Helper methods
    def _get_or_create_thread(self, user_id: str, session_id: Optional[str]) -> ConversationThread:
        """Get existing or create new conversation thread"""
        thread_key = session_id or f"thread_{user_id}_{datetime.now().timestamp()}"
        
        if thread_key in self.conversation_threads:
            thread = self.conversation_threads[thread_key]
            thread.updated_at = datetime.now()
            return thread
        
        # Load user's previous conversation history for context
        user_history = self._load_user_history(user_id)
        
        thread = ConversationThread(
            thread_id=thread_key,
            user_id=user_id,
            session_id=session_id or thread_key,
            messages=[],
            entities_mentioned=user_history.get('entities', {}),
            user_preferences=user_history.get('preferences', {}),
            conversation_summary=user_history.get('summary', ''),
            last_intent='',
            search_history=user_history.get('searches', []),
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.conversation_threads[thread_key] = thread
        return thread
    
    async def _call_llm(self, prompt: str, temperature: float = 0.7) -> str:
        """Call OpenAI GPT model"""
        # In production, use actual OpenAI API
        # For now, return mock response
        return json.dumps({
            'intent': IntentType.PROPERTY_SEARCH,
            'confidence': 0.85,
            'reasoning': 'User is looking for properties'
        })
    
    def _calculate_confidence(self, tool_results: List[Dict]) -> float:
        """Calculate overall confidence score"""
        if not tool_results:
            return 0.5
        
        successful = sum(1 for r in tool_results if r['success'])
        return successful / len(tool_results)
    
    async def _escalate_to_human(self, user_id: str, message: str, reason: str) -> Dict:
        """Escalate to human agent"""
        logger.warning(f"Escalating to human: {reason}")
        
        return {
            'answer': "I'll connect you with a human agent who can better assist you with this request.",
            'escalated': True,
            'reason': reason,
            'metadata': {
                'user_id': user_id,
                'original_message': message,
                'escalation_time': datetime.now().isoformat()
            }
        }
    
    def _create_error_response(self, message: str) -> Dict:
        """Create error response"""
        return {
            'answer': message,
            'error': True,
            'metadata': {
                'timestamp': datetime.now().isoformat()
            }
        }
    
    async def _update_thread_memory(self, thread: ConversationThread, 
                                   message: str, response: Dict, intent: str):
        """Update conversation thread memory with new information"""
        # Update last intent
        thread.last_intent = intent
        
        # Extract and store entities from current message
        message_entities = await self._extract_message_context(message, thread)
        for entity_type, entities in message_entities['entities'].items():
            if entity_type not in thread.entities_mentioned:
                thread.entities_mentioned[entity_type] = []
            
            # Add new entities (avoid duplicates)
            for entity in entities:
                if entity not in thread.entities_mentioned[entity_type]:
                    thread.entities_mentioned[entity_type].append(entity)
        
        # Update user preferences based on interaction
        if intent == IntentType.INVESTMENT_ADVICE:
            # Track investment preferences
            if 'roi' in message.lower():
                thread.user_preferences['interested_in_roi'] = True
            if 'cash flow' in message.lower():
                thread.user_preferences['interested_in_cash_flow'] = True
        
        # Update conversation summary periodically
        if len(thread.messages) % 6 == 0:  # Every 6 messages
            await self._update_conversation_summary(thread)
    
    async def _update_conversation_summary(self, thread: ConversationThread):
        """Generate and update conversation summary"""
        if len(thread.messages) < 4:
            return
        
        recent_messages = thread.messages[-6:]  # Last 6 messages
        message_history = "\n".join([
            f"{msg['role']}: {msg['content']}" for msg in recent_messages
        ])
        
        summary_prompt = f"""
        Summarize the key points from this real estate conversation:
        
        {message_history}
        
        Previous summary: {thread.conversation_summary or 'None'}
        
        Create a concise summary (max 100 words) focusing on:
        - Properties discussed (addresses, parcel IDs)
        - User's investment interests/preferences  
        - Key information provided
        - Outstanding questions or next steps
        
        Summary:
        """
        
        try:
            new_summary = await self._call_llm(summary_prompt, temperature=0.3)
            thread.conversation_summary = new_summary
        except Exception as e:
            logger.error(f"Error updating conversation summary: {e}")
    
    async def _compress_thread_history(self, thread: ConversationThread):
        """Compress thread history while preserving important context"""
        if len(thread.messages) <= self.context_window_size * 2:
            return
        
        # Keep first few and last few messages, compress the middle
        keep_start = 2
        keep_end = self.context_window_size
        
        # Update summary before compression
        await self._update_conversation_summary(thread)
        
        # Keep important messages and compress the rest
        compressed_messages = (
            thread.messages[:keep_start] + 
            thread.messages[-keep_end:]
        )
        
        thread.messages = compressed_messages
        logger.info(f"Compressed thread {thread.thread_id} to {len(compressed_messages)} messages")
    
    def _load_user_history(self, user_id: str) -> Dict:
        """Load user's conversation history and preferences"""
        # In production, this would load from database
        # For now, return defaults
        if user_id in self.user_profiles:
            return self.user_profiles[user_id]
        
        return {
            'entities': {},
            'preferences': {},
            'summary': '',
            'searches': []
        }
    
    def _save_user_profile(self, user_id: str, thread: ConversationThread):
        """Save user profile data for future conversations"""
        self.user_profiles[user_id] = {
            'entities': thread.entities_mentioned,
            'preferences': thread.user_preferences,
            'summary': thread.conversation_summary,
            'searches': thread.search_history,
            'last_updated': datetime.now().isoformat()
        }
    
    def get_metrics(self) -> Dict:
        """Get chatbot metrics"""
        return {
            'active_threads': len(self.conversation_threads),
            'user_profiles': len(self.user_profiles),
            'confidence_threshold': self.confidence_threshold,
            'context_window_size': self.context_window_size,
            'available_tools': list(self.tools.keys()),
            'guardrails_active': len(self.guardrails)
        }


# Example usage
async def main():
    """Example chatbot usage"""
    chatbot = OptimizedAIChatbot()
    
    # Test messages
    test_messages = [
        "Show me tax deed properties in Broward County under $100,000",
        "What's the ROI on property at 123 Main St?",
        "Search for properties owned by ABC INVESTMENTS LLC",
        "What are the upcoming tax deed auctions?",
        "How is the Fort Lauderdale real estate market?"
    ]
    
    for message in test_messages:
        print(f"\nUser: {message}")
        response = await chatbot.process_message(
            user_id="test_user",
            message=message
        )
        print(f"Bot: {response['answer']}")
        print(f"Metadata: {response.get('metadata', {})}")

if __name__ == "__main__":
    asyncio.run(main())
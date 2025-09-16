"""
AI Search Service with GPT Integration and Chain of Agents
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import openai
from supabase import create_client, Client
from dotenv import load_dotenv
import numpy as np
from sentence_transformers import SentenceTransformer

load_dotenv()

class PropertySearchAgent:
    """Base class for property search agents"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.name = "Base Agent"
        
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process the search context and return results"""
        raise NotImplementedError

class NaturalLanguageAgent(PropertySearchAgent):
    """Agent for processing natural language queries"""
    
    def __init__(self, supabase_client: Client):
        super().__init__(supabase_client)
        self.name = "Natural Language Agent"
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract intent and entities from natural language"""
        query = context.get('query', '')
        
        # Parse natural language for property features
        features = {
            'location': [],
            'property_type': None,
            'price_range': None,
            'features': [],
            'bedrooms': None,
            'bathrooms': None,
            'year_built': None
        }
        
        # Keywords mapping
        property_types = {
            'house': 'Residential',
            'home': 'Residential',
            'condo': 'Residential',
            'apartment': 'Residential',
            'commercial': 'Commercial',
            'office': 'Commercial',
            'retail': 'Commercial',
            'industrial': 'Industrial',
            'warehouse': 'Industrial',
            'land': 'Vacant',
            'vacant': 'Vacant',
            'farm': 'Agricultural',
            'agricultural': 'Agricultural'
        }
        
        # Extract property type
        query_lower = query.lower()
        for keyword, ptype in property_types.items():
            if keyword in query_lower:
                features['property_type'] = ptype
                break
        
        # Extract price mentions
        import re
        price_patterns = [
            r'under\s+\$?(\d+)k', 
            r'below\s+\$?(\d+)k',
            r'less\s+than\s+\$?(\d+)k',
            r'under\s+\$?([\d,]+)',
            r'below\s+\$?([\d,]+)',
            r'between\s+\$?([\d,]+)\s+and\s+\$?([\d,]+)',
            r'\$?([\d,]+)\s+to\s+\$?([\d,]+)'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                if 'between' in pattern or 'to' in pattern:
                    if len(matches[0]) == 2:
                        min_price = int(matches[0][0].replace(',', ''))
                        max_price = int(matches[0][1].replace(',', ''))
                        if 'k' in query_lower:
                            min_price *= 1000
                            max_price *= 1000
                        features['price_range'] = {'min': min_price, 'max': max_price}
                else:
                    max_price = int(matches[0].replace(',', ''))
                    if 'k' in query_lower:
                        max_price *= 1000
                    features['price_range'] = {'max': max_price}
                break
        
        # Extract bedroom/bathroom counts
        bed_match = re.search(r'(\d+)\s*(?:bed|br|bedroom)', query_lower)
        if bed_match:
            features['bedrooms'] = int(bed_match.group(1))
            
        bath_match = re.search(r'(\d+)\s*(?:bath|ba|bathroom)', query_lower)
        if bath_match:
            features['bathrooms'] = int(bath_match.group(1))
        
        # Extract location mentions
        locations = ['miami', 'fort lauderdale', 'hollywood', 'pompano', 'coral springs', 
                    'davie', 'plantation', 'sunrise', 'pembroke pines', 'miramar']
        for loc in locations:
            if loc in query_lower:
                features['location'].append(loc.title())
        
        # Extract special features
        feature_keywords = {
            'pool': 'pool',
            'waterfront': 'waterfront',
            'water': 'waterfront',
            'ocean': 'ocean view',
            'beach': 'beach access',
            'garage': 'garage',
            'renovated': 'recently renovated',
            'updated': 'recently updated',
            'modern': 'modern',
            'luxury': 'luxury',
            'gated': 'gated community',
            'golf': 'golf course'
        }
        
        for keyword, feature in feature_keywords.items():
            if keyword in query_lower:
                features['features'].append(feature)
        
        context['extracted_features'] = features
        context['embeddings'] = self.model.encode(query).tolist()
        
        return context

class DatabaseSearchAgent(PropertySearchAgent):
    """Agent for searching the database based on extracted features"""
    
    def __init__(self, supabase_client: Client):
        super().__init__(supabase_client)
        self.name = "Database Search Agent"
        
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Search database using extracted features"""
        features = context.get('extracted_features', {})
        
        # Build query
        query = self.supabase.from_('florida_parcels').select('*')
        
        # Apply property type filter
        if features.get('property_type'):
            property_type = features['property_type']
            if property_type == 'Residential':
                query = query.gte('dor_cd', '001').lte('dor_cd', '009')
            elif property_type == 'Commercial':
                query = query.gte('dor_cd', '010').lte('dor_cd', '039')
            elif property_type == 'Industrial':
                query = query.gte('dor_cd', '040').lte('dor_cd', '049')
            elif property_type == 'Agricultural':
                query = query.gte('dor_cd', '050').lte('dor_cd', '069')
            elif property_type == 'Vacant':
                query = query.or_('dor_cd.eq.000,dor_cd.gte.090.lte.095')
        
        # Apply price filter
        if features.get('price_range'):
            price_range = features['price_range']
            if 'min' in price_range:
                query = query.gte('taxable_value', price_range['min'])
            if 'max' in price_range:
                query = query.lte('taxable_value', price_range['max'])
        
        # Apply location filter
        if features.get('location'):
            location_filter = '|'.join([f'%{loc}%' for loc in features['location']])
            query = query.ilike('phy_city', location_filter)
        
        # Apply bedroom/bathroom filters if available
        if features.get('bedrooms'):
            query = query.eq('bedrooms', features['bedrooms'])
        if features.get('bathrooms'):
            query = query.eq('bathrooms', features['bathrooms'])
        
        # Limit results
        query = query.limit(50)
        
        # Execute query
        try:
            result = query.execute()
            context['properties'] = result.data
            context['total_found'] = len(result.data)
        except Exception as e:
            context['error'] = str(e)
            context['properties'] = []
            context['total_found'] = 0
        
        return context

class RankingAgent(PropertySearchAgent):
    """Agent for ranking and scoring properties"""
    
    def __init__(self, supabase_client: Client):
        super().__init__(supabase_client)
        self.name = "Ranking Agent"
        
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Rank properties based on relevance to query"""
        properties = context.get('properties', [])
        features = context.get('extracted_features', {})
        
        if not properties:
            return context
        
        # Score each property
        for prop in properties:
            score = 0
            
            # Location match
            if features.get('location'):
                for loc in features['location']:
                    if loc.lower() in (prop.get('phy_city', '') or '').lower():
                        score += 20
            
            # Feature match
            if features.get('features'):
                for feature in features['features']:
                    if 'waterfront' in feature.lower():
                        # Check if property has waterfront indicators
                        if prop.get('waterfront'):
                            score += 15
                    if 'pool' in feature.lower():
                        if prop.get('pool'):
                            score += 10
            
            # Price range match
            if features.get('price_range'):
                taxable_value = prop.get('taxable_value', 0)
                if 'max' in features['price_range']:
                    if taxable_value <= features['price_range']['max']:
                        score += 25
                if 'min' in features['price_range']:
                    if taxable_value >= features['price_range']['min']:
                        score += 10
            
            # Recency bonus
            sale_date = prop.get('sale_date')
            if sale_date:
                try:
                    sale_year = int(sale_date[:4])
                    if sale_year >= 2024:
                        score += 5
                except:
                    pass
            
            prop['relevance_score'] = score
        
        # Sort by relevance score
        properties.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        context['properties'] = properties[:20]  # Return top 20
        
        return context

class GPTEnhancementAgent(PropertySearchAgent):
    """Agent for enhancing results with GPT insights"""
    
    def __init__(self, supabase_client: Client, openai_key: str):
        super().__init__(supabase_client)
        self.name = "GPT Enhancement Agent"
        openai.api_key = openai_key
        
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use GPT to provide insights and recommendations"""
        query = context.get('query', '')
        properties = context.get('properties', [])[:5]  # Top 5 properties
        
        if not properties:
            context['gpt_insights'] = "No properties found matching your criteria."
            return context
        
        # Prepare property summaries
        property_summaries = []
        for i, prop in enumerate(properties, 1):
            summary = f"{i}. {prop.get('phy_addr1', 'Unknown Address')}, "
            summary += f"{prop.get('phy_city', 'Unknown City')} - "
            summary += f"${prop.get('taxable_value', 0):,.0f}"
            if prop.get('bedrooms'):
                summary += f", {prop.get('bedrooms')} beds"
            if prop.get('bathrooms'):
                summary += f", {prop.get('bathrooms')} baths"
            property_summaries.append(summary)
        
        # Create GPT prompt
        prompt = f"""
        User is searching for: "{query}"
        
        Top matching properties:
        {chr(10).join(property_summaries)}
        
        Provide a brief, helpful response (2-3 sentences) that:
        1. Confirms what was found
        2. Highlights the best match and why
        3. Suggests what to consider or look for
        
        Keep it conversational and helpful.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful real estate assistant providing property search insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            context['gpt_insights'] = response.choices[0].message['content']
        except Exception as e:
            context['gpt_insights'] = f"Found {len(properties)} properties matching your criteria."
        
        return context

class AISearchOrchestrator:
    """Main orchestrator for the chain of agents"""
    
    def __init__(self):
        # Initialize Supabase
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        )
        
        # Initialize agents
        self.agents = [
            NaturalLanguageAgent(self.supabase),
            DatabaseSearchAgent(self.supabase),
            RankingAgent(self.supabase),
            GPTEnhancementAgent(self.supabase, os.getenv('OPENAI_API_KEY', ''))
        ]
        
        # Conversation history
        self.conversations = {}
    
    async def search(self, query: str, conversation_id: str = None) -> Dict[str, Any]:
        """Execute the chain of agents for property search"""
        
        # Initialize context
        context = {
            'query': query,
            'conversation_id': conversation_id or str(datetime.now().timestamp()),
            'timestamp': datetime.now().isoformat(),
            'history': []
        }
        
        # Get conversation history if exists
        if conversation_id and conversation_id in self.conversations:
            context['history'] = self.conversations[conversation_id]
        
        # Execute chain of agents
        for agent in self.agents:
            try:
                context = await agent.process(context)
                context['history'].append({
                    'agent': agent.name,
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                })
            except Exception as e:
                context['history'].append({
                    'agent': agent.name,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': str(e)
                })
        
        # Store conversation
        if conversation_id:
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []
            self.conversations[conversation_id].append({
                'query': query,
                'timestamp': context['timestamp'],
                'results_count': context.get('total_found', 0)
            })
        
        # Format response
        response = {
            'success': True,
            'query': query,
            'conversation_id': context['conversation_id'],
            'extracted_features': context.get('extracted_features', {}),
            'properties': context.get('properties', []),
            'total_found': context.get('total_found', 0),
            'insights': context.get('gpt_insights', ''),
            'processing_history': context.get('history', [])
        }
        
        return response
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Get conversation history"""
        return self.conversations.get(conversation_id, [])
    
    def clear_conversation(self, conversation_id: str):
        """Clear conversation history"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]

# Singleton instance
ai_search_service = AISearchOrchestrator()
"""
Specialized LangChain Agents for ConcordBroker
Each agent handles specific aspects of property analysis and investment advice
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from langchain.agents import Tool, AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage
from langchain_core.messages import BaseMessage
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.callbacks import StdOutCallbackHandler
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import GoogleSearchAPIWrapper
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class PropertyAnalysisAgent:
    """
    Agent specialized in comprehensive property analysis
    Evaluates properties based on multiple criteria and provides investment recommendations
    """
    
    def __init__(self, llm, memory, vector_store):
        self.llm = llm
        self.memory = memory
        self.vector_store = vector_store
        
        # Define the agent's system prompt
        self.system_prompt = """You are an expert real estate analyst for ConcordBroker, specializing in Florida properties.
        Your role is to provide comprehensive property analysis including:
        1. Investment potential scoring (0-100)
        2. Risk assessment
        3. Market positioning
        4. Renovation/flip potential
        5. Rental income projections
        6. Tax implications
        7. Comparable property analysis
        
        Always provide data-driven insights and actionable recommendations.
        Consider tax liens, market trends, property condition, and location factors.
        Be specific with numbers and percentages when possible."""
        
        # Initialize tools
        self.tools = self._create_tools()
        
        # Create the agent
        self.agent = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for property analysis"""
        
        tools = [
            Tool(
                name="search_comparables",
                func=self._search_comparable_properties,
                description="Search for comparable properties in the same area"
            ),
            Tool(
                name="calculate_roi",
                func=self._calculate_roi,
                description="Calculate return on investment for a property"
            ),
            Tool(
                name="assess_renovation_cost",
                func=self._assess_renovation_cost,
                description="Estimate renovation costs based on property condition"
            ),
            Tool(
                name="analyze_tax_liens",
                func=self._analyze_tax_liens,
                description="Analyze tax liens and their impact on investment"
            ),
            Tool(
                name="estimate_rental_income",
                func=self._estimate_rental_income,
                description="Estimate potential rental income for a property"
            ),
            Tool(
                name="check_market_trends",
                func=self._check_market_trends,
                description="Check current market trends for the area"
            )
        ]
        
        return tools
    
    def _create_agent(self) -> AgentExecutor:
        """Create the agent executor"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            return_intermediate_steps=True,
            max_iterations=5
        )
    
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a property with full context
        
        Args:
            context: Property data and analysis parameters
        
        Returns:
            Comprehensive analysis results
        """
        
        property_data = context.get("property_data", {})
        
        # Prepare the analysis query
        query = f"""
        Analyze this Florida property for investment potential:
        
        Property Details:
        - Parcel ID: {property_data.get('parcel_id', 'Unknown')}
        - Address: {property_data.get('address', 'Unknown')}
        - Market Value: ${property_data.get('market_value', 0):,.2f}
        - Assessed Value: ${property_data.get('assessed_value', 0):,.2f}
        - Year Built: {property_data.get('year_built', 'Unknown')}
        - Square Footage: {property_data.get('building_sqft', 0)} sq ft
        - Lot Size: {property_data.get('lot_sqft', 0)} sq ft
        
        Tax Information:
        - Annual Tax: ${property_data.get('annual_tax', 0):,.2f}
        - Tax Liens: {len(property_data.get('tax_certificates', {}).get('certificates', []))} active
        - Total Lien Amount: ${property_data.get('tax_certificates', {}).get('total_amount', 0):,.2f}
        
        Provide a comprehensive investment analysis including:
        1. Investment score (0-100) with justification
        2. Key opportunities and risks
        3. Recommended strategy (flip, rent, hold)
        4. Estimated profit potential
        5. Action items for investor
        """
        
        # Run the analysis
        result = await self.agent.ainvoke({"input": query})
        
        # Extract and structure the response
        analysis = {
            "property_id": property_data.get('parcel_id'),
            "analysis_date": datetime.now().isoformat(),
            "investment_score": self._extract_score(result['output']),
            "recommendations": result['output'],
            "tools_used": [step[0].tool for step in result.get('intermediate_steps', [])],
            "confidence_level": "high" if len(result.get('intermediate_steps', [])) > 3 else "medium"
        }
        
        return analysis
    
    def _extract_score(self, text: str) -> int:
        """Extract investment score from analysis text"""
        import re
        
        # Look for patterns like "score: 85" or "85/100" or "85 out of 100"
        patterns = [
            r'score[:\s]+(\d+)',
            r'(\d+)/100',
            r'(\d+)\s+out\s+of\s+100'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return min(100, max(0, int(match.group(1))))
        
        return 50  # Default score if not found
    
    def _search_comparable_properties(self, criteria: str) -> str:
        """Search for comparable properties"""
        # In production, this would query the database
        return f"Found 5 comparable properties in the area with similar characteristics"
    
    def _calculate_roi(self, property_data: str) -> str:
        """Calculate ROI for a property"""
        try:
            data = json.loads(property_data) if isinstance(property_data, str) else property_data
            purchase_price = float(data.get('price', 0))
            rental_income = float(data.get('rental_income', 0))
            expenses = float(data.get('expenses', 0))
            
            if purchase_price > 0:
                annual_profit = (rental_income * 12) - expenses
                roi = (annual_profit / purchase_price) * 100
                return f"Estimated ROI: {roi:.2f}% annually"
            return "Insufficient data to calculate ROI"
        except:
            return "Error calculating ROI - please provide price, rental_income, and expenses"
    
    def _assess_renovation_cost(self, property_condition: str) -> str:
        """Estimate renovation costs"""
        # Simplified estimation logic
        condition_multipliers = {
            "excellent": 0,
            "good": 5000,
            "fair": 25000,
            "poor": 50000,
            "teardown": 100000
        }
        
        base_cost = condition_multipliers.get(property_condition.lower(), 30000)
        return f"Estimated renovation cost: ${base_cost:,.2f} based on {property_condition} condition"
    
    def _analyze_tax_liens(self, lien_data: str) -> str:
        """Analyze tax liens impact"""
        try:
            data = json.loads(lien_data) if isinstance(lien_data, str) else lien_data
            lien_amount = float(data.get('amount', 0))
            property_value = float(data.get('property_value', 1))
            
            lien_ratio = (lien_amount / property_value) * 100 if property_value > 0 else 0
            
            if lien_ratio > 20:
                return f"HIGH RISK: Tax liens represent {lien_ratio:.1f}% of property value"
            elif lien_ratio > 10:
                return f"MODERATE RISK: Tax liens represent {lien_ratio:.1f}% of property value"
            else:
                return f"LOW RISK: Tax liens represent {lien_ratio:.1f}% of property value"
        except:
            return "Unable to analyze tax liens - insufficient data"
    
    def _estimate_rental_income(self, property_details: str) -> str:
        """Estimate potential rental income"""
        # Simplified rental estimation
        # In production, this would use market data and comparables
        return "Estimated monthly rental income: $2,500-$3,000 based on local market rates"
    
    def _check_market_trends(self, location: str) -> str:
        """Check market trends for the area"""
        # In production, this would query real market data
        return f"Market trends for {location}: +3.5% YoY appreciation, 45 days average DOM, seller's market"


class InvestmentAdvisorAgent:
    """
    Agent specialized in providing investment advice and strategy
    """
    
    def __init__(self, llm, memory):
        self.llm = llm
        self.memory = memory
        
        self.system_prompt = """You are a seasoned real estate investment advisor for ConcordBroker.
        Your expertise includes:
        1. Portfolio strategy and diversification
        2. Risk management and mitigation
        3. Financing options and leverage strategies
        4. Tax optimization and 1031 exchanges
        5. Market timing and exit strategies
        6. Cash flow optimization
        
        Provide actionable investment advice tailored to the investor's goals and risk tolerance.
        Always consider the investor's complete portfolio and long-term objectives."""
        
        self.agent = self._create_agent()
    
    def _create_agent(self) -> LLMChain:
        """Create the investment advisor chain"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{query}")
        ])
        
        return LLMChain(
            llm=self.llm,
            prompt=prompt,
            memory=self.memory,
            verbose=True
        )
    
    async def advise(self, query: str, portfolio_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide investment advice based on query and portfolio context
        
        Args:
            query: Investment question or scenario
            portfolio_context: Current portfolio and investor profile
        
        Returns:
            Investment advice and recommendations
        """
        
        enhanced_query = f"""
        Investment Query: {query}
        
        Portfolio Context:
        - Total Portfolio Value: ${portfolio_context.get('total_value', 0):,.2f}
        - Number of Properties: {portfolio_context.get('property_count', 0)}
        - Risk Tolerance: {portfolio_context.get('risk_tolerance', 'moderate')}
        - Investment Horizon: {portfolio_context.get('horizon', '5-10 years')}
        - Available Capital: ${portfolio_context.get('available_capital', 0):,.2f}
        
        Provide specific, actionable investment advice.
        """
        
        response = await self.agent.apredict(query=enhanced_query)
        
        return {
            "advice": response,
            "timestamp": datetime.now().isoformat(),
            "context_considered": portfolio_context
        }


class DataResearchAgent:
    """
    Agent specialized in researching and gathering property-related data
    """
    
    def __init__(self, llm, vector_stores):
        self.llm = llm
        self.vector_stores = vector_stores
        offline = os.getenv("OFFLINE_MODE", "false").lower() == "true"
        self.search_tool = None if offline else DuckDuckGoSearchRun()
        
        self.system_prompt = """You are a meticulous data researcher for ConcordBroker.
        Your responsibilities include:
        1. Gathering property records and public data
        2. Researching owner information and business entities
        3. Finding building permits and code violations
        4. Discovering liens, judgments, and encumbrances
        5. Analyzing neighborhood demographics and trends
        6. Monitoring foreclosure and distressed property listings
        
        Always verify data from multiple sources and provide confidence levels for your findings."""
    
    async def research(self, research_query: str, research_type: str = "general") -> Dict[str, Any]:
        """
        Conduct research based on query and type
        
        Args:
            research_query: What to research
            research_type: Type of research (owner, property, market, legal)
        
        Returns:
            Research findings with sources
        """
        
        # Search web for information
        if self.search_tool is not None:
            web_results = self.search_tool.run(research_query)
        else:
            web_results = "[offline mode: web search disabled]"
        
        # Search internal vector stores
        internal_results = []
        for store_name, store in self.vector_stores.items():
            if research_type in store_name or research_type == "general":
                results = store.similarity_search(research_query, k=3)
                internal_results.extend(results)
        
        # Synthesize findings
        synthesis_prompt = f"""
        Research Query: {research_query}
        Research Type: {research_type}
        
        Web Results:
        {web_results}
        
        Internal Database Results:
        {[r.page_content for r in internal_results[:5]]}
        
        Provide a comprehensive research summary with:
        1. Key findings
        2. Data sources
        3. Confidence level
        4. Recommended next steps
        """
        
        synthesis = await self.llm.apredict(synthesis_prompt)
        
        return {
            "query": research_query,
            "type": research_type,
            "findings": synthesis,
            "web_sources": web_results[:500],  # Truncate for response size
            "internal_sources": len(internal_results),
            "timestamp": datetime.now().isoformat()
        }


class MarketAnalysisAgent:
    """
    Agent specialized in market analysis and trends
    """
    
    def __init__(self, llm, vector_store):
        self.llm = llm
        self.vector_store = vector_store
        
        self.system_prompt = """You are a market analysis expert for ConcordBroker.
        Analyze real estate markets with focus on:
        1. Price trends and appreciation rates
        2. Supply and demand dynamics
        3. Demographic shifts and migration patterns
        4. Economic indicators and job growth
        5. Development plans and infrastructure projects
        6. Competitive market positioning
        
        Provide data-driven market insights with specific metrics and projections."""
    
    async def analyze_market(self, location: str, timeframe: str = "current") -> Dict[str, Any]:
        """
        Analyze market conditions for a specific location
        
        Args:
            location: Geographic area to analyze
            timeframe: Analysis timeframe (current, 6months, 1year, 5year)
        
        Returns:
            Market analysis with trends and projections
        """
        
        # Query vector store for market data
        market_data = self.vector_store.similarity_search(
            f"market analysis {location} {timeframe}",
            k=5
        )
        
        analysis_prompt = f"""
        Analyze the real estate market for: {location}
        Timeframe: {timeframe}
        
        Available Data:
        {[doc.page_content for doc in market_data]}
        
        Provide analysis including:
        1. Current market conditions (buyer's/seller's market)
        2. Price trends and projections
        3. Inventory levels and days on market
        4. Key opportunities and risks
        5. Investment recommendations
        """
        
        analysis = await self.llm.apredict(analysis_prompt)
        
        return {
            "location": location,
            "timeframe": timeframe,
            "analysis": analysis,
            "data_points": len(market_data),
            "timestamp": datetime.now().isoformat()
        }


class LegalComplianceAgent:
    """
    Agent specialized in legal and compliance matters
    """
    
    def __init__(self, llm, vector_store):
        self.llm = llm
        self.vector_store = vector_store
        
        self.system_prompt = """You are a legal compliance expert for ConcordBroker.
        Your expertise covers:
        1. Property title and ownership issues
        2. Zoning and land use regulations
        3. Building codes and permit requirements
        4. Tax lien and foreclosure procedures
        5. Disclosure requirements and liability
        6. Contract review and negotiation points
        
        Always provide legally sound advice while recommending consultation with attorneys for specific matters.
        Never provide advice that could be construed as unauthorized practice of law."""
    
    async def check_compliance(self, property_data: Dict[str, Any], check_type: str = "general") -> Dict[str, Any]:
        """
        Check legal and compliance issues for a property
        
        Args:
            property_data: Property information
            check_type: Type of compliance check
        
        Returns:
            Compliance analysis with recommendations
        """
        
        # Search for relevant legal information
        legal_docs = self.vector_store.similarity_search(
            f"legal compliance {check_type} Florida real estate",
            k=5
        )
        
        compliance_prompt = f"""
        Review legal compliance for this property:
        
        Property Details:
        {json.dumps(property_data, indent=2)}
        
        Check Type: {check_type}
        
        Relevant Regulations:
        {[doc.page_content for doc in legal_docs]}
        
        Provide compliance analysis including:
        1. Potential legal issues identified
        2. Required disclosures
        3. Recommended due diligence steps
        4. Risk mitigation strategies
        5. When to consult legal counsel
        """
        
        analysis = await self.llm.apredict(compliance_prompt)
        
        return {
            "property_id": property_data.get("parcel_id"),
            "check_type": check_type,
            "compliance_analysis": analysis,
            "regulations_reviewed": len(legal_docs),
            "timestamp": datetime.now().isoformat(),
            "disclaimer": "This analysis is for informational purposes only and does not constitute legal advice."
        }

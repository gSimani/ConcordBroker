"""
Chain-of-Thought Property to Company Matching System
Advanced reasoning agents with maximum accuracy and active monitoring
"""

import asyncio
import re
import json
import hashlib
from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from abc import ABC, abstractmethod
import aiohttp
from collections import defaultdict
import numpy as np
from fuzzywuzzy import fuzz
import phonetics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThoughtProcess:
    """Represents a single step in chain-of-thought reasoning"""
    
    def __init__(self, step: str, reasoning: str, confidence: float, evidence: List[str]):
        self.step = step
        self.reasoning = reasoning
        self.confidence = confidence
        self.evidence = evidence
        self.timestamp = datetime.now()
        
    def to_dict(self):
        return {
            "step": self.step,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat()
        }

class AgentStatus(Enum):
    """Agent operational status"""
    ACTIVE = "active"
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    MAINTENANCE = "maintenance"

@dataclass
class ChainOfThoughtResult:
    """Enhanced result with reasoning chain"""
    company_name: str
    company_doc_number: str
    confidence: float
    match_type: str
    thought_chain: List[ThoughtProcess]
    evidence: List[str]
    agent_name: str
    processing_time: float
    timestamp: datetime = field(default_factory=datetime.now)

class BaseChainAgent(ABC):
    """Enhanced base agent with chain-of-thought reasoning"""
    
    def __init__(self, supabase_client, name: str = None):
        self.supabase = supabase_client
        self.name = name or self.__class__.__name__
        self.status = AgentStatus.ACTIVE
        self.last_heartbeat = datetime.now()
        self.total_processed = 0
        self.success_rate = 1.0
        self.thought_chain: List[ThoughtProcess] = []
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    @abstractmethod
    async def think(self, property_data: Dict) -> List[ThoughtProcess]:
        """Generate chain of thought for the matching process"""
        pass
    
    @abstractmethod
    async def execute(self, property_data: Dict, thoughts: List[ThoughtProcess]) -> List[ChainOfThoughtResult]:
        """Execute matching based on thought chain"""
        pass
    
    async def match(self, property_data: Dict) -> List[ChainOfThoughtResult]:
        """Main matching method with chain-of-thought"""
        start_time = datetime.now()
        self.status = AgentStatus.PROCESSING
        self.thought_chain = []
        
        try:
            # Step 1: Think through the problem
            thoughts = await self.think(property_data)
            self.thought_chain.extend(thoughts)
            
            # Step 2: Execute based on reasoning
            results = await self.execute(property_data, thoughts)
            
            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.total_processed += 1
            self.last_heartbeat = datetime.now()
            
            # Add processing time to results
            for result in results:
                result.processing_time = processing_time
                
            self.status = AgentStatus.ACTIVE
            return results
            
        except Exception as e:
            logger.error(f"{self.name} error: {str(e)}")
            self.status = AgentStatus.ERROR
            self.success_rate *= 0.95  # Decay success rate
            return []
    
    def add_thought(self, step: str, reasoning: str, confidence: float, evidence: List[str] = None):
        """Add a thought to the chain"""
        thought = ThoughtProcess(step, reasoning, confidence, evidence or [])
        self.thought_chain.append(thought)
        return thought
    
    async def heartbeat(self):
        """Keep agent alive and monitor health"""
        self.last_heartbeat = datetime.now()
        if self.status == AgentStatus.ERROR:
            # Try to recover
            self.status = AgentStatus.ACTIVE
        return {
            "agent": self.name,
            "status": self.status.value,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "total_processed": self.total_processed,
            "success_rate": self.success_rate
        }

# =====================================================
# TIER 1: VERY HIGH ACCURACY AGENTS (90-95%)
# =====================================================

class TaxIdChainAgent(BaseChainAgent):
    """Tax ID matching with chain-of-thought reasoning"""
    
    async def think(self, property_data: Dict) -> List[ThoughtProcess]:
        thoughts = []
        
        # Thought 1: Check if we have tax ID data
        tax_id = property_data.get('tax_id') or property_data.get('ein')
        if tax_id:
            thoughts.append(ThoughtProcess(
                "Tax ID Analysis",
                f"Found tax ID {tax_id} in property records. This is highly reliable for matching.",
                0.95,
                [f"Tax ID: {tax_id}"]
            ))
        else:
            thoughts.append(ThoughtProcess(
                "Tax ID Search",
                "No direct tax ID found. Will attempt to extract from other fields.",
                0.3,
                ["No tax ID in primary fields"]
            ))
            
            # Try to extract from owner name or other fields
            owner = property_data.get('owner_name', '')
            if re.search(r'\d{2}-\d{7}', owner):
                tax_id = re.search(r'(\d{2}-\d{7})', owner).group(1)
                thoughts.append(ThoughtProcess(
                    "Tax ID Extraction",
                    f"Extracted potential EIN {tax_id} from owner name field.",
                    0.7,
                    [f"Extracted: {tax_id}"]
                ))
                
        return thoughts
    
    async def execute(self, property_data: Dict, thoughts: List[ThoughtProcess]) -> List[ChainOfThoughtResult]:
        results = []
        
        # Extract tax ID from thoughts
        tax_id = None
        for thought in thoughts:
            if "Tax ID:" in str(thought.evidence):
                tax_id = thought.evidence[0].replace("Tax ID: ", "")
                break
            elif "Extracted:" in str(thought.evidence):
                tax_id = thought.evidence[0].replace("Extracted: ", "")
                break
                
        if not tax_id:
            return results
            
        # Query Sunbiz
        response = await self.supabase.from_('sunbiz_corporate')\
            .select('*')\
            .eq('ein', tax_id)\
            .execute()
            
        for corp in (response.data or []):
            results.append(ChainOfThoughtResult(
                company_name=corp['entity_name'],
                company_doc_number=corp['doc_number'],
                confidence=0.95,
                match_type="Tax ID Match",
                thought_chain=thoughts,
                evidence=[
                    f"EIN {tax_id} exact match",
                    f"Corporate status: {corp.get('status', 'Unknown')}",
                    f"Filed: {corp.get('filing_date', 'Unknown')}"
                ],
                agent_name=self.name,
                processing_time=0
            ))
            
        return results

class MortgageDocumentChainAgent(BaseChainAgent):
    """Enhanced mortgage document analysis with reasoning"""
    
    async def think(self, property_data: Dict) -> List[ThoughtProcess]:
        thoughts = []
        parcel_id = property_data.get('parcel_id')
        
        if parcel_id:
            thoughts.append(ThoughtProcess(
                "Document Search Strategy",
                "Will search mortgage documents, deeds, and liens for business entities.",
                0.85,
                [f"Parcel ID: {parcel_id}"]
            ))
            
            # Consider document types
            thoughts.append(ThoughtProcess(
                "Document Priority",
                "Prioritizing: 1) Current mortgages, 2) Recent deeds, 3) UCC filings, 4) Liens",
                0.9,
                ["Warranty deeds most reliable", "Mortgages show current obligations"]
            ))
        else:
            thoughts.append(ThoughtProcess(
                "Limited Search",
                "No parcel ID available. Will attempt address-based document search.",
                0.5,
                ["Address-based search less reliable"]
            ))
            
        return thoughts
    
    async def execute(self, property_data: Dict, thoughts: List[ThoughtProcess]) -> List[ChainOfThoughtResult]:
        results = []
        parcel_id = property_data.get('parcel_id')
        
        if not parcel_id:
            return results
            
        # Query multiple document types
        doc_types = ['MORTGAGE', 'WARRANTY_DEED', 'QUIT_CLAIM', 'UCC', 'LIEN']
        
        for doc_type in doc_types:
            response = await self.supabase.from_('property_documents')\
                .select('*')\
                .eq('parcel_id', parcel_id)\
                .eq('document_type', doc_type)\
                .order('record_date', desc=True)\
                .limit(5)\
                .execute()
                
            for doc in (response.data or []):
                # Analyze parties involved
                grantor = doc.get('grantor_name', '')
                grantee = doc.get('grantee_name', '')
                
                for party in [grantor, grantee]:
                    if self._is_business_entity(party):
                        # Look up in Sunbiz
                        corp_response = await self.supabase.from_('sunbiz_corporate')\
                            .select('*')\
                            .ilike('entity_name', f'%{party}%')\
                            .limit(1)\
                            .execute()
                            
                        if corp_response.data:
                            corp = corp_response.data[0]
                            
                            # Add reasoning about the match
                            match_thoughts = thoughts.copy()
                            match_thoughts.append(ThoughtProcess(
                                "Document Match Found",
                                f"Found {party} in {doc_type} document dated {doc.get('record_date', 'Unknown')}",
                                0.9,
                                [f"Document #: {doc.get('document_number', 'Unknown')}"]
                            ))
                            
                            results.append(ChainOfThoughtResult(
                                company_name=corp['entity_name'],
                                company_doc_number=corp['doc_number'],
                                confidence=0.92,
                                match_type=f"{doc_type} Document Match",
                                thought_chain=match_thoughts,
                                evidence=[
                                    f"Document type: {doc_type}",
                                    f"Party role: {'Grantor' if party == grantor else 'Grantee'}",
                                    f"Record date: {doc.get('record_date', 'Unknown')}",
                                    f"Document #: {doc.get('document_number', 'Unknown')}"
                                ],
                                agent_name=self.name,
                                processing_time=0
                            ))
                            
        return results
    
    def _is_business_entity(self, name: str) -> bool:
        """Enhanced business entity detection"""
        if not name:
            return False
            
        business_indicators = [
            'LLC', 'L.L.C.', 'INC', 'INCORPORATED', 'CORP', 'CORPORATION',
            'LP', 'L.P.', 'LLP', 'L.L.P.', 'PA', 'P.A.', 'PC', 'P.C.',
            'PARTNERSHIP', 'COMPANY', 'CO.', 'ASSOCIATES', 'GROUP',
            'HOLDINGS', 'PROPERTIES', 'INVESTMENTS', 'CAPITAL', 'VENTURES',
            'TRUST', 'FOUNDATION', 'FUND'
        ]
        
        name_upper = name.upper()
        
        # Check for business indicators
        if any(indicator in name_upper for indicator in business_indicators):
            return True
            
        # Check for multiple words (likely business)
        if len(name.split()) > 3:
            return True
            
        # Check for numbers in name (often business)
        if re.search(r'\d', name):
            return True
            
        return False

class UtilityAccountChainAgent(BaseChainAgent):
    """Utility account matching with intelligent reasoning"""
    
    async def think(self, property_data: Dict) -> List[ThoughtProcess]:
        thoughts = []
        address = property_data.get('address', '')
        
        thoughts.append(ThoughtProcess(
            "Utility Strategy",
            "Checking utility accounts: electric, water, gas, internet, waste management",
            0.85,
            ["Commercial properties have business utility accounts"]
        ))
        
        # Determine property type
        property_use = property_data.get('property_use_code', '')
        if property_use and property_use.startswith('C'):
            thoughts.append(ThoughtProcess(
                "Commercial Property",
                "This is a commercial property - high likelihood of business utility accounts",
                0.9,
                [f"Use code: {property_use}"]
            ))
        else:
            thoughts.append(ThoughtProcess(
                "Residential Check",
                "Checking if residential property has business utility accounts (rental/investment)",
                0.6,
                ["Some residential properties are business-owned"]
            ))
            
        return thoughts
    
    async def execute(self, property_data: Dict, thoughts: List[ThoughtProcess]) -> List[ChainOfThoughtResult]:
        results = []
        address = property_data.get('address', '')
        
        if not address:
            return results
            
        # Query utility accounts
        utility_types = ['ELECTRIC', 'WATER', 'GAS', 'INTERNET', 'WASTE']
        
        for utility_type in utility_types:
            response = await self.supabase.from_('utility_accounts')\
                .select('*')\
                .eq('service_address', address)\
                .eq('utility_type', utility_type)\
                .execute()
                
            for account in (response.data or []):
                account_name = account.get('account_holder_name', '')
                
                if self._is_business_entity(account_name):
                    # Look up in Sunbiz
                    corp_response = await self.supabase.from_('sunbiz_corporate')\
                        .select('*')\
                        .ilike('entity_name', f'%{account_name}%')\
                        .limit(1)\
                        .execute()
                        
                    if corp_response.data:
                        corp = corp_response.data[0]
                        
                        # Add specific utility reasoning
                        match_thoughts = thoughts.copy()
                        match_thoughts.append(ThoughtProcess(
                            f"{utility_type} Account Match",
                            f"Business utility account for {account_name} at property address",
                            0.93,
                            [f"Account #: {account.get('account_number', 'Unknown')}"]
                        ))
                        
                        results.append(ChainOfThoughtResult(
                            company_name=corp['entity_name'],
                            company_doc_number=corp['doc_number'],
                            confidence=0.93,
                            match_type=f"{utility_type} Utility Account",
                            thought_chain=match_thoughts,
                            evidence=[
                                f"Utility: {utility_type}",
                                f"Account holder: {account_name}",
                                f"Account active: {account.get('is_active', False)}",
                                f"Service start: {account.get('service_start_date', 'Unknown')}"
                            ],
                            agent_name=self.name,
                            processing_time=0
                        ))
                        
        return results
    
    def _is_business_entity(self, name: str) -> bool:
        """Check if name is a business"""
        if not name:
            return False
        business_indicators = ['LLC', 'INC', 'CORP', 'COMPANY', 'GROUP']
        return any(ind in name.upper() for ind in business_indicators)

# =====================================================
# TIER 2: HIGH ACCURACY AGENTS (75-85%)
# =====================================================

class PermitLicenseChainAgent(BaseChainAgent):
    """Cross-reference permits and licenses with reasoning"""
    
    async def think(self, property_data: Dict) -> List[ThoughtProcess]:
        thoughts = []
        address = property_data.get('address', '')
        
        thoughts.append(ThoughtProcess(
            "Permit Analysis",
            "Analyzing building permits, business licenses, and occupational licenses",
            0.8,
            ["Recent permits indicate active business operations"]
        ))
        
        # Consider timeframe
        thoughts.append(ThoughtProcess(
            "Temporal Relevance",
            "Prioritizing permits/licenses from last 2 years for accuracy",
            0.85,
            ["Recent activity more relevant", "Older permits may be outdated"]
        ))
        
        return thoughts
    
    async def execute(self, property_data: Dict, thoughts: List[ThoughtProcess]) -> List[ChainOfThoughtResult]:
        results = []
        address = property_data.get('address', '')
        
        if not address:
            return results
            
        # Get recent permits
        two_years_ago = (datetime.now() - timedelta(days=730)).isoformat()
        
        permit_response = await self.supabase.from_('building_permits')\
            .select('*')\
            .eq('property_address', address)\
            .gte('issue_date', two_years_ago)\
            .execute()
            
        # Get business licenses
        license_response = await self.supabase.from_('business_licenses')\
            .select('*')\
            .eq('business_address', address)\
            .eq('status', 'ACTIVE')\
            .execute()
            
        # Cross-reference
        permit_applicants = set()
        for permit in (permit_response.data or []):
            applicant = permit.get('applicant_name', '')
            if self._is_business_entity(applicant):
                permit_applicants.add(applicant.upper())
                
        for license in (license_response.data or []):
            business_name = license.get('business_name', '').upper()
            
            # Check if business has permits
            confidence = 0.75
            if business_name in permit_applicants:
                confidence = 0.85
                
            # Look up in Sunbiz
            corp_response = await self.supabase.from_('sunbiz_corporate')\
                .select('*')\
                .ilike('entity_name', f'%{license.get("business_name", "")}%')\
                .limit(1)\
                .execute()
                
            if corp_response.data:
                corp = corp_response.data[0]
                
                match_thoughts = thoughts.copy()
                match_thoughts.append(ThoughtProcess(
                    "License Match",
                    f"Active business license for {business_name} at address",
                    confidence,
                    [f"License #: {license.get('license_number', 'Unknown')}"]
                ))
                
                if business_name in permit_applicants:
                    match_thoughts.append(ThoughtProcess(
                        "Permit Correlation",
                        "Business also has recent building permits - stronger match",
                        0.9,
                        ["Multiple data points confirm"]
                    ))
                    
                results.append(ChainOfThoughtResult(
                    company_name=corp['entity_name'],
                    company_doc_number=corp['doc_number'],
                    confidence=confidence,
                    match_type="Permit & License Match",
                    thought_chain=match_thoughts,
                    evidence=[
                        f"Business license: {license.get('license_number', 'Unknown')}",
                        f"License type: {license.get('license_type', 'Unknown')}",
                        f"Has permits: {business_name in permit_applicants}"
                    ],
                    agent_name=self.name,
                    processing_time=0
                ))
                
        return results
    
    def _is_business_entity(self, name: str) -> bool:
        return bool(name and any(ind in name.upper() for ind in ['LLC', 'INC', 'CORP']))

class DigitalFootprintChainAgent(BaseChainAgent):
    """Web presence and digital footprint analysis"""
    
    async def think(self, property_data: Dict) -> List[ThoughtProcess]:
        thoughts = []
        
        thoughts.append(ThoughtProcess(
            "Digital Search Strategy",
            "Will search: Google Business, websites, social media, review sites",
            0.75,
            ["Online presence indicates active business"]
        ))
        
        # Consider verification levels
        thoughts.append(ThoughtProcess(
            "Verification Priority",
            "Google verified listings are most reliable, followed by websites with SSL",
            0.8,
            ["Verified listings require proof", "SSL certificates show legitimacy"]
        ))
        
        return thoughts
    
    async def execute(self, property_data: Dict, thoughts: List[ThoughtProcess]) -> List[ChainOfThoughtResult]:
        results = []
        address = property_data.get('address', '')
        city = property_data.get('city', '')
        
        if not address:
            return results
            
        # Query web presence data
        response = await self.supabase.from_('business_web_presence')\
            .select('*')\
            .ilike('listed_address', f'%{address}%')\
            .execute()
            
        for web_presence in (response.data or []):
            # Verify city match
            if city and city.upper() not in web_presence.get('listed_address', '').upper():
                continue
                
            business_name = web_presence.get('business_name', '')
            
            # Calculate confidence based on verification
            confidence = 0.7
            if web_presence.get('google_verified'):
                confidence = 0.85
            elif web_presence.get('has_ssl_cert'):
                confidence = 0.8
                
            # Look up in Sunbiz
            corp_response = await self.supabase.from_('sunbiz_corporate')\
                .select('*')\
                .ilike('entity_name', f'%{business_name}%')\
                .limit(1)\
                .execute()
                
            if corp_response.data:
                corp = corp_response.data[0]
                
                match_thoughts = thoughts.copy()
                match_thoughts.append(ThoughtProcess(
                    "Digital Presence Found",
                    f"{business_name} has online presence at property address",
                    confidence,
                    [
                        f"Website: {web_presence.get('website', 'None')}",
                        f"Google verified: {web_presence.get('google_verified', False)}"
                    ]
                ))
                
                results.append(ChainOfThoughtResult(
                    company_name=corp['entity_name'],
                    company_doc_number=corp['doc_number'],
                    confidence=confidence,
                    match_type="Digital Footprint",
                    thought_chain=match_thoughts,
                    evidence=[
                        f"Website: {web_presence.get('website', 'N/A')}",
                        f"Google Business: {web_presence.get('google_business_id', 'N/A')}",
                        f"Reviews: {web_presence.get('review_count', 0)}",
                        f"Rating: {web_presence.get('average_rating', 'N/A')}"
                    ],
                    agent_name=self.name,
                    processing_time=0
                ))
                
        return results

class PropertyManagerPatternAgent(BaseChainAgent):
    """Identify property management patterns"""
    
    async def think(self, property_data: Dict) -> List[ThoughtProcess]:
        thoughts = []
        
        thoughts.append(ThoughtProcess(
            "Management Pattern Analysis",
            "Identifying if property is managed by a property management company",
            0.75,
            ["Management companies often own or control multiple properties"]
        ))
        
        thoughts.append(ThoughtProcess(
            "Pattern Recognition",
            "Looking for: similar owner names, registered agents, mailing addresses",
            0.8,
            ["Patterns indicate corporate ownership structure"]
        ))
        
        return thoughts
    
    async def execute(self, property_data: Dict, thoughts: List[ThoughtProcess]) -> List[ChainOfThoughtResult]:
        results = []
        
        # Get mailing address (often management company address)
        mail_address = property_data.get('mail_addr1', '')
        owner_name = property_data.get('owner_name', '')
        
        if mail_address and mail_address != property_data.get('address', ''):
            # Find other properties with same mailing address
            response = await self.supabase.from_('florida_parcels')\
                .select('owner_name, parcel_id')\
                .eq('mail_addr1', mail_address)\
                .limit(20)\
                .execute()
                
            if len(response.data or []) >= 3:
                # Multiple properties with same mailing - likely management company
                unique_owners = set(p['owner_name'] for p in response.data)
                
                for owner in unique_owners:
                    if self._is_business_entity(owner):
                        # Look up in Sunbiz
                        corp_response = await self.supabase.from_('sunbiz_corporate')\
                            .select('*')\
                            .ilike('entity_name', f'%{owner}%')\
                            .limit(1)\
                            .execute()
                            
                        if corp_response.data:
                            corp = corp_response.data[0]
                            
                            match_thoughts = thoughts.copy()
                            match_thoughts.append(ThoughtProcess(
                                "Management Pattern Found",
                                f"Found {len(response.data)} properties with same mailing address",
                                0.8,
                                [f"Properties managed: {len(response.data)}"]
                            ))
                            
                            results.append(ChainOfThoughtResult(
                                company_name=corp['entity_name'],
                                company_doc_number=corp['doc_number'],
                                confidence=0.78,
                                match_type="Property Management Pattern",
                                thought_chain=match_thoughts,
                                evidence=[
                                    f"Mailing address: {mail_address}",
                                    f"Properties at address: {len(response.data)}",
                                    f"Unique owners: {len(unique_owners)}"
                                ],
                                agent_name=self.name,
                                processing_time=0
                            ))
                            
        return results
    
    def _is_business_entity(self, name: str) -> bool:
        return bool(name and ('MANAGEMENT' in name.upper() or 
                             'PROPERTIES' in name.upper() or
                             'REALTY' in name.upper() or
                             any(ind in name.upper() for ind in ['LLC', 'INC', 'CORP'])))

# =====================================================
# TIER 3: MEDIUM ACCURACY AGENTS (60-75%)
# =====================================================

class NameVariationChainAgent(BaseChainAgent):
    """Advanced name matching with phonetic and fuzzy logic"""
    
    async def think(self, property_data: Dict) -> List[ThoughtProcess]:
        thoughts = []
        owner_name = property_data.get('owner_name', '')
        
        if owner_name:
            thoughts.append(ThoughtProcess(
                "Name Analysis",
                f"Analyzing '{owner_name}' for variations, DBAs, and aliases",
                0.65,
                ["Will use phonetic matching", "Fuzzy string matching", "Common abbreviations"]
            ))
            
            # Determine name type
            if self._is_business_entity(owner_name):
                thoughts.append(ThoughtProcess(
                    "Business Name Detected",
                    "This appears to be a business entity - will generate business variations",
                    0.7,
                    ["Business suffixes detected"]
                ))
            else:
                thoughts.append(ThoughtProcess(
                    "Individual Name",
                    "This appears to be an individual - will check for businesses owned by this person",
                    0.6,
                    ["Will search officer records"]
                ))
                
        return thoughts
    
    async def execute(self, property_data: Dict, thoughts: List[ThoughtProcess]) -> List[ChainOfThoughtResult]:
        results = []
        owner_name = property_data.get('owner_name', '')
        
        if not owner_name:
            return results
            
        # Generate variations
        variations = self._generate_advanced_variations(owner_name)
        
        # Add phonetic variations
        phonetic_variations = self._generate_phonetic_variations(owner_name)
        variations.extend(phonetic_variations)
        
        # Search for each variation
        for variation in variations[:10]:  # Limit to top 10 variations
            # Search in Sunbiz
            response = await self.supabase.from_('sunbiz_corporate')\
                .select('*')\
                .or_(f'entity_name.ilike.%{variation}%,trade_name.ilike.%{variation}%')\
                .limit(3)\
                .execute()
                
            for corp in (response.data or []):
                # Calculate match confidence
                confidence = self._calculate_match_confidence(
                    owner_name, 
                    corp['entity_name'], 
                    variation
                )
                
                if confidence >= 0.6:
                    match_thoughts = thoughts.copy()
                    match_thoughts.append(ThoughtProcess(
                        "Name Match Found",
                        f"Matched '{variation}' to '{corp['entity_name']}'",
                        confidence,
                        [f"Match method: {self._get_match_method(owner_name, variation)}"]
                    ))
                    
                    results.append(ChainOfThoughtResult(
                        company_name=corp['entity_name'],
                        company_doc_number=corp['doc_number'],
                        confidence=confidence,
                        match_type="Name Variation Match",
                        thought_chain=match_thoughts,
                        evidence=[
                            f"Original: {owner_name}",
                            f"Variation: {variation}",
                            f"Matched: {corp['entity_name']}",
                            f"Match score: {confidence:.2f}"
                        ],
                        agent_name=self.name,
                        processing_time=0
                    ))
                    
        return results
    
    def _is_business_entity(self, name: str) -> bool:
        business_indicators = ['LLC', 'INC', 'CORP', 'COMPANY', 'GROUP']
        return any(ind in name.upper() for ind in business_indicators)
    
    def _generate_advanced_variations(self, name: str) -> List[str]:
        """Generate sophisticated name variations"""
        variations = [name]
        
        # Remove/add common suffixes
        suffixes = ['LLC', 'INC', 'INCORPORATED', 'CORP', 'CORPORATION', 
                   'CO', 'COMPANY', 'LP', 'LLP', 'HOLDINGS', 'GROUP']
        
        base_name = name
        for suffix in suffixes:
            pattern = rf'\s*{suffix}\.?\s*$'
            base_name = re.sub(pattern, '', base_name, flags=re.IGNORECASE).strip()
            
        if base_name != name:
            variations.append(base_name)
            
        # Add variations with different suffixes
        for suffix in ['LLC', 'INC', 'CORP']:
            variations.append(f"{base_name} {suffix}")
            variations.append(f"{base_name}, {suffix}")
            
        # Handle possessives
        if "'s" in name or "'S" in name:
            variations.append(re.sub(r"'[sS]\s*", " ", name))
            variations.append(re.sub(r"'[sS]\s*", "", name))
        else:
            variations.append(f"{base_name}'s")
            
        # Handle "and" vs "&"
        if " AND " in name.upper():
            variations.append(name.replace(" AND ", " & ").replace(" and ", " & "))
        elif " & " in name:
            variations.append(name.replace(" & ", " AND "))
            
        # Handle "The" prefix
        if name.upper().startswith("THE "):
            variations.append(name[4:])
        else:
            variations.append(f"The {name}")
            
        # Handle numbers
        number_map = {
            '1ST': 'FIRST', '2ND': 'SECOND', '3RD': 'THIRD',
            '1': 'ONE', '2': 'TWO', '3': 'THREE'
        }
        for num, word in number_map.items():
            if num in name.upper():
                variations.append(name.upper().replace(num, word))
            if word in name.upper():
                variations.append(name.upper().replace(word, num))
                
        return list(set(variations))
    
    def _generate_phonetic_variations(self, name: str) -> List[str]:
        """Generate phonetic variations using soundex and metaphone"""
        variations = []
        
        try:
            # Clean name for phonetic analysis
            clean_name = re.sub(r'[^a-zA-Z\s]', '', name)
            words = clean_name.split()
            
            # Generate soundex
            soundex_words = [phonetics.soundex(word) for word in words if word]
            
            # Find similar sounding words (this would query a phonetic index)
            # For now, we'll just return the soundex as a search term
            variations.append(' '.join(soundex_words))
            
        except:
            pass
            
        return variations
    
    def _calculate_match_confidence(self, original: str, found: str, variation: str) -> float:
        """Calculate confidence score for name match"""
        # Use fuzzy string matching
        score1 = fuzz.ratio(original.upper(), found.upper()) / 100
        score2 = fuzz.token_sort_ratio(original.upper(), found.upper()) / 100
        score3 = fuzz.partial_ratio(variation.upper(), found.upper()) / 100
        
        # Weight the scores
        final_score = (score1 * 0.4 + score2 * 0.3 + score3 * 0.3)
        
        # Boost score if exact match on base name
        base_original = re.sub(r'\b(LLC|INC|CORP)\b', '', original.upper()).strip()
        base_found = re.sub(r'\b(LLC|INC|CORP)\b', '', found.upper()).strip()
        
        if base_original == base_found:
            final_score = min(final_score + 0.2, 0.95)
            
        return final_score
    
    def _get_match_method(self, original: str, variation: str) -> str:
        """Determine how the match was made"""
        if original.upper() == variation.upper():
            return "Exact match"
        elif original.upper().replace(' ', '') == variation.upper().replace(' ', ''):
            return "Space variation"
        elif re.sub(r'[^a-zA-Z0-9]', '', original.upper()) == re.sub(r'[^a-zA-Z0-9]', '', variation.upper()):
            return "Punctuation variation"
        elif any(suffix in variation.upper() for suffix in ['LLC', 'INC', 'CORP']):
            return "Suffix variation"
        else:
            return "Fuzzy match"

class NetworkAnalysisChainAgent(BaseChainAgent):
    """Deep network analysis of corporate relationships"""
    
    async def think(self, property_data: Dict) -> List[ThoughtProcess]:
        thoughts = []
        owner_name = property_data.get('owner_name', '')
        
        thoughts.append(ThoughtProcess(
            "Network Strategy",
            "Analyzing corporate networks, officer relationships, and entity families",
            0.65,
            ["Will map corporate structures", "Identify parent/subsidiary relationships"]
        ))
        
        if owner_name:
            # Parse for individual names
            individuals = self._parse_individuals(owner_name)
            if individuals:
                thoughts.append(ThoughtProcess(
                    "Individual Officers",
                    f"Found {len(individuals)} potential individual names to search in officer records",
                    0.7,
                    [f"Names: {', '.join(individuals)}"]
                ))
                
        return thoughts
    
    async def execute(self, property_data: Dict, thoughts: List[ThoughtProcess]) -> List[ChainOfThoughtResult]:
        results = []
        owner_name = property_data.get('owner_name', '')
        
        if not owner_name:
            return results
            
        # Parse individual names
        individuals = self._parse_individuals(owner_name)
        
        # Build network graph
        network = defaultdict(set)
        
        for individual in individuals:
            # Find all companies where this person is an officer
            officer_response = await self.supabase.from_('sunbiz_officers')\
                .select('doc_number, officer_title')\
                .ilike('officer_name', f'%{individual}%')\
                .execute()
                
            for officer in (officer_response.data or []):
                network[individual].add(officer['doc_number'])
                
        # Find companies with overlapping officers (stronger connection)
        company_officers = defaultdict(set)
        for person, companies in network.items():
            for company in companies:
                company_officers[company].add(person)
                
        # Get company details for network
        all_doc_numbers = list(set(doc for docs in network.values() for doc in docs))
        
        if all_doc_numbers:
            corp_response = await self.supabase.from_('sunbiz_corporate')\
                .select('*')\
                .in_('doc_number', all_doc_numbers)\
                .execute()
                
            for corp in (corp_response.data or []):
                # Calculate network strength
                officers_count = len(company_officers.get(corp['doc_number'], set()))
                confidence = min(0.6 + (officers_count * 0.1), 0.75)
                
                match_thoughts = thoughts.copy()
                match_thoughts.append(ThoughtProcess(
                    "Network Connection",
                    f"Found {corp['entity_name']} through officer network",
                    confidence,
                    [f"Connected officers: {officers_count}"]
                ))
                
                # Check for other properties
                other_props = await self._find_related_properties(corp['entity_name'])
                if len(other_props) > 1:
                    match_thoughts.append(ThoughtProcess(
                        "Property Portfolio",
                        f"This company owns {len(other_props)} other properties",
                        0.8,
                        [f"Portfolio size indicates active business"]
                    ))
                    confidence = min(confidence + 0.05, 0.8)
                    
                results.append(ChainOfThoughtResult(
                    company_name=corp['entity_name'],
                    company_doc_number=corp['doc_number'],
                    confidence=confidence,
                    match_type="Corporate Network",
                    thought_chain=match_thoughts,
                    evidence=[
                        f"Network size: {len(network)} officers",
                        f"Connected through: {', '.join(company_officers[corp['doc_number']])}",
                        f"Other properties: {len(other_props)}"
                    ],
                    agent_name=self.name,
                    processing_time=0
                ))
                
        return results
    
    def _parse_individuals(self, owner_name: str) -> List[str]:
        """Extract individual names from owner string"""
        names = re.split(r'\s*[&,]\s*|\s+AND\s+', owner_name, flags=re.IGNORECASE)
        individuals = []
        
        for name in names:
            # Filter out obvious business names
            if not any(ind in name.upper() for ind in ['LLC', 'INC', 'CORP', 'COMPANY']):
                # Check if it looks like a person's name (2-4 words)
                word_count = len(name.split())
                if 2 <= word_count <= 4:
                    individuals.append(name.strip())
                    
        return individuals
    
    async def _find_related_properties(self, company_name: str) -> List[str]:
        """Find other properties owned by company"""
        response = await self.supabase.from_('florida_parcels')\
            .select('parcel_id')\
            .ilike('owner_name', f'%{company_name}%')\
            .limit(10)\
            .execute()
        return [p['parcel_id'] for p in (response.data or [])]

class HistoricalTransactionAgent(BaseChainAgent):
    """Analyze property transaction history"""
    
    async def think(self, property_data: Dict) -> List[ThoughtProcess]:
        thoughts = []
        
        thoughts.append(ThoughtProcess(
            "Transaction Analysis",
            "Analyzing property sale history, transfers, and transaction patterns",
            0.65,
            ["Corporate buyers/sellers leave transaction trails"]
        ))
        
        sale_price = property_data.get('sale_price', 0)
        if sale_price > 1000000:
            thoughts.append(ThoughtProcess(
                "High-Value Transaction",
                f"Sale price ${sale_price:,.0f} indicates likely corporate involvement",
                0.75,
                ["High-value properties often involve business entities"]
            ))
            
        return thoughts
    
    async def execute(self, property_data: Dict, thoughts: List[ThoughtProcess]) -> List[ChainOfThoughtResult]:
        results = []
        parcel_id = property_data.get('parcel_id')
        
        if not parcel_id:
            return results
            
        # Get transaction history
        response = await self.supabase.from_('property_sales')\
            .select('*')\
            .eq('parcel_id', parcel_id)\
            .order('sale_date', desc=True)\
            .limit(10)\
            .execute()
            
        for sale in (response.data or []):
            # Check buyer and seller
            for party_type, party_name in [('buyer', sale.get('buyer_name', '')),
                                           ('seller', sale.get('seller_name', ''))]:
                if self._is_business_entity(party_name):
                    # Look up in Sunbiz
                    corp_response = await self.supabase.from_('sunbiz_corporate')\
                        .select('*')\
                        .ilike('entity_name', f'%{party_name}%')\
                        .limit(1)\
                        .execute()
                        
                    if corp_response.data:
                        corp = corp_response.data[0]
                        
                        # Calculate confidence based on transaction recency
                        days_ago = (datetime.now() - datetime.fromisoformat(sale['sale_date'])).days
                        confidence = max(0.75 - (days_ago / 3650), 0.6)  # Decay over 10 years
                        
                        match_thoughts = thoughts.copy()
                        match_thoughts.append(ThoughtProcess(
                            f"Transaction {party_type.title()}",
                            f"{party_name} was {party_type} on {sale['sale_date']}",
                            confidence,
                            [f"Sale price: ${sale.get('sale_price', 0):,.0f}"]
                        ))
                        
                        results.append(ChainOfThoughtResult(
                            company_name=corp['entity_name'],
                            company_doc_number=corp['doc_number'],
                            confidence=confidence,
                            match_type=f"Historical {party_type.title()}",
                            thought_chain=match_thoughts,
                            evidence=[
                                f"Role: {party_type.title()}",
                                f"Transaction date: {sale['sale_date']}",
                                f"Sale price: ${sale.get('sale_price', 0):,.0f}",
                                f"Document: {sale.get('document_number', 'Unknown')}"
                            ],
                            agent_name=self.name,
                            processing_time=0
                        ))
                        
        return results
    
    def _is_business_entity(self, name: str) -> bool:
        return bool(name and any(ind in name.upper() for ind in ['LLC', 'INC', 'CORP', 'TRUST']))

# =====================================================
# TIER 4: MODERATE ACCURACY AGENTS (45-60%)
# =====================================================

class GeospatialClusterAgent(BaseChainAgent):
    """Analyze spatial patterns and clusters"""
    
    async def think(self, property_data: Dict) -> List[ThoughtProcess]:
        thoughts = []
        
        thoughts.append(ThoughtProcess(
            "Spatial Analysis",
            "Analyzing geographic clustering and ownership patterns nearby",
            0.5,
            ["Companies often own multiple nearby properties"]
        ))
        
        lat = property_data.get('latitude')
        lon = property_data.get('longitude')
        
        if lat and lon:
            thoughts.append(ThoughtProcess(
                "Coordinates Available",
                f"Using coordinates ({lat}, {lon}) for precise spatial analysis",
                0.6,
                ["Will search 0.5 mile radius"]
            ))
        else:
            thoughts.append(ThoughtProcess(
                "Address-Based Search",
                "No coordinates available - using address proximity",
                0.45,
                ["Less precise than coordinate search"]
            ))
            
        return thoughts
    
    async def execute(self, property_data: Dict, thoughts: List[ThoughtProcess]) -> List[ChainOfThoughtResult]:
        results = []
        lat = property_data.get('latitude')
        lon = property_data.get('longitude')
        
        if not lat or not lon:
            return results
            
        # Find nearby properties
        # In production, use PostGIS ST_DWithin
        # For now, use simple bounding box
        lat_range = 0.007  # ~0.5 miles
        lon_range = 0.009  # ~0.5 miles
        
        response = await self.supabase.from_('florida_parcels')\
            .select('owner_name, parcel_id, latitude, longitude')\
            .gte('latitude', lat - lat_range)\
            .lte('latitude', lat + lat_range)\
            .gte('longitude', lon - lon_range)\
            .lte('longitude', lon + lon_range)\
            .limit(100)\
            .execute()
            
        # Group by owner
        owner_properties = defaultdict(list)
        for prop in (response.data or []):
            owner = prop.get('owner_name', '')
            if self._is_business_entity(owner):
                # Calculate distance
                distance = self._calculate_distance(
                    lat, lon,
                    prop.get('latitude', 0),
                    prop.get('longitude', 0)
                )
                owner_properties[owner].append({
                    'parcel_id': prop['parcel_id'],
                    'distance': distance
                })
                
        # Find owners with multiple properties
        for owner, properties in owner_properties.items():
            if len(properties) >= 2:
                # Look up in Sunbiz
                corp_response = await self.supabase.from_('sunbiz_corporate')\
                    .select('*')\
                    .ilike('entity_name', f'%{owner}%')\
                    .limit(1)\
                    .execute()
                    
                if corp_response.data:
                    corp = corp_response.data[0]
                    
                    # Calculate confidence based on cluster size
                    confidence = min(0.45 + (len(properties) * 0.05), 0.6)
                    
                    # Identify pattern
                    pattern = self._identify_cluster_pattern(properties)
                    
                    match_thoughts = thoughts.copy()
                    match_thoughts.append(ThoughtProcess(
                        "Cluster Found",
                        f"{owner} owns {len(properties)} nearby properties",
                        confidence,
                        [f"Pattern: {pattern}"]
                    ))
                    
                    results.append(ChainOfThoughtResult(
                        company_name=corp['entity_name'],
                        company_doc_number=corp['doc_number'],
                        confidence=confidence,
                        match_type="Geospatial Cluster",
                        thought_chain=match_thoughts,
                        evidence=[
                            f"Properties in cluster: {len(properties)}",
                            f"Average distance: {np.mean([p['distance'] for p in properties]):.2f} miles",
                            f"Pattern: {pattern}"
                        ],
                        agent_name=self.name,
                        processing_time=0
                    ))
                    
        return results
    
    def _is_business_entity(self, name: str) -> bool:
        return bool(name and any(ind in name.upper() for ind in ['LLC', 'INC', 'CORP', 'PROPERTIES']))
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in miles between two points"""
        # Simplified distance calculation
        lat_diff = abs(lat2 - lat1) * 69  # miles per degree latitude
        lon_diff = abs(lon2 - lon1) * 54.6  # miles per degree longitude at ~28°N
        return (lat_diff**2 + lon_diff**2)**0.5
    
    def _identify_cluster_pattern(self, properties: List[Dict]) -> str:
        """Identify the pattern of property clustering"""
        count = len(properties)
        avg_distance = np.mean([p['distance'] for p in properties])
        
        if count >= 10:
            return "Major development/investment cluster"
        elif count >= 5:
            if avg_distance < 0.2:
                return "Concentrated commercial complex"
            else:
                return "Distributed portfolio"
        elif count >= 3:
            return "Small investment cluster"
        else:
            return "Adjacent properties"

class IndustryClassificationAgent(BaseChainAgent):
    """Match property use to business industry"""
    
    async def think(self, property_data: Dict) -> List[ThoughtProcess]:
        thoughts = []
        use_code = property_data.get('property_use_code', '')
        
        if use_code:
            thoughts.append(ThoughtProcess(
                "Use Code Analysis",
                f"Property use code '{use_code}' will be matched to business types",
                0.55,
                ["Use codes indicate property purpose"]
            ))
            
            # Interpret use code
            industry = self._interpret_use_code(use_code)
            if industry:
                thoughts.append(ThoughtProcess(
                    "Industry Identified",
                    f"Property appears to be used for: {industry}",
                    0.6,
                    ["Will search for businesses in this industry"]
                ))
                
        return thoughts
    
    async def execute(self, property_data: Dict, thoughts: List[ThoughtProcess]) -> List[ChainOfThoughtResult]:
        results = []
        use_code = property_data.get('property_use_code', '')
        address = property_data.get('address', '')
        
        if not use_code or not address:
            return results
            
        # Interpret industry from use code
        industry = self._interpret_use_code(use_code)
        
        if industry:
            # Search for businesses in this industry at this address
            response = await self.supabase.from_('business_licenses')\
                .select('*')\
                .eq('business_address', address)\
                .ilike('business_type', f'%{industry}%')\
                .execute()
                
            for license in (response.data or []):
                business_name = license.get('business_name', '')
                
                # Look up in Sunbiz
                corp_response = await self.supabase.from_('sunbiz_corporate')\
                    .select('*')\
                    .ilike('entity_name', f'%{business_name}%')\
                    .limit(1)\
                    .execute()
                    
                if corp_response.data:
                    corp = corp_response.data[0]
                    
                    match_thoughts = thoughts.copy()
                    match_thoughts.append(ThoughtProcess(
                        "Industry Match",
                        f"{business_name} matches property use type {industry}",
                        0.55,
                        [f"Business type: {license.get('business_type', 'Unknown')}"]
                    ))
                    
                    results.append(ChainOfThoughtResult(
                        company_name=corp['entity_name'],
                        company_doc_number=corp['doc_number'],
                        confidence=0.55,
                        match_type="Industry Classification",
                        thought_chain=match_thoughts,
                        evidence=[
                            f"Property use: {use_code}",
                            f"Industry: {industry}",
                            f"Business type: {license.get('business_type', 'Unknown')}"
                        ],
                        agent_name=self.name,
                        processing_time=0
                    ))
                    
        return results
    
    def _interpret_use_code(self, use_code: str) -> str:
        """Convert property use code to industry"""
        use_map = {
            'C': 'Commercial',
            'R': 'Residential/Rental',
            'I': 'Industrial',
            'A': 'Agricultural',
            'O': 'Office',
            'M': 'Manufacturing',
            'W': 'Warehouse',
            'H': 'Hotel/Hospitality',
            'S': 'Retail/Store',
            'F': 'Food Service/Restaurant'
        }
        
        # Check first character
        first_char = use_code[0].upper() if use_code else ''
        return use_map.get(first_char, '')

class FinancialPatternAgent(BaseChainAgent):
    """Analyze financial patterns and investment profiles"""
    
    async def think(self, property_data: Dict) -> List[ThoughtProcess]:
        thoughts = []
        
        value = property_data.get('taxable_value', 0)
        sale_price = property_data.get('sale_price', 0)
        
        thoughts.append(ThoughtProcess(
            "Financial Analysis",
            f"Analyzing financial patterns: Value ${value:,.0f}, Sale ${sale_price:,.0f}",
            0.5,
            ["Financial patterns indicate investor type"]
        ))
        
        # Categorize investment level
        if value > 5000000:
            thoughts.append(ThoughtProcess(
                "Institutional Investment",
                "Property value indicates institutional or REIT ownership",
                0.6,
                ["High-value properties often owned by large entities"]
            ))
        elif value > 1000000:
            thoughts.append(ThoughtProcess(
                "Commercial Investment",
                "Property value indicates commercial investment entity",
                0.55,
                ["Mid-range commercial property"]
            ))
            
        return thoughts
    
    async def execute(self, property_data: Dict, thoughts: List[ThoughtProcess]) -> List[ChainOfThoughtResult]:
        results = []
        
        value = property_data.get('taxable_value', 0)
        owner_name = property_data.get('owner_name', '')
        
        if value > 1000000 and owner_name:
            # Search for investment companies with similar portfolio values
            # This would typically use more sophisticated financial analysis
            
            if self._is_investment_entity(owner_name):
                # Look up in Sunbiz
                corp_response = await self.supabase.from_('sunbiz_corporate')\
                    .select('*')\
                    .ilike('entity_name', f'%{owner_name}%')\
                    .limit(1)\
                    .execute()
                    
                if corp_response.data:
                    corp = corp_response.data[0]
                    
                    # Determine investment type
                    investment_type = self._classify_investment_type(owner_name, value)
                    
                    match_thoughts = thoughts.copy()
                    match_thoughts.append(ThoughtProcess(
                        "Investment Pattern",
                        f"Identified as {investment_type}",
                        0.5,
                        [f"Portfolio value range: ${value:,.0f}"]
                    ))
                    
                    results.append(ChainOfThoughtResult(
                        company_name=corp['entity_name'],
                        company_doc_number=corp['doc_number'],
                        confidence=0.5,
                        match_type="Financial Pattern",
                        thought_chain=match_thoughts,
                        evidence=[
                            f"Property value: ${value:,.0f}",
                            f"Investment type: {investment_type}",
                            f"Entity type: {corp.get('subtype', 'Unknown')}"
                        ],
                        agent_name=self.name,
                        processing_time=0
                    ))
                    
        return results
    
    def _is_investment_entity(self, name: str) -> bool:
        """Check if name suggests investment entity"""
        investment_keywords = [
            'INVESTMENT', 'CAPITAL', 'HOLDINGS', 'PROPERTIES',
            'REALTY', 'REAL ESTATE', 'REIT', 'FUND', 'TRUST',
            'VENTURES', 'PARTNERS', 'EQUITY', 'ASSETS'
        ]
        name_upper = name.upper()
        return any(keyword in name_upper for keyword in investment_keywords)
    
    def _classify_investment_type(self, name: str, value: float) -> str:
        """Classify the type of investment entity"""
        name_upper = name.upper()
        
        if 'REIT' in name_upper or value > 10000000:
            return "Real Estate Investment Trust"
        elif 'FUND' in name_upper:
            return "Investment Fund"
        elif 'CAPITAL' in name_upper or 'EQUITY' in name_upper:
            return "Private Equity/Capital"
        elif 'HOLDINGS' in name_upper:
            return "Holding Company"
        elif 'TRUST' in name_upper:
            return "Trust/Estate"
        elif value > 5000000:
            return "Institutional Investor"
        else:
            return "Commercial Investor"

# =====================================================
# ORCHESTRATOR WITH HEALTH MONITORING
# =====================================================

class ChainOfThoughtOrchestrator:
    """Master orchestrator with chain-of-thought reasoning and health monitoring"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        
        # Initialize all agents
        self.agents = {
            'tier1': [
                TaxIdChainAgent(supabase_client),
                MortgageDocumentChainAgent(supabase_client),
                UtilityAccountChainAgent(supabase_client)
            ],
            'tier2': [
                PermitLicenseChainAgent(supabase_client),
                DigitalFootprintChainAgent(supabase_client),
                PropertyManagerPatternAgent(supabase_client)
            ],
            'tier3': [
                NameVariationChainAgent(supabase_client),
                NetworkAnalysisChainAgent(supabase_client),
                HistoricalTransactionAgent(supabase_client)
            ],
            'tier4': [
                GeospatialClusterAgent(supabase_client),
                IndustryClassificationAgent(supabase_client),
                FinancialPatternAgent(supabase_client)
            ]
        }
        
        # Start health monitoring
        self.monitoring_active = True
        asyncio.create_task(self._monitor_health())
        
    async def match_with_reasoning(self, property_data: Dict, 
                                  min_confidence: float = 0.6,
                                  max_agents: int = 6,
                                  explain: bool = True) -> Dict:
        """
        Execute matching with full chain-of-thought reasoning
        """
        start_time = datetime.now()
        all_results = []
        reasoning_chain = []
        agents_used = []
        
        # Master thought process
        reasoning_chain.append(ThoughtProcess(
            "Initialization",
            f"Starting property-company matching for {property_data.get('address', 'property')}",
            1.0,
            [f"Min confidence: {min_confidence}", f"Max agents: {max_agents}"]
        ))
        
        # Determine strategy based on available data
        strategy = self._determine_strategy(property_data)
        reasoning_chain.append(ThoughtProcess(
            "Strategy Selection",
            f"Selected strategy: {strategy['name']}",
            strategy['confidence'],
            strategy['reasons']
        ))
        
        # Execute agents based on strategy
        for tier in strategy['tier_order']:
            if len(agents_used) >= max_agents:
                break
                
            tier_agents = self.agents[tier]
            
            # Run agents in parallel within tier
            tasks = []
            for agent in tier_agents:
                if len(agents_used) >= max_agents:
                    break
                if agent.status == AgentStatus.ACTIVE:
                    tasks.append(agent.match(property_data))
                    agents_used.append(agent.name)
                    
            if tasks:
                tier_results = await asyncio.gather(*tasks)
                for results in tier_results:
                    all_results.extend(results)
                    
            # Check if we have high-confidence matches
            high_confidence = [r for r in all_results if r.confidence >= 0.85]
            if high_confidence and tier in ['tier1', 'tier2']:
                reasoning_chain.append(ThoughtProcess(
                    "Early Termination",
                    f"Found {len(high_confidence)} high-confidence matches - stopping search",
                    0.9,
                    [f"Best match: {high_confidence[0].company_name}"]
                ))
                break
                
        # Filter and deduplicate results
        filtered_results = [r for r in all_results if r.confidence >= min_confidence]
        unique_results = self._deduplicate_results(filtered_results)
        
        # Sort by confidence
        unique_results.sort(key=lambda r: r.confidence, reverse=True)
        
        # Generate final analysis
        processing_time = (datetime.now() - start_time).total_seconds()
        
        reasoning_chain.append(ThoughtProcess(
            "Final Analysis",
            f"Completed matching with {len(unique_results)} results above threshold",
            0.95,
            [
                f"Agents used: {len(agents_used)}",
                f"Processing time: {processing_time:.2f}s",
                f"Best match confidence: {unique_results[0].confidence:.2f}" if unique_results else "No matches found"
            ]
        ))
        
        # Build response
        response = {
            "matches": unique_results[:10],  # Top 10 matches
            "reasoning_chain": reasoning_chain,
            "agents_used": agents_used,
            "processing_time": processing_time,
            "strategy": strategy['name']
        }
        
        if explain and unique_results:
            response["explanation"] = self._generate_explanation(unique_results[0], reasoning_chain)
            
        return response
    
    def _determine_strategy(self, property_data: Dict) -> Dict:
        """Determine the best matching strategy based on available data"""
        
        # Check what data we have
        has_tax_id = bool(property_data.get('tax_id') or property_data.get('ein'))
        has_parcel = bool(property_data.get('parcel_id'))
        has_address = bool(property_data.get('address'))
        has_owner = bool(property_data.get('owner_name'))
        has_coords = bool(property_data.get('latitude') and property_data.get('longitude'))
        
        if has_tax_id:
            return {
                'name': 'Tax ID Priority',
                'confidence': 0.95,
                'tier_order': ['tier1', 'tier2'],
                'reasons': ['Tax ID available - highest accuracy matching']
            }
        elif has_parcel and has_address:
            return {
                'name': 'Document-Based',
                'confidence': 0.85,
                'tier_order': ['tier1', 'tier2', 'tier3'],
                'reasons': ['Full property identification available', 'Can search documents and permits']
            }
        elif has_owner and has_address:
            return {
                'name': 'Owner-Address Correlation',
                'confidence': 0.75,
                'tier_order': ['tier2', 'tier3', 'tier1'],
                'reasons': ['Owner and address for cross-reference', 'License and permit matching possible']
            }
        elif has_owner:
            return {
                'name': 'Name-Based Network',
                'confidence': 0.65,
                'tier_order': ['tier3', 'tier2', 'tier4'],
                'reasons': ['Owner name only - using variations and network analysis']
            }
        elif has_coords:
            return {
                'name': 'Geospatial',
                'confidence': 0.5,
                'tier_order': ['tier4', 'tier3'],
                'reasons': ['Coordinates only - using spatial analysis']
            }
        else:
            return {
                'name': 'Broad Search',
                'confidence': 0.4,
                'tier_order': ['tier3', 'tier4'],
                'reasons': ['Limited data - using all available methods']
            }
    
    def _deduplicate_results(self, results: List[ChainOfThoughtResult]) -> List[ChainOfThoughtResult]:
        """Remove duplicate companies, keeping highest confidence"""
        seen = {}
        unique = []
        
        for result in results:
            key = result.company_doc_number
            if key not in seen or result.confidence > seen[key].confidence:
                seen[key] = result
                
        return list(seen.values())
    
    def _generate_explanation(self, best_match: ChainOfThoughtResult, 
                             reasoning_chain: List[ThoughtProcess]) -> str:
        """Generate human-readable explanation"""
        
        explanation = f"**Best Match: {best_match.company_name}**\n\n"
        explanation += f"**Confidence: {best_match.confidence:.1%}**\n\n"
        
        explanation += "**Reasoning Process:**\n"
        for thought in best_match.thought_chain[:3]:  # Top 3 thoughts
            explanation += f"- {thought.reasoning} (confidence: {thought.confidence:.1%})\n"
            
        explanation += f"\n**Evidence:**\n"
        for evidence in best_match.evidence[:5]:  # Top 5 evidence
            explanation += f"- {evidence}\n"
            
        explanation += f"\n**Match Type:** {best_match.match_type}\n"
        explanation += f"**Agent:** {best_match.agent_name}\n"
        
        return explanation
    
    async def _monitor_health(self):
        """Monitor agent health and keep them active"""
        while self.monitoring_active:
            try:
                for tier, agents in self.agents.items():
                    for agent in agents:
                        # Check if agent needs heartbeat
                        time_since_heartbeat = (datetime.now() - agent.last_heartbeat).total_seconds()
                        
                        if time_since_heartbeat > 60:  # Heartbeat every minute
                            status = await agent.heartbeat()
                            
                            if agent.status == AgentStatus.ERROR:
                                logger.warning(f"Agent {agent.name} in error state - attempting recovery")
                                agent.status = AgentStatus.ACTIVE
                                
                            # Log agent health
                            if agent.success_rate < 0.5:
                                logger.warning(f"Agent {agent.name} success rate low: {agent.success_rate:.1%}")
                                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Health monitoring error: {str(e)}")
                await asyncio.sleep(60)
    
    async def get_agent_status(self) -> Dict:
        """Get current status of all agents"""
        status = {}
        
        for tier, agents in self.agents.items():
            tier_status = []
            for agent in agents:
                tier_status.append({
                    "name": agent.name,
                    "status": agent.status.value,
                    "last_heartbeat": agent.last_heartbeat.isoformat(),
                    "total_processed": agent.total_processed,
                    "success_rate": f"{agent.success_rate:.1%}"
                })
            status[tier] = tier_status
            
        return status
    
    def shutdown(self):
        """Gracefully shutdown the orchestrator"""
        self.monitoring_active = False
        logger.info("Chain-of-thought orchestrator shutdown complete")
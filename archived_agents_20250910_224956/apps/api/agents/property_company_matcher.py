"""
Property to Company Matching Agent System
Intelligent agents for finding relationships between properties and businesses
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime
import asyncio
from abc import ABC, abstractmethod

class MatchConfidence(Enum):
    """Confidence levels for property-company matches"""
    EXACT = 95  # Direct documentary evidence
    VERY_HIGH = 85  # Multiple strong indicators
    HIGH = 75  # Strong correlation
    MEDIUM = 60  # Probable match
    LOW = 40  # Possible match
    UNCERTAIN = 20  # Weak correlation

@dataclass
class MatchResult:
    """Result of a property-company matching attempt"""
    company_name: str
    company_doc_number: str
    confidence: MatchConfidence
    match_type: str
    evidence: List[str]
    agent_name: str
    timestamp: datetime

class BaseMatchingAgent(ABC):
    """Base class for all property-company matching agents"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.name = self.__class__.__name__
        
    @abstractmethod
    async def match(self, property_data: Dict) -> List[MatchResult]:
        """Attempt to match property to companies"""
        pass
    
    def calculate_confidence(self, evidence_count: int, evidence_quality: str) -> MatchConfidence:
        """Calculate match confidence based on evidence"""
        if evidence_quality == "documentary":
            return MatchConfidence.EXACT
        elif evidence_count >= 3 and evidence_quality == "strong":
            return MatchConfidence.VERY_HIGH
        elif evidence_count >= 2 and evidence_quality == "strong":
            return MatchConfidence.HIGH
        elif evidence_count >= 1 and evidence_quality == "moderate":
            return MatchConfidence.MEDIUM
        else:
            return MatchConfidence.LOW

# TIER 1: Very High Accuracy Agents (90-95%)

class TaxIdCrossReferenceAgent(BaseMatchingAgent):
    """Matches properties to companies via tax ID numbers"""
    
    async def match(self, property_data: Dict) -> List[MatchResult]:
        results = []
        
        # Extract tax ID from property records
        tax_id = property_data.get('tax_id') or property_data.get('ein')
        if not tax_id:
            return results
            
        # Search Sunbiz for matching EIN
        response = await self.supabase.from_('sunbiz_corporate')\
            .select('*')\
            .eq('ein', tax_id)\
            .execute()
            
        for corp in response.data:
            results.append(MatchResult(
                company_name=corp['entity_name'],
                company_doc_number=corp['doc_number'],
                confidence=MatchConfidence.EXACT,
                match_type="Tax ID Match",
                evidence=[f"EIN {tax_id} matches corporate records"],
                agent_name=self.name,
                timestamp=datetime.now()
            ))
            
        return results

class MortgageLenderDocumentAgent(BaseMatchingAgent):
    """Analyzes mortgage and deed documents for business entities"""
    
    async def match(self, property_data: Dict) -> List[MatchResult]:
        results = []
        parcel_id = property_data.get('parcel_id')
        
        # Query mortgage records
        mortgage_response = await self.supabase.from_('property_mortgages')\
            .select('*')\
            .eq('parcel_id', parcel_id)\
            .execute()
            
        for mortgage in mortgage_response.data:
            # Check if mortgagee is a business entity
            mortgagee = mortgage.get('mortgagee_name', '')
            if self._is_business_entity(mortgagee):
                # Search for matching business
                corp_response = await self.supabase.from_('sunbiz_corporate')\
                    .select('*')\
                    .ilike('entity_name', f'%{mortgagee}%')\
                    .execute()
                    
                for corp in corp_response.data:
                    results.append(MatchResult(
                        company_name=corp['entity_name'],
                        company_doc_number=corp['doc_number'],
                        confidence=MatchConfidence.VERY_HIGH,
                        match_type="Mortgage Document",
                        evidence=[
                            f"Mortgagee: {mortgagee}",
                            f"Mortgage Date: {mortgage.get('record_date')}",
                            f"Document #: {mortgage.get('document_number')}"
                        ],
                        agent_name=self.name,
                        timestamp=datetime.now()
                    ))
                    
        return results
    
    def _is_business_entity(self, name: str) -> bool:
        """Check if name appears to be a business entity"""
        business_indicators = ['LLC', 'INC', 'CORP', 'LP', 'LLP', 'PA', 
                              'PARTNERSHIP', 'COMPANY', 'ASSOCIATES', 'GROUP']
        name_upper = name.upper()
        return any(indicator in name_upper for indicator in business_indicators)

# TIER 2: High Accuracy Agents (75-85%)

class PermitLicenseAgent(BaseMatchingAgent):
    """Matches properties via building permits and business licenses"""
    
    async def match(self, property_data: Dict) -> List[MatchResult]:
        results = []
        address = property_data.get('address')
        
        # Query permits for this property
        permit_response = await self.supabase.from_('building_permits')\
            .select('*')\
            .eq('property_address', address)\
            .execute()
            
        # Query business licenses at this address
        license_response = await self.supabase.from_('business_licenses')\
            .select('*')\
            .eq('business_address', address)\
            .execute()
            
        # Cross-reference permits with business entities
        for permit in permit_response.data:
            applicant = permit.get('applicant_name', '')
            if self._is_business_entity(applicant):
                # Match with licenses
                for license in license_response.data:
                    if self._names_match(applicant, license.get('business_name', '')):
                        results.append(MatchResult(
                            company_name=license['business_name'],
                            company_doc_number=license.get('sunbiz_doc_number', ''),
                            confidence=MatchConfidence.HIGH,
                            match_type="Permit & License Match",
                            evidence=[
                                f"Permit Applicant: {applicant}",
                                f"Business License: {license['license_number']}",
                                f"License Type: {license.get('license_type', 'N/A')}"
                            ],
                            agent_name=self.name,
                            timestamp=datetime.now()
                        ))
                        
        return results
    
    def _is_business_entity(self, name: str) -> bool:
        """Check if name appears to be a business entity"""
        business_indicators = ['LLC', 'INC', 'CORP', 'LP', 'LLP', 'PA']
        name_upper = name.upper()
        return any(indicator in name_upper for indicator in business_indicators)
    
    def _names_match(self, name1: str, name2: str, threshold: float = 0.8) -> bool:
        """Fuzzy match business names"""
        # Simple implementation - could use Levenshtein distance
        name1_clean = re.sub(r'[^a-zA-Z0-9]', '', name1.upper())
        name2_clean = re.sub(r'[^a-zA-Z0-9]', '', name2.upper())
        return name1_clean == name2_clean or name1_clean in name2_clean or name2_clean in name1_clean

class DomainDigitalFootprintAgent(BaseMatchingAgent):
    """Searches for businesses listing the property address online"""
    
    async def match(self, property_data: Dict) -> List[MatchResult]:
        results = []
        address = property_data.get('address')
        city = property_data.get('city')
        
        # This would typically call external APIs like Google Places, Bing, etc.
        # For now, we'll check our cached web presence data
        web_response = await self.supabase.from_('business_web_presence')\
            .select('*')\
            .ilike('listed_address', f'%{address}%')\
            .execute()
            
        for web_presence in web_response.data:
            # Verify it's the same city
            if city and city.upper() in web_presence.get('listed_address', '').upper():
                results.append(MatchResult(
                    company_name=web_presence['business_name'],
                    company_doc_number=web_presence.get('sunbiz_doc_number', ''),
                    confidence=MatchConfidence.HIGH,
                    match_type="Digital Footprint",
                    evidence=[
                        f"Website: {web_presence.get('website', 'N/A')}",
                        f"Google Business: {web_presence.get('google_verified', False)}",
                        f"Social Media: {web_presence.get('social_media_links', 'N/A')}"
                    ],
                    agent_name=self.name,
                    timestamp=datetime.now()
                ))
                
        return results

# TIER 3: Medium Accuracy Agents (60-75%)

class NameVariationAliasAgent(BaseMatchingAgent):
    """Handles business name variations, DBAs, and aliases"""
    
    async def match(self, property_data: Dict) -> List[MatchResult]:
        results = []
        owner_name = property_data.get('owner_name', '')
        
        if not owner_name:
            return results
            
        # Generate name variations
        variations = self._generate_name_variations(owner_name)
        
        for variation in variations:
            # Search corporate entities
            corp_response = await self.supabase.from_('sunbiz_corporate')\
                .select('*')\
                .or_(f'entity_name.ilike.%{variation}%,trade_name.ilike.%{variation}%')\
                .execute()
                
            # Search fictitious names
            dba_response = await self.supabase.from_('sunbiz_fictitious')\
                .select('*')\
                .ilike('name', f'%{variation}%')\
                .execute()
                
            for corp in corp_response.data:
                results.append(MatchResult(
                    company_name=corp['entity_name'],
                    company_doc_number=corp['doc_number'],
                    confidence=MatchConfidence.MEDIUM,
                    match_type="Name Variation",
                    evidence=[
                        f"Original: {owner_name}",
                        f"Matched Variation: {variation}",
                        f"Match Type: {'DBA' if 'trade_name' in corp else 'Entity Name'}"
                    ],
                    agent_name=self.name,
                    timestamp=datetime.now()
                ))
                
        return results
    
    def _generate_name_variations(self, name: str) -> List[str]:
        """Generate possible variations of a business name"""
        variations = [name]
        
        # Remove common suffixes
        suffixes = ['LLC', 'INC', 'CORP', 'CO', 'COMPANY', 'LP', 'LLP']
        for suffix in suffixes:
            pattern = rf'\s*{suffix}\.?\s*$'
            clean_name = re.sub(pattern, '', name, flags=re.IGNORECASE).strip()
            if clean_name != name:
                variations.append(clean_name)
                
        # Add common suffixes if not present
        base_name = variations[-1] if len(variations) > 1 else name
        if not any(suffix in name.upper() for suffix in suffixes):
            variations.extend([
                f"{base_name} LLC",
                f"{base_name} INC",
                f"{base_name} CORP"
            ])
            
        # Handle possessives
        if "'s" in name or "'S" in name:
            variations.append(re.sub(r"'[sS]\s*", " ", name))
        else:
            variations.append(f"{name}'s")
            
        # Handle "and" vs "&"
        if " AND " in name.upper():
            variations.append(name.replace(" AND ", " & ").replace(" and ", " & "))
        elif " & " in name:
            variations.append(name.replace(" & ", " AND "))
            
        return list(set(variations))  # Remove duplicates

class NetworkAnalysisAgent(BaseMatchingAgent):
    """Maps relationships between officers and entities"""
    
    async def match(self, property_data: Dict) -> List[MatchResult]:
        results = []
        owner_name = property_data.get('owner_name', '')
        
        if not owner_name:
            return results
            
        # Parse individual names from owner
        individual_names = self._parse_individual_names(owner_name)
        
        for individual in individual_names:
            # Find all companies where this person is an officer
            officer_response = await self.supabase.from_('sunbiz_officers')\
                .select('doc_number')\
                .ilike('officer_name', f'%{individual}%')\
                .execute()
                
            if officer_response.data:
                doc_numbers = [o['doc_number'] for o in officer_response.data]
                
                # Get company details
                corp_response = await self.supabase.from_('sunbiz_corporate')\
                    .select('*')\
                    .in_('doc_number', doc_numbers)\
                    .execute()
                    
                for corp in corp_response.data:
                    # Check if this company has other properties
                    other_props = await self._find_other_properties(corp['entity_name'])
                    
                    results.append(MatchResult(
                        company_name=corp['entity_name'],
                        company_doc_number=corp['doc_number'],
                        confidence=MatchConfidence.MEDIUM,
                        match_type="Officer Network",
                        evidence=[
                            f"Officer: {individual}",
                            f"Role: {self._get_officer_role(individual, corp['doc_number'])}",
                            f"Other Properties: {len(other_props)}"
                        ],
                        agent_name=self.name,
                        timestamp=datetime.now()
                    ))
                    
        return results
    
    def _parse_individual_names(self, owner_name: str) -> List[str]:
        """Extract individual names from owner string"""
        # Split on common separators
        names = re.split(r'\s*[&,]\s*|\s+AND\s+', owner_name, flags=re.IGNORECASE)
        # Filter out business names
        individual_names = []
        for name in names:
            if not any(indicator in name.upper() for indicator in ['LLC', 'INC', 'CORP']):
                individual_names.append(name.strip())
        return individual_names
    
    async def _find_other_properties(self, company_name: str) -> List[str]:
        """Find other properties owned by this company"""
        response = await self.supabase.from_('florida_parcels')\
            .select('parcel_id')\
            .ilike('owner_name', f'%{company_name}%')\
            .limit(10)\
            .execute()
        return [p['parcel_id'] for p in response.data]
    
    async def _get_officer_role(self, officer_name: str, doc_number: str) -> str:
        """Get officer's role in the company"""
        response = await self.supabase.from_('sunbiz_officers')\
            .select('officer_title')\
            .eq('doc_number', doc_number)\
            .ilike('officer_name', f'%{officer_name}%')\
            .single()\
            .execute()
        return response.data.get('officer_title', 'Unknown') if response.data else 'Unknown'

# TIER 4: Moderate Accuracy Agents (45-60%)

class GeospatialClusteringAgent(BaseMatchingAgent):
    """Identifies businesses owning nearby properties"""
    
    async def match(self, property_data: Dict) -> List[MatchResult]:
        results = []
        lat = property_data.get('latitude')
        lon = property_data.get('longitude')
        
        if not lat or not lon:
            return results
            
        # Find nearby properties (within 0.5 miles)
        # This is a simplified version - real implementation would use PostGIS
        nearby_response = await self.supabase.rpc('find_nearby_properties', {
            'lat': lat,
            'lon': lon,
            'radius_miles': 0.5
        }).execute()
        
        # Group by owner
        owner_counts = {}
        for prop in nearby_response.data:
            owner = prop.get('owner_name', '')
            if self._is_business_entity(owner):
                owner_counts[owner] = owner_counts.get(owner, 0) + 1
                
        # Find owners with multiple nearby properties
        for owner, count in owner_counts.items():
            if count >= 2:  # Owns at least 2 nearby properties
                # Look up in Sunbiz
                corp_response = await self.supabase.from_('sunbiz_corporate')\
                    .select('*')\
                    .ilike('entity_name', f'%{owner}%')\
                    .execute()
                    
                for corp in corp_response.data:
                    results.append(MatchResult(
                        company_name=corp['entity_name'],
                        company_doc_number=corp['doc_number'],
                        confidence=MatchConfidence.LOW,
                        match_type="Geospatial Cluster",
                        evidence=[
                            f"Owns {count} properties within 0.5 miles",
                            f"Cluster Pattern: {self._identify_pattern(count, nearby_response.data)}"
                        ],
                        agent_name=self.name,
                        timestamp=datetime.now()
                    ))
                    
        return results
    
    def _is_business_entity(self, name: str) -> bool:
        """Check if name appears to be a business entity"""
        business_indicators = ['LLC', 'INC', 'CORP', 'LP', 'LLP', 'PA']
        name_upper = name.upper()
        return any(indicator in name_upper for indicator in business_indicators)
    
    def _identify_pattern(self, count: int, properties: List[Dict]) -> str:
        """Identify spatial pattern of ownership"""
        if count >= 5:
            return "Major cluster - possible development"
        elif count >= 3:
            return "Medium cluster - expansion pattern"
        else:
            return "Small cluster - initial investment"

# Master Orchestrator

class PropertyCompanyMatcher:
    """Orchestrates multiple agents to find property-company matches"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        
        # Initialize agents in priority order
        self.tier1_agents = [
            TaxIdCrossReferenceAgent(supabase_client),
            MortgageLenderDocumentAgent(supabase_client)
        ]
        
        self.tier2_agents = [
            PermitLicenseAgent(supabase_client),
            DomainDigitalFootprintAgent(supabase_client)
        ]
        
        self.tier3_agents = [
            NameVariationAliasAgent(supabase_client),
            NetworkAnalysisAgent(supabase_client)
        ]
        
        self.tier4_agents = [
            GeospatialClusteringAgent(supabase_client)
        ]
        
    async def find_matches(self, property_data: Dict, 
                          min_confidence: MatchConfidence = MatchConfidence.MEDIUM,
                          max_agents: int = 5) -> List[MatchResult]:
        """
        Find all possible company matches for a property
        
        Args:
            property_data: Property information
            min_confidence: Minimum confidence threshold
            max_agents: Maximum number of agents to run
        """
        all_results = []
        agents_run = 0
        
        # Run Tier 1 agents first (highest accuracy)
        for agent in self.tier1_agents:
            if agents_run >= max_agents:
                break
            results = await agent.match(property_data)
            all_results.extend(results)
            agents_run += 1
            
            # If we found high-confidence matches, we might stop
            if any(r.confidence.value >= 90 for r in results):
                break
                
        # If no high-confidence matches, try Tier 2
        if not any(r.confidence.value >= 85 for r in all_results):
            for agent in self.tier2_agents:
                if agents_run >= max_agents:
                    break
                results = await agent.match(property_data)
                all_results.extend(results)
                agents_run += 1
                
        # Continue with lower tiers if needed
        if not any(r.confidence.value >= 75 for r in all_results):
            for agent in self.tier3_agents:
                if agents_run >= max_agents:
                    break
                results = await agent.match(property_data)
                all_results.extend(results)
                agents_run += 1
                
        # Filter by minimum confidence
        filtered_results = [r for r in all_results 
                           if r.confidence.value >= min_confidence.value]
        
        # Sort by confidence (highest first)
        filtered_results.sort(key=lambda r: r.confidence.value, reverse=True)
        
        # Deduplicate by company
        seen_companies = set()
        unique_results = []
        for result in filtered_results:
            if result.company_doc_number not in seen_companies:
                seen_companies.add(result.company_doc_number)
                unique_results.append(result)
                
        return unique_results
    
    async def explain_match(self, match_result: MatchResult) -> str:
        """Generate human-readable explanation of why a match was made"""
        explanation = f"**{match_result.company_name}** was matched to this property with "\
                     f"**{match_result.confidence.value}% confidence**.\n\n"
        
        explanation += f"**Match Type:** {match_result.match_type}\n"
        explanation += f"**Agent:** {match_result.agent_name}\n\n"
        
        explanation += "**Evidence:**\n"
        for evidence in match_result.evidence:
            explanation += f"- {evidence}\n"
            
        return explanation
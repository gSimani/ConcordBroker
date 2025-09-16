"""
Entity Extraction Agent using BERT-base-NER
Extracts names, addresses, organizations, and financial entities
"""

from typing import Dict, Any, List
import aiohttp
import os
import re
from .base_agent import BaseAgent

class EntityExtractionAgent(BaseAgent):
    """Agent for extracting entities from property documents and text"""
    
    def __init__(self):
        super().__init__(
            agent_id="entity_extraction",
            name="Entity Extraction Agent",
            description="Extract entities using BERT-base-NER model"
        )
        self.model_id = "dslim/bert-base-NER"
        self.api_token = os.getenv("HUGGINGFACE_API_TOKEN")
        if not self.api_token:
            raise ValueError("HUGGINGFACE_API_TOKEN not configured for EntityExtractionAgent")
        self.entity_patterns = {
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "price": r"\$[\d,]+(?:\.\d{2})?",
            "parcel_id": r"\b\d{10,15}\b",
            "date": r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b"
        }
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input has text to process"""
        if "test" in input_data:
            return True
        return "text" in input_data or "document" in input_data
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entities from text"""
        
        text = input_data.get("text") or input_data.get("document", "")
        extract_type = input_data.get("extract_type", "all")
        
        self.logger.info(f"Extracting entities from text (length: {len(text)})")
        
        # Get NER entities from BERT
        ner_entities = await self._extract_ner_entities(text)
        
        # Extract pattern-based entities
        pattern_entities = self._extract_pattern_entities(text)
        
        # Process and categorize entities
        categorized = self._categorize_entities(ner_entities, pattern_entities)
        
        # Filter by extract_type if specified
        if extract_type != "all":
            categorized = self._filter_entities(categorized, extract_type)
        
        # Enhance with context
        enhanced = self._enhance_entities(categorized, text)
        
        return {
            "entities": enhanced,
            "summary": self._generate_summary(enhanced),
            "confidence_scores": self._calculate_confidence(enhanced),
            "text_length": len(text),
            "model": self.model_id
        }
    
    async def _extract_ner_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using BERT-NER model"""
        
        url = f"https://api-inference.huggingface.co/models/{self.model_id}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # Split text into chunks if too long
        max_length = 512
        chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        
        all_entities = []
        
        for chunk in chunks:
            payload = {
                "inputs": chunk,
                "options": {"wait_for_model": True}
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            all_entities.extend(result)
                        else:
                            self.logger.warning(f"NER API call failed: {response.status}")
            except Exception as e:
                self.logger.error(f"Error calling NER API: {str(e)}")
        
        return all_entities
    
    def _extract_pattern_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using regex patterns"""
        
        extracted = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                extracted[entity_type] = list(set(matches))
        
        return extracted
    
    def _categorize_entities(self, ner_entities: List[Dict], pattern_entities: Dict) -> Dict[str, List[Any]]:
        """Categorize all extracted entities"""
        
        categorized = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "addresses": [],
            "financial": [],
            "dates": [],
            "contact": [],
            "property_ids": []
        }
        
        # Process NER entities
        for entity in ner_entities:
            entity_type = entity.get("entity_group", entity.get("entity", "")).upper()
            word = entity.get("word", "").strip()
            score = entity.get("score", 0.0)
            
            if not word:
                continue
            
            entity_info = {
                "value": word,
                "confidence": score,
                "source": "ner"
            }
            
            if "PER" in entity_type:
                categorized["persons"].append(entity_info)
            elif "ORG" in entity_type:
                categorized["organizations"].append(entity_info)
            elif "LOC" in entity_type or "GPE" in entity_type:
                categorized["locations"].append(entity_info)
        
        # Add pattern-based entities
        if "phone" in pattern_entities:
            for phone in pattern_entities["phone"]:
                categorized["contact"].append({
                    "value": phone,
                    "type": "phone",
                    "confidence": 0.95,
                    "source": "pattern"
                })
        
        if "email" in pattern_entities:
            for email in pattern_entities["email"]:
                categorized["contact"].append({
                    "value": email,
                    "type": "email",
                    "confidence": 0.95,
                    "source": "pattern"
                })
        
        if "price" in pattern_entities:
            for price in pattern_entities["price"]:
                categorized["financial"].append({
                    "value": price,
                    "type": "price",
                    "confidence": 0.9,
                    "source": "pattern"
                })
        
        if "date" in pattern_entities:
            for date in pattern_entities["date"]:
                categorized["dates"].append({
                    "value": date,
                    "confidence": 0.85,
                    "source": "pattern"
                })
        
        if "parcel_id" in pattern_entities:
            for pid in pattern_entities["parcel_id"]:
                categorized["property_ids"].append({
                    "value": pid,
                    "confidence": 0.8,
                    "source": "pattern"
                })
        
        # Remove duplicates and empty categories
        for category in categorized:
            # Remove duplicates based on value
            seen = set()
            unique = []
            for item in categorized[category]:
                val = item.get("value", "")
                if val and val not in seen:
                    seen.add(val)
                    unique.append(item)
            categorized[category] = unique
        
        return categorized
    
    def _filter_entities(self, entities: Dict, extract_type: str) -> Dict:
        """Filter entities by type"""
        
        type_mapping = {
            "names": ["persons"],
            "addresses": ["locations", "addresses"],
            "prices": ["financial"],
            "dates": ["dates"],
            "organizations": ["organizations"],
            "contact": ["contact"]
        }
        
        if extract_type in type_mapping:
            filtered = {}
            for key in type_mapping[extract_type]:
                if key in entities:
                    filtered[key] = entities[key]
            return filtered
        
        return entities
    
    def _enhance_entities(self, entities: Dict, text: str) -> Dict:
        """Enhance entities with context and relationships"""
        
        enhanced = entities.copy()
        
        # Find relationships between entities
        relationships = []
        
        # Check for buyer/seller patterns
        buyer_patterns = ["buyer", "purchaser", "bought by", "purchased by"]
        seller_patterns = ["seller", "vendor", "sold by", "owner"]
        
        for person in enhanced.get("persons", []):
            person_name = person["value"]
            
            # Check context around person name
            for pattern in buyer_patterns:
                if pattern in text.lower() and person_name in text:
                    person["role"] = "buyer"
                    relationships.append({
                        "entity": person_name,
                        "role": "buyer",
                        "confidence": 0.7
                    })
                    break
            
            for pattern in seller_patterns:
                if pattern in text.lower() and person_name in text:
                    person["role"] = "seller"
                    relationships.append({
                        "entity": person_name,
                        "role": "seller",
                        "confidence": 0.7
                    })
                    break
        
        enhanced["relationships"] = relationships
        
        # Identify potential addresses by combining location entities
        potential_addresses = []
        locations = enhanced.get("locations", [])
        for i, loc in enumerate(locations):
            # Check if next location could form an address
            if i < len(locations) - 1:
                combined = f"{loc['value']} {locations[i+1]['value']}"
                if any(word in combined.lower() for word in ["street", "st", "avenue", "ave", "road", "rd", "drive", "dr"]):
                    potential_addresses.append({
                        "value": combined,
                        "confidence": 0.6,
                        "source": "combined"
                    })
        
        if potential_addresses:
            enhanced["addresses"] = enhanced.get("addresses", []) + potential_addresses
        
        return enhanced
    
    def _generate_summary(self, entities: Dict) -> Dict[str, Any]:
        """Generate summary of extracted entities"""
        
        summary = {
            "total_entities": sum(len(v) for v in entities.values() if isinstance(v, list)),
            "categories_found": [k for k, v in entities.items() if v and isinstance(v, list)],
            "key_findings": []
        }
        
        # Add key findings
        if entities.get("persons"):
            summary["key_findings"].append(f"Found {len(entities['persons'])} person(s)")
        
        if entities.get("financial"):
            prices = [e["value"] for e in entities["financial"] if e.get("type") == "price"]
            if prices:
                summary["key_findings"].append(f"Found {len(prices)} price reference(s)")
        
        if entities.get("property_ids"):
            summary["key_findings"].append(f"Found {len(entities['property_ids'])} property ID(s)")
        
        if entities.get("relationships"):
            summary["key_findings"].append(f"Identified {len(entities['relationships'])} relationship(s)")
        
        return summary
    
    def _calculate_confidence(self, entities: Dict) -> Dict[str, float]:
        """Calculate average confidence for each category"""
        
        confidence_scores = {}
        
        for category, items in entities.items():
            if isinstance(items, list) and items:
                scores = [item.get("confidence", 0) for item in items if "confidence" in item]
                if scores:
                    confidence_scores[category] = sum(scores) / len(scores)
        
        return confidence_scores
    
    async def extract_from_contract(self, contract_text: str) -> Dict[str, Any]:
        """Specialized extraction for contracts"""
        
        # Extract standard entities
        result = await self.process({"text": contract_text})
        
        # Add contract-specific extraction
        contract_entities = {
            "parties": [],
            "property_description": "",
            "terms": [],
            "important_dates": []
        }
        
        # Extract parties (buyers and sellers)
        for person in result["entities"].get("persons", []):
            if person.get("role"):
                contract_entities["parties"].append({
                    "name": person["value"],
                    "role": person["role"]
                })
        
        # Extract important dates
        for date in result["entities"].get("dates", []):
            contract_entities["important_dates"].append(date["value"])
        
        # Extract financial terms
        for financial in result["entities"].get("financial", []):
            contract_entities["terms"].append({
                "type": "financial",
                "value": financial["value"]
            })
        
        result["contract_specific"] = contract_entities
        
        return result

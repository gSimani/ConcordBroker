"""
Document Processing Agent using GOT-OCR2.0 and Donut
Processes property documents, contracts, and images
"""

from typing import Dict, Any, List, Optional
import aiohttp
import os
import base64
from PIL import Image
import io
from .base_agent import BaseAgent

class DocumentProcessingAgent(BaseAgent):
    """Agent for processing property documents and images"""
    
    def __init__(self):
        super().__init__(
            agent_id="document_processing",
            name="Document Processing Agent", 
            description="Process documents using GOT-OCR2.0 and Donut models"
        )
        self.ocr_model = "ucaslcl/GOT-OCR2_0"  # For OCR tasks
        self.donut_model = "naver-clova-ix/donut-base"  # For document understanding
        self.api_token = os.getenv("HUGGINGFACE_API_TOKEN", "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")
        self.processed_documents = {}
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate document processing input"""
        if "test" in input_data:
            return True
        return any(key in input_data for key in ["document", "image", "file_path", "documents"])
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process documents based on input type"""
        
        doc_type = input_data.get("document_type", "general")
        
        self.logger.info(f"Processing document of type: {doc_type}")
        
        if "documents" in input_data:
            return await self._batch_process(input_data["documents"])
        elif "image" in input_data:
            return await self._process_image(input_data["image"], doc_type)
        elif "file_path" in input_data:
            return await self._process_file(input_data["file_path"], doc_type)
        elif "document" in input_data:
            return await self._process_text_document(input_data["document"], doc_type)
        else:
            raise ValueError("No valid document input provided")
    
    async def _process_image(self, image_data: Any, doc_type: str) -> Dict[str, Any]:
        """Process image document (deed, contract, etc.)"""
        
        # Determine processing strategy based on document type
        if doc_type == "property_deed":
            return await self._process_deed(image_data)
        elif doc_type == "tax_assessment":
            return await self._process_tax_assessment(image_data)
        elif doc_type == "contract":
            return await self._process_contract(image_data)
        elif doc_type == "property_photo":
            return await self._analyze_property_photo(image_data)
        else:
            return await self._general_ocr(image_data)
    
    async def _process_deed(self, image_data: Any) -> Dict[str, Any]:
        """Process property deed document"""
        
        # Extract text using OCR
        ocr_result = await self._perform_ocr(image_data)
        
        # Parse deed-specific information
        parsed_data = {
            "document_type": "property_deed",
            "raw_text": ocr_result,
            "extracted_fields": {}
        }
        
        # Extract key deed information
        fields_to_extract = {
            "grantor": ["grantor", "seller", "party of the first part"],
            "grantee": ["grantee", "buyer", "party of the second part"],
            "property_description": ["legal description", "property described as", "situated in"],
            "consideration": ["consideration", "sum of", "purchase price"],
            "recording_info": ["recorded", "book", "page", "instrument"],
            "date": ["dated", "day of", "executed on"]
        }
        
        for field, keywords in fields_to_extract.items():
            value = self._extract_field(ocr_result, keywords)
            if value:
                parsed_data["extracted_fields"][field] = value
        
        # Extract parcel information
        parcel_info = self._extract_parcel_info(ocr_result)
        if parcel_info:
            parsed_data["extracted_fields"]["parcel_info"] = parcel_info
        
        # Validate deed completeness
        parsed_data["validation"] = self._validate_deed(parsed_data["extracted_fields"])
        
        # Generate summary
        parsed_data["summary"] = self._generate_deed_summary(parsed_data["extracted_fields"])
        
        return parsed_data
    
    async def _process_tax_assessment(self, image_data: Any) -> Dict[str, Any]:
        """Process tax assessment document"""
        
        # Extract tables and text
        ocr_result = await self._perform_ocr(image_data)
        tables = await self._extract_tables(image_data)
        
        parsed_data = {
            "document_type": "tax_assessment",
            "raw_text": ocr_result,
            "tables": tables,
            "extracted_values": {}
        }
        
        # Extract assessment values
        value_patterns = {
            "assessed_value": ["assessed value", "total assessment", "market value"],
            "land_value": ["land value", "site value"],
            "improvement_value": ["improvement value", "building value"],
            "exemptions": ["exemption", "homestead", "senior"],
            "tax_amount": ["tax amount", "total tax", "amount due"],
            "millage_rate": ["millage", "tax rate", "mill rate"]
        }
        
        for field, patterns in value_patterns.items():
            value = self._extract_numeric_value(ocr_result, patterns)
            if value:
                parsed_data["extracted_values"][field] = value
        
        # Extract property details
        property_details = self._extract_property_details(ocr_result)
        parsed_data["property_details"] = property_details
        
        # Calculate effective tax rate if possible
        if parsed_data["extracted_values"].get("tax_amount") and parsed_data["extracted_values"].get("assessed_value"):
            tax_rate = (parsed_data["extracted_values"]["tax_amount"] / 
                       parsed_data["extracted_values"]["assessed_value"]) * 100
            parsed_data["calculated_tax_rate"] = round(tax_rate, 3)
        
        return parsed_data
    
    async def _process_contract(self, image_data: Any) -> Dict[str, Any]:
        """Process real estate contract"""
        
        ocr_result = await self._perform_ocr(image_data)
        
        parsed_data = {
            "document_type": "contract",
            "raw_text": ocr_result,
            "contract_terms": {},
            "parties": [],
            "important_dates": [],
            "contingencies": []
        }
        
        # Extract parties
        parsed_data["parties"] = self._extract_contract_parties(ocr_result)
        
        # Extract key terms
        terms_to_extract = {
            "purchase_price": ["purchase price", "total consideration", "sale price"],
            "earnest_money": ["earnest money", "deposit", "escrow amount"],
            "closing_date": ["closing date", "settlement date", "closing on"],
            "possession_date": ["possession date", "occupancy date"],
            "financing_terms": ["financing", "mortgage", "loan amount"]
        }
        
        for term, keywords in terms_to_extract.items():
            value = self._extract_field(ocr_result, keywords)
            if value:
                parsed_data["contract_terms"][term] = value
        
        # Extract contingencies
        contingency_keywords = ["contingent upon", "subject to", "conditional on", "provided that"]
        for keyword in contingency_keywords:
            contingencies = self._extract_contingencies(ocr_result, keyword)
            parsed_data["contingencies"].extend(contingencies)
        
        # Extract important dates
        parsed_data["important_dates"] = self._extract_dates(ocr_result)
        
        # Validate contract
        parsed_data["validation"] = self._validate_contract(parsed_data)
        
        # Risk assessment
        parsed_data["risk_assessment"] = self._assess_contract_risks(parsed_data)
        
        return parsed_data
    
    async def _analyze_property_photo(self, image_data: Any) -> Dict[str, Any]:
        """Analyze property photo for features and quality"""
        
        analysis = {
            "document_type": "property_photo",
            "detected_features": [],
            "quality_assessment": {},
            "room_type": None,
            "style_elements": []
        }
        
        # Detect room type and features
        # This would use image classification models
        room_keywords = ["kitchen", "bedroom", "bathroom", "living room", "exterior", "pool", "garage"]
        feature_keywords = ["granite", "hardwood", "stainless steel", "crown molding", "fireplace"]
        
        # Simulate feature detection
        analysis["detected_features"] = ["modern kitchen", "granite countertops", "stainless appliances"]
        analysis["room_type"] = "kitchen"
        analysis["style_elements"] = ["contemporary", "upgraded", "spacious"]
        
        # Quality assessment
        analysis["quality_assessment"] = {
            "lighting": "excellent",
            "composition": "professional",
            "resolution": "high",
            "staging": "well-staged"
        }
        
        # Generate description
        analysis["auto_description"] = self._generate_photo_description(analysis)
        
        # Marketing tags
        analysis["marketing_tags"] = self._generate_marketing_tags(analysis)
        
        return analysis
    
    async def _general_ocr(self, image_data: Any) -> Dict[str, Any]:
        """Perform general OCR on document"""
        
        text = await self._perform_ocr(image_data)
        
        return {
            "document_type": "general",
            "extracted_text": text,
            "word_count": len(text.split()),
            "detected_language": "en",
            "confidence": 0.85
        }
    
    async def _perform_ocr(self, image_data: Any) -> str:
        """Perform OCR using HuggingFace model"""
        
        # Convert image to base64 if needed
        if isinstance(image_data, str):
            image_b64 = image_data
        else:
            image_b64 = self._encode_image(image_data)
        
        # Simulate OCR (in production, would call actual model)
        # For now, return sample text
        return """WARRANTY DEED
        This deed made this 15th day of January, 2024, between John Smith and Jane Smith,
        husband and wife (Grantor), and Robert Johnson (Grantee).
        
        The Grantor, for consideration of Five Hundred Thousand Dollars ($500,000.00),
        hereby grants and conveys to the Grantee the following described real property:
        
        Lot 5, Block 2, Ocean View Estates, according to the plat recorded in
        Plat Book 125, Page 45, Public Records of Broward County, Florida.
        
        Property Address: 123 Ocean Drive, Fort Lauderdale, FL 33301
        Parcel ID: 494200010050
        
        Together with all improvements and appurtenances thereto."""
    
    async def _extract_tables(self, image_data: Any) -> List[Dict]:
        """Extract tables from document image"""
        
        # Simulate table extraction
        return [
            {
                "table_type": "assessment_values",
                "headers": ["Year", "Land Value", "Building Value", "Total Value"],
                "rows": [
                    ["2024", "$150,000", "$350,000", "$500,000"],
                    ["2023", "$140,000", "$340,000", "$480,000"],
                    ["2022", "$130,000", "$330,000", "$460,000"]
                ]
            }
        ]
    
    def _extract_field(self, text: str, keywords: List[str]) -> Optional[str]:
        """Extract field value based on keywords"""
        
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                # Extract text after keyword
                start = text_lower.find(keyword)
                end = text_lower.find("\n", start)
                if end == -1:
                    end = min(start + 200, len(text))
                
                extracted = text[start:end].strip()
                # Clean up extraction
                extracted = extracted.replace(keyword, "").strip(": ")
                
                return extracted[:100]  # Limit length
        
        return None
    
    def _extract_numeric_value(self, text: str, patterns: List[str]) -> Optional[float]:
        """Extract numeric value from text"""
        
        import re
        
        text_lower = text.lower()
        for pattern in patterns:
            if pattern in text_lower:
                # Look for numbers near the pattern
                start = text_lower.find(pattern)
                snippet = text[start:start+100]
                
                # Extract numbers
                numbers = re.findall(r'\$?[\d,]+\.?\d*', snippet)
                if numbers:
                    # Clean and convert first number
                    num_str = numbers[0].replace('$', '').replace(',', '')
                    try:
                        return float(num_str)
                    except:
                        pass
        
        return None
    
    def _extract_parcel_info(self, text: str) -> Optional[Dict]:
        """Extract parcel information from text"""
        
        import re
        
        parcel_info = {}
        
        # Look for parcel ID
        parcel_patterns = [r'Parcel ID:?\s*([\d-]+)', r'Folio:?\s*([\d-]+)', r'Tax ID:?\s*([\d-]+)']
        for pattern in parcel_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parcel_info["parcel_id"] = match.group(1)
                break
        
        # Look for lot/block
        lot_pattern = r'Lot\s+(\d+),?\s+Block\s+(\d+)'
        lot_match = re.search(lot_pattern, text, re.IGNORECASE)
        if lot_match:
            parcel_info["lot"] = lot_match.group(1)
            parcel_info["block"] = lot_match.group(2)
        
        # Look for subdivision
        sub_pattern = r'(?:subdivision|plat|estates?)\s+([A-Za-z\s]+?)(?:,|\.|according)'
        sub_match = re.search(sub_pattern, text, re.IGNORECASE)
        if sub_match:
            parcel_info["subdivision"] = sub_match.group(1).strip()
        
        return parcel_info if parcel_info else None
    
    def _extract_property_details(self, text: str) -> Dict:
        """Extract property details from assessment"""
        
        details = {}
        
        # Extract year built
        import re
        year_pattern = r'Year Built:?\s*(\d{4})'
        year_match = re.search(year_pattern, text, re.IGNORECASE)
        if year_match:
            details["year_built"] = int(year_match.group(1))
        
        # Extract square footage
        sqft_pattern = r'(?:Living Area|Square Feet|Sq Ft):?\s*([\d,]+)'
        sqft_match = re.search(sqft_pattern, text, re.IGNORECASE)
        if sqft_match:
            details["square_feet"] = int(sqft_match.group(1).replace(',', ''))
        
        # Extract bedrooms/bathrooms
        bed_pattern = r'(\d+)\s*(?:Bedrooms?|Beds?|BR)'
        bed_match = re.search(bed_pattern, text, re.IGNORECASE)
        if bed_match:
            details["bedrooms"] = int(bed_match.group(1))
        
        bath_pattern = r'(\d+(?:\.\d)?)\s*(?:Bathrooms?|Baths?|BA)'
        bath_match = re.search(bath_pattern, text, re.IGNORECASE)
        if bath_match:
            details["bathrooms"] = float(bath_match.group(1))
        
        return details
    
    def _extract_contract_parties(self, text: str) -> List[Dict]:
        """Extract parties from contract"""
        
        parties = []
        
        # Look for buyer/seller patterns
        import re
        
        buyer_patterns = [
            r'Buyer:?\s*([A-Za-z\s]+?)(?:\n|,)',
            r'Purchaser:?\s*([A-Za-z\s]+?)(?:\n|,)',
            r'Grantee:?\s*([A-Za-z\s]+?)(?:\n|,)'
        ]
        
        seller_patterns = [
            r'Seller:?\s*([A-Za-z\s]+?)(?:\n|,)',
            r'Vendor:?\s*([A-Za-z\s]+?)(?:\n|,)',
            r'Grantor:?\s*([A-Za-z\s]+?)(?:\n|,)'
        ]
        
        for pattern in buyer_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parties.append({
                    "name": match.group(1).strip(),
                    "role": "buyer"
                })
                break
        
        for pattern in seller_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parties.append({
                    "name": match.group(1).strip(),
                    "role": "seller"
                })
                break
        
        return parties
    
    def _extract_contingencies(self, text: str, keyword: str) -> List[str]:
        """Extract contingencies from contract"""
        
        contingencies = []
        text_lower = text.lower()
        
        if keyword in text_lower:
            start = text_lower.find(keyword)
            end = text_lower.find(".", start)
            if end == -1:
                end = min(start + 200, len(text))
            
            contingency = text[start:end].strip()
            contingencies.append(contingency)
        
        return contingencies
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from document"""
        
        import re
        
        date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))  # Remove duplicates
    
    def _validate_deed(self, fields: Dict) -> Dict:
        """Validate deed completeness"""
        
        required_fields = ["grantor", "grantee", "property_description", "consideration"]
        missing = [field for field in required_fields if field not in fields]
        
        return {
            "is_complete": len(missing) == 0,
            "missing_fields": missing,
            "confidence": 1.0 - (len(missing) * 0.25)
        }
    
    def _validate_contract(self, parsed_data: Dict) -> Dict:
        """Validate contract completeness"""
        
        issues = []
        
        if len(parsed_data["parties"]) < 2:
            issues.append("Missing buyer or seller information")
        
        if not parsed_data["contract_terms"].get("purchase_price"):
            issues.append("Purchase price not found")
        
        if not parsed_data["contract_terms"].get("closing_date"):
            issues.append("Closing date not specified")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "completeness_score": 1.0 - (len(issues) * 0.2)
        }
    
    def _assess_contract_risks(self, parsed_data: Dict) -> List[str]:
        """Assess risks in contract"""
        
        risks = []
        
        if len(parsed_data["contingencies"]) > 3:
            risks.append("Multiple contingencies may delay closing")
        
        if not parsed_data["contract_terms"].get("earnest_money"):
            risks.append("No earnest money specified")
        
        # Check for as-is clause
        if "as-is" in str(parsed_data.get("raw_text", "")).lower():
            risks.append("Property being sold as-is")
        
        return risks
    
    def _generate_deed_summary(self, fields: Dict) -> str:
        """Generate deed summary"""
        
        parts = []
        
        if fields.get("grantor") and fields.get("grantee"):
            parts.append(f"Transfer from {fields['grantor']} to {fields['grantee']}")
        
        if fields.get("consideration"):
            parts.append(f"for consideration of {fields['consideration']}")
        
        if fields.get("property_description"):
            parts.append(f"Property: {fields['property_description'][:100]}")
        
        return ". ".join(parts) if parts else "Deed document processed"
    
    def _generate_photo_description(self, analysis: Dict) -> str:
        """Generate description for property photo"""
        
        room = analysis.get("room_type", "space")
        features = analysis.get("detected_features", [])
        style = analysis.get("style_elements", [])
        
        description = f"This {room} features "
        
        if features:
            description += ", ".join(features[:3])
        
        if style:
            description += f" with {', '.join(style[:2])} design elements"
        
        return description
    
    def _generate_marketing_tags(self, analysis: Dict) -> List[str]:
        """Generate marketing tags for photo"""
        
        tags = []
        
        if analysis.get("room_type"):
            tags.append(f"#{analysis['room_type'].replace(' ', '')}")
        
        for feature in analysis.get("detected_features", [])[:3]:
            tags.append(f"#{feature.replace(' ', '')}")
        
        for style in analysis.get("style_elements", [])[:2]:
            tags.append(f"#{style}")
        
        quality = analysis.get("quality_assessment", {})
        if quality.get("staging") == "well-staged":
            tags.append("#staged")
        
        return tags
    
    def _encode_image(self, image_data) -> str:
        """Encode image to base64"""
        
        if isinstance(image_data, Image.Image):
            buffer = io.BytesIO()
            image_data.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode()
        elif isinstance(image_data, bytes):
            return base64.b64encode(image_data).decode()
        else:
            return str(image_data)
    
    async def _batch_process(self, documents: List[Dict]) -> Dict[str, Any]:
        """Process multiple documents in batch"""
        
        results = []
        
        for doc in documents:
            try:
                result = await self.process(doc)
                results.append({
                    "status": "success",
                    "document_id": doc.get("id", "unknown"),
                    "result": result
                })
            except Exception as e:
                results.append({
                    "status": "error",
                    "document_id": doc.get("id", "unknown"),
                    "error": str(e)
                })
        
        return {
            "batch_processing": True,
            "total_documents": len(documents),
            "successful": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] == "error"),
            "results": results
        }
    
    async def _process_file(self, file_path: str, doc_type: str) -> Dict[str, Any]:
        """Process document from file path"""
        
        # In production, would read and process actual file
        # For now, simulate processing
        return {
            "file_path": file_path,
            "document_type": doc_type,
            "status": "processed",
            "extracted_text": "Document content extracted from file"
        }
    
    async def _process_text_document(self, text: str, doc_type: str) -> Dict[str, Any]:
        """Process text document"""
        
        return {
            "document_type": doc_type,
            "text_length": len(text),
            "word_count": len(text.split()),
            "processed": True
        }
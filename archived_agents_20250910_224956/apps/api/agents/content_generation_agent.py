"""
Content Generation Agent using Qwen2.5-1.5B-Instruct
Generates property descriptions, market reports, and investment analyses
"""

from typing import Dict, Any, List, Optional
import aiohttp
import os
from datetime import datetime
from .base_agent import BaseAgent

class ContentGenerationAgent(BaseAgent):
    """Agent for generating property-related content"""
    
    def __init__(self):
        super().__init__(
            agent_id="content_generation",
            name="Content Generation Agent",
            description="Generate property descriptions and reports using Qwen2.5"
        )
        self.model_id = "Qwen/Qwen2.5-1.5B-Instruct"
        self.api_token = os.getenv("HUGGINGFACE_API_TOKEN", "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")
        self.templates = self._load_templates()
        self.generation_history = []
        
    def _load_templates(self) -> Dict[str, str]:
        """Load content generation templates"""
        return {
            "luxury_listing": """Create an elegant, sophisticated property listing for a luxury {property_type}.
                Address: {address}
                Features: {features}
                Price: {price}
                
                Emphasize exclusivity, premium amenities, and investment value.
                Listing:""",
            
            "professional_listing": """Write a professional real estate listing for:
                Property Type: {property_type}
                Location: {address}
                Specifications: {bedrooms} bedrooms, {bathrooms} bathrooms, {sqft} sq ft
                Key Features: {features}
                
                Description:""",
            
            "investment_analysis": """Provide an investment analysis for:
                Property: {address}
                Purchase Price: {price}
                Market Trends: {market_data}
                Comparable Sales: {comparables}
                
                Analysis should include ROI projections, market outlook, and investment recommendation.
                Analysis:""",
            
            "market_report": """Generate a comprehensive market report for {location}:
                Property Type: {property_type}
                Time Period: {period}
                Market Data: {market_data}
                
                Include trends, predictions, and actionable insights.
                Report:""",
            
            "email_template": """Compose a professional email to {recipient_type} regarding:
                Property: {address}
                Purpose: {purpose}
                Key Points: {key_points}
                
                Email:""",
            
            "social_media": """Create an engaging social media post for:
                Property: {address}
                Platform: {platform}
                Target Audience: {audience}
                Call to Action: {cta}
                
                Post:"""
        }
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate content generation request"""
        if "test" in input_data:
            return True
        return "content_type" in input_data or "property_data" in input_data
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate requested content"""
        
        content_type = input_data.get("content_type", "listing")
        property_data = input_data.get("property_data", {})
        style = input_data.get("style", "professional")
        
        self.logger.info(f"Generating {content_type} content with style: {style}")
        
        # Route to appropriate generation method
        if content_type == "listing":
            return await self._generate_listing(property_data, style)
        elif content_type == "investment_analysis":
            return await self._generate_investment_analysis(property_data)
        elif content_type == "market_report":
            return await self._generate_market_report(input_data)
        elif content_type == "email":
            return await self._generate_email(input_data)
        elif content_type == "social_media":
            return await self._generate_social_media(input_data)
        elif content_type == "batch":
            return await self._batch_generate(input_data)
        else:
            return await self._generate_custom(input_data)
    
    async def _generate_listing(self, property_data: Dict[str, Any], style: str) -> Dict[str, Any]:
        """Generate property listing description"""
        
        # Select template based on style
        template_key = f"{style}_listing" if f"{style}_listing" in self.templates else "professional_listing"
        template = self.templates[template_key]
        
        # Prepare data for template
        features = property_data.get("features", [])
        features_text = ", ".join(features) if features else "modern amenities"
        
        prompt = template.format(
            property_type=property_data.get("property_type", "residential property"),
            address=property_data.get("address", "Prime location"),
            bedrooms=property_data.get("bedrooms", 3),
            bathrooms=property_data.get("bathrooms", 2),
            sqft=property_data.get("sqft", 2000),
            features=features_text,
            price=f"${property_data.get('price', 500000):,}" if property_data.get('price') else "Competitive pricing"
        )
        
        # Generate content
        generated = await self._call_generation_api(prompt)
        
        # Post-process the generated content
        listing = self._post_process_listing(generated, property_data)
        
        # Generate additional content
        highlights = self._extract_highlights(listing)
        seo_keywords = self._generate_seo_keywords(property_data)
        
        result = {
            "content_type": "listing",
            "style": style,
            "listing": listing,
            "highlights": highlights,
            "seo_keywords": seo_keywords,
            "word_count": len(listing.split()),
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in history
        self.generation_history.append(result)
        
        return result
    
    async def _generate_investment_analysis(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate investment analysis report"""
        
        # Prepare market data
        market_data = property_data.get("market_data", {})
        comparables = property_data.get("comparables", [])
        
        prompt = self.templates["investment_analysis"].format(
            address=property_data.get("address", "Investment property"),
            price=f"${property_data.get('price', 0):,}",
            market_data=self._format_market_data(market_data),
            comparables=self._format_comparables(comparables)
        )
        
        # Generate analysis
        analysis = await self._call_generation_api(prompt)
        
        # Calculate investment metrics
        metrics = self._calculate_investment_metrics(property_data)
        
        return {
            "content_type": "investment_analysis",
            "analysis": analysis,
            "metrics": metrics,
            "recommendation": self._generate_recommendation(metrics),
            "risk_assessment": self._assess_risk(property_data, market_data),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _generate_market_report(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate market analysis report"""
        
        location = input_data.get("location", "Market area")
        period = input_data.get("period", "Last 12 months")
        market_data = input_data.get("market_data", {})
        
        prompt = self.templates["market_report"].format(
            location=location,
            property_type=input_data.get("property_type", "residential"),
            period=period,
            market_data=self._format_market_data(market_data)
        )
        
        report = await self._call_generation_api(prompt)
        
        # Generate charts data
        chart_data = self._prepare_chart_data(market_data)
        
        return {
            "content_type": "market_report",
            "location": location,
            "period": period,
            "report": report,
            "chart_data": chart_data,
            "key_insights": self._extract_insights(report),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _generate_email(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate email content"""
        
        recipient_type = input_data.get("recipient_type", "potential buyer")
        purpose = input_data.get("purpose", "property inquiry")
        
        prompt = self.templates["email_template"].format(
            recipient_type=recipient_type,
            address=input_data.get("address", ""),
            purpose=purpose,
            key_points=", ".join(input_data.get("key_points", []))
        )
        
        email_content = await self._call_generation_api(prompt)
        
        # Generate subject line
        subject = await self._generate_subject_line(purpose, input_data.get("address", ""))
        
        return {
            "content_type": "email",
            "subject": subject,
            "body": email_content,
            "recipient_type": recipient_type,
            "purpose": purpose,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _generate_social_media(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate social media content"""
        
        platform = input_data.get("platform", "instagram")
        audience = input_data.get("audience", "home buyers")
        
        prompt = self.templates["social_media"].format(
            address=input_data.get("address", "Featured property"),
            platform=platform,
            audience=audience,
            cta=input_data.get("cta", "Schedule a viewing today!")
        )
        
        post_content = await self._call_generation_api(prompt)
        
        # Generate hashtags
        hashtags = self._generate_hashtags(input_data, platform)
        
        # Adjust for platform limits
        post_content = self._adjust_for_platform(post_content, platform)
        
        return {
            "content_type": "social_media",
            "platform": platform,
            "post": post_content,
            "hashtags": hashtags,
            "character_count": len(post_content),
            "audience": audience,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _batch_generate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate multiple content pieces in batch"""
        
        properties = input_data.get("properties", [])
        content_types = input_data.get("content_types", ["listing"])
        
        results = []
        
        for prop in properties:
            for content_type in content_types:
                request = {
                    "content_type": content_type,
                    "property_data": prop
                }
                result = await self.process(request)
                results.append(result)
        
        return {
            "content_type": "batch",
            "total_generated": len(results),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _generate_custom(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate custom content based on prompt"""
        
        prompt = input_data.get("prompt", "")
        if not prompt:
            return {"error": "No prompt provided for custom generation"}
        
        generated = await self._call_generation_api(prompt)
        
        return {
            "content_type": "custom",
            "prompt": prompt,
            "generated": generated,
            "word_count": len(generated.split()),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _call_generation_api(self, prompt: str) -> str:
        """Call Qwen model for text generation"""
        
        url = f"https://api-inference.huggingface.co/models/{self.model_id}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 500,
                "temperature": 0.8,
                "top_p": 0.9,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        if isinstance(result, list) and len(result) > 0:
                            return result[0].get("generated_text", "")
                        return str(result)
                    else:
                        self.logger.warning(f"Generation API failed: {response.status}")
                        return self._fallback_generation(prompt)
        except Exception as e:
            self.logger.error(f"Error calling generation API: {str(e)}")
            return self._fallback_generation(prompt)
    
    def _fallback_generation(self, prompt: str) -> str:
        """Fallback content generation"""
        if "listing" in prompt.lower():
            return "Beautiful property featuring modern amenities and excellent location. This home offers comfortable living spaces and is perfect for families or investors. Contact us for more details and to schedule a viewing."
        elif "investment" in prompt.lower():
            return "This property presents a solid investment opportunity with strong rental potential and appreciation prospects. Market analysis indicates positive growth trends in the area."
        else:
            return "Professional real estate content tailored to your needs. Contact us for personalized service and expert guidance."
    
    def _post_process_listing(self, generated: str, property_data: Dict) -> str:
        """Post-process generated listing"""
        
        # Ensure key information is included
        if property_data.get("address") and property_data["address"] not in generated:
            generated = f"Located at {property_data['address']}. {generated}"
        
        # Add call to action if missing
        if "contact" not in generated.lower() and "schedule" not in generated.lower():
            generated += " Contact us today to schedule a private viewing."
        
        # Clean up any artifacts
        generated = generated.replace("Listing:", "").replace("Description:", "").strip()
        
        return generated
    
    def _extract_highlights(self, listing: str) -> List[str]:
        """Extract key highlights from listing"""
        highlights = []
        
        # Extract sentences with key terms
        sentences = listing.split(".")
        key_terms = ["featuring", "offers", "includes", "boasts", "perfect for", "ideal"]
        
        for sentence in sentences:
            if any(term in sentence.lower() for term in key_terms):
                highlights.append(sentence.strip())
        
        return highlights[:5]  # Return top 5 highlights
    
    def _generate_seo_keywords(self, property_data: Dict) -> List[str]:
        """Generate SEO keywords for property"""
        keywords = []
        
        # Location-based keywords
        if property_data.get("city"):
            keywords.extend([
                f"{property_data['city']} real estate",
                f"homes for sale {property_data['city']}",
                f"{property_data['city']} properties"
            ])
        
        # Property type keywords
        prop_type = property_data.get("property_type", "home")
        keywords.extend([
            f"{prop_type} for sale",
            f"buy {prop_type}",
            f"{prop_type} listing"
        ])
        
        # Feature keywords
        for feature in property_data.get("features", []):
            keywords.append(feature.lower())
        
        return keywords
    
    def _calculate_investment_metrics(self, property_data: Dict) -> Dict[str, Any]:
        """Calculate investment metrics"""
        price = property_data.get("price", 0)
        rent = property_data.get("estimated_rent", price * 0.005)  # 0.5% rule
        
        return {
            "cap_rate": (rent * 12 / price * 100) if price > 0 else 0,
            "cash_on_cash": ((rent * 12 - price * 0.08) / (price * 0.2) * 100) if price > 0 else 0,
            "monthly_cashflow": rent - (price * 0.008),  # Assuming expenses
            "roi_1_year": ((rent * 12) / price * 100) if price > 0 else 0
        }
    
    def _generate_recommendation(self, metrics: Dict) -> str:
        """Generate investment recommendation based on metrics"""
        cap_rate = metrics.get("cap_rate", 0)
        
        if cap_rate > 8:
            return "Strong Buy - Excellent investment opportunity"
        elif cap_rate > 6:
            return "Buy - Good investment potential"
        elif cap_rate > 4:
            return "Hold - Moderate investment potential"
        else:
            return "Consider alternatives - Limited investment returns"
    
    def _assess_risk(self, property_data: Dict, market_data: Dict) -> str:
        """Assess investment risk"""
        # Simple risk assessment logic
        age = datetime.now().year - property_data.get("year_built", datetime.now().year)
        
        if age > 30:
            return "Moderate to High - Property may require significant maintenance"
        elif age > 15:
            return "Moderate - Standard maintenance expected"
        else:
            return "Low - Newer property with minimal maintenance needs"
    
    def _format_market_data(self, market_data: Dict) -> str:
        """Format market data for prompts"""
        if not market_data:
            return "Current market conditions"
        
        parts = []
        for key, value in market_data.items():
            parts.append(f"{key}: {value}")
        
        return ", ".join(parts)
    
    def _format_comparables(self, comparables: List) -> str:
        """Format comparable properties"""
        if not comparables:
            return "No direct comparables available"
        
        return f"{len(comparables)} comparable properties analyzed"
    
    def _prepare_chart_data(self, market_data: Dict) -> Dict:
        """Prepare data for charts"""
        return {
            "price_trend": market_data.get("price_trend", []),
            "inventory": market_data.get("inventory", []),
            "days_on_market": market_data.get("days_on_market", [])
        }
    
    def _extract_insights(self, report: str) -> List[str]:
        """Extract key insights from report"""
        insights = []
        
        # Look for conclusion sentences
        sentences = report.split(".")
        for sentence in sentences:
            if any(word in sentence.lower() for word in ["trend", "growth", "decline", "opportunity", "risk"]):
                insights.append(sentence.strip())
        
        return insights[:3]
    
    async def _generate_subject_line(self, purpose: str, address: str) -> str:
        """Generate email subject line"""
        if "inquiry" in purpose.lower():
            return f"Property Inquiry: {address}"
        elif "offer" in purpose.lower():
            return f"Offer Submitted: {address}"
        elif "showing" in purpose.lower():
            return f"Showing Request: {address}"
        else:
            return f"Re: {address}"
    
    def _generate_hashtags(self, property_data: Dict, platform: str) -> List[str]:
        """Generate platform-specific hashtags"""
        hashtags = ["#realestate", "#property", "#forsale"]
        
        if property_data.get("city"):
            hashtags.append(f"#{property_data['city'].replace(' ', '')}realestate")
        
        if property_data.get("property_type"):
            hashtags.append(f"#{property_data['property_type'].replace(' ', '')}")
        
        if platform == "instagram":
            hashtags.extend(["#homesofinstagram", "#dreamhome", "#househunting"])
        elif platform == "twitter":
            hashtags = hashtags[:5]  # Limit for Twitter
        
        return hashtags
    
    def _adjust_for_platform(self, content: str, platform: str) -> str:
        """Adjust content for platform limits"""
        limits = {
            "twitter": 280,
            "instagram": 2200,
            "facebook": 63206,
            "linkedin": 3000
        }
        
        limit = limits.get(platform, 1000)
        
        if len(content) > limit:
            content = content[:limit-3] + "..."
        
        return content
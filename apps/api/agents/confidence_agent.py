"""
Confidence-Based Agent System
Implements confidence thresholds and human escalation based on arxiv:2504.15228
"""

from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime
from .base_agent import BaseAgent, AgentStatus, AgentPriority

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence levels for agent decisions"""
    VERY_LOW = 0.2    # < 20% - Always escalate
    LOW = 0.4         # 20-40% - Escalate for important operations
    MEDIUM = 0.6      # 40-60% - Escalate for high-risk operations
    HIGH = 0.8        # 60-80% - Proceed with caution
    VERY_HIGH = 0.95  # > 80% - Proceed with confidence


@dataclass
class Decision:
    """Represents an agent decision with confidence"""
    action: str
    confidence: float
    reasoning: str
    risk_level: str
    requires_human: bool
    data: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ConfidenceThreshold:
    """Manages confidence thresholds for different operation types"""
    
    # Default thresholds for different operation types
    THRESHOLDS = {
        "read": 0.5,           # Low risk - reading data
        "write": 0.7,          # Medium risk - writing data
        "delete": 0.9,         # High risk - deleting data
        "financial": 0.85,     # High risk - financial operations
        "property_sale": 0.9,  # Very high risk - property transactions
        "bulk_operation": 0.8, # High risk - operations affecting multiple records
        "system_config": 0.95  # Critical - system configuration changes
    }
    
    @classmethod
    def get_threshold(cls, operation_type: str) -> float:
        """Get confidence threshold for operation type"""
        return cls.THRESHOLDS.get(operation_type, 0.7)  # Default to 0.7
    
    @classmethod
    def requires_escalation(cls, confidence: float, operation_type: str) -> bool:
        """Check if operation requires human escalation"""
        threshold = cls.get_threshold(operation_type)
        return confidence < threshold


class ConfidenceAgent(BaseAgent):
    """
    Enhanced agent with confidence scoring and human escalation
    Following principles from Self-Improving Agent paper
    """
    
    def __init__(self, agent_id: str, name: str, description: str):
        super().__init__(agent_id, name, description)
        self.confidence_history: List[Decision] = []
        self.escalation_callback: Optional[Callable] = None
        self.confidence_metrics = {
            "total_decisions": 0,
            "escalated_decisions": 0,
            "avg_confidence": 0.0,
            "confidence_trend": []  # Track last 10 decisions
        }
        
    def set_escalation_callback(self, callback: Callable):
        """Set callback for human escalation"""
        self.escalation_callback = callback
        logger.info(f"Escalation callback set for agent {self.agent_id}")
        
    async def calculate_confidence(self, 
                                   input_data: Dict[str, Any], 
                                   context: Dict[str, Any]) -> float:
        """
        Calculate confidence score for a decision
        Returns value between 0.0 and 1.0
        """
        confidence = 1.0
        
        # Factor 1: Data completeness
        required_fields = context.get("required_fields", [])
        if required_fields:
            present_fields = sum(1 for field in required_fields if field in input_data)
            data_completeness = present_fields / len(required_fields)
            confidence *= data_completeness
            logger.debug(f"Data completeness: {data_completeness:.2f}")
        
        # Factor 2: Historical success rate
        if self.metrics["tasks_processed"] > 0:
            historical_success = self.metrics["success_rate"]
            confidence *= (0.5 + 0.5 * historical_success)  # Weight historical success
            logger.debug(f"Historical success factor: {historical_success:.2f}")
        
        # Factor 3: Input validation strength
        validation_score = await self.validate_input_with_score(input_data)
        confidence *= validation_score
        logger.debug(f"Validation score: {validation_score:.2f}")
        
        # Factor 4: Pattern recognition
        if self.confidence_history:
            similar_decisions = self._find_similar_decisions(input_data)
            if similar_decisions:
                avg_past_confidence = sum(d.confidence for d in similar_decisions) / len(similar_decisions)
                confidence *= (0.7 + 0.3 * avg_past_confidence)
                logger.debug(f"Pattern recognition factor: {avg_past_confidence:.2f}")
        
        # Factor 5: Risk assessment
        risk_factor = self._assess_risk(input_data, context)
        confidence *= (1.0 - risk_factor * 0.3)  # Higher risk reduces confidence
        logger.debug(f"Risk factor: {risk_factor:.2f}")
        
        # Ensure confidence is within bounds
        confidence = max(0.0, min(1.0, confidence))
        
        logger.info(f"Calculated confidence: {confidence:.2f} for agent {self.agent_id}")
        return confidence
        
    async def validate_input_with_score(self, input_data: Dict[str, Any]) -> float:
        """
        Validate input and return a score (0.0 to 1.0)
        Override this in derived classes for specific validation
        """
        score = 1.0
        
        # Check for required fields
        if not input_data:
            return 0.0
            
        # Check for valid data types
        for key, value in input_data.items():
            if value is None:
                score *= 0.9
            elif isinstance(value, str) and not value.strip():
                score *= 0.95
                
        return score
        
    def _find_similar_decisions(self, input_data: Dict[str, Any]) -> List[Decision]:
        """Find similar past decisions for pattern matching"""
        similar = []
        
        for decision in self.confidence_history[-10:]:  # Check last 10 decisions
            similarity = self._calculate_similarity(input_data, decision.data)
            if similarity > 0.7:  # 70% similarity threshold
                similar.append(decision)
                
        return similar
        
    def _calculate_similarity(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> float:
        """Calculate similarity between two data sets"""
        if not data1 or not data2:
            return 0.0
            
        common_keys = set(data1.keys()) & set(data2.keys())
        if not common_keys:
            return 0.0
            
        matches = sum(1 for key in common_keys if data1[key] == data2[key])
        return matches / len(common_keys)
        
    def _assess_risk(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Assess risk level of operation (0.0 = no risk, 1.0 = maximum risk)
        """
        risk = 0.0
        
        # Check operation type
        operation = context.get("operation_type", "read")
        if operation == "delete":
            risk += 0.5
        elif operation == "write":
            risk += 0.3
        elif operation in ["financial", "property_sale"]:
            risk += 0.7
            
        # Check data volume
        if context.get("bulk_operation", False):
            risk += 0.2
            
        # Check for high-value operations
        value = input_data.get("value", 0)
        if isinstance(value, (int, float)):
            if value > 100000:  # Operations over $100k
                risk += 0.3
            elif value > 50000:  # Operations over $50k
                risk += 0.2
                
        # Check for irreversible operations
        if context.get("irreversible", False):
            risk += 0.3
            
        return min(1.0, risk)
        
    async def make_decision(self, 
                            input_data: Dict[str, Any],
                            context: Dict[str, Any]) -> Decision:
        """
        Make a decision with confidence assessment
        """
        # Calculate confidence
        confidence = await self.calculate_confidence(input_data, context)
        
        # Determine operation type
        operation_type = context.get("operation_type", "read")
        
        # Check if escalation is needed
        requires_human = ConfidenceThreshold.requires_escalation(confidence, operation_type)
        
        # Assess risk
        risk_level = self._get_risk_level(self._assess_risk(input_data, context))
        
        # Create decision
        decision = Decision(
            action=context.get("action", "unknown"),
            confidence=confidence,
            reasoning=self._generate_reasoning(confidence, operation_type),
            risk_level=risk_level,
            requires_human=requires_human,
            data=input_data
        )
        
        # Log decision
        self._log_decision(decision)
        
        # Handle escalation if needed
        if requires_human:
            await self._escalate_to_human(decision, context)
            
        return decision
        
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score < 0.2:
            return "low"
        elif risk_score < 0.5:
            return "medium"
        elif risk_score < 0.8:
            return "high"
        else:
            return "critical"
            
    def _generate_reasoning(self, confidence: float, operation_type: str) -> str:
        """Generate reasoning for confidence level"""
        threshold = ConfidenceThreshold.get_threshold(operation_type)
        
        if confidence >= threshold:
            return f"Confidence {confidence:.2f} exceeds threshold {threshold:.2f} for {operation_type}"
        else:
            return f"Confidence {confidence:.2f} below threshold {threshold:.2f} for {operation_type} - escalation required"
            
    def _log_decision(self, decision: Decision):
        """Log decision and update metrics"""
        self.confidence_history.append(decision)
        
        # Update metrics
        self.confidence_metrics["total_decisions"] += 1
        if decision.requires_human:
            self.confidence_metrics["escalated_decisions"] += 1
            
        # Update average confidence
        total = self.confidence_metrics["total_decisions"]
        current_avg = self.confidence_metrics["avg_confidence"]
        self.confidence_metrics["avg_confidence"] = ((current_avg * (total - 1)) + decision.confidence) / total
        
        # Track confidence trend (last 10)
        self.confidence_metrics["confidence_trend"].append(decision.confidence)
        if len(self.confidence_metrics["confidence_trend"]) > 10:
            self.confidence_metrics["confidence_trend"].pop(0)
            
        logger.info(f"Decision logged: {decision.action} with confidence {decision.confidence:.2f}")
        
    async def _escalate_to_human(self, decision: Decision, context: Dict[str, Any]):
        """Escalate decision to human for review"""
        logger.warning(f"ESCALATION REQUIRED: {decision.action}")
        logger.warning(f"Confidence: {decision.confidence:.2f}")
        logger.warning(f"Risk Level: {decision.risk_level}")
        logger.warning(f"Reasoning: {decision.reasoning}")
        
        if self.escalation_callback:
            try:
                human_response = await self.escalation_callback(decision, context)
                logger.info(f"Human response received: {human_response}")
                return human_response
            except Exception as e:
                logger.error(f"Error in escalation callback: {e}")
                
        # If no callback or error, log for manual review
        escalation_log = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "decision": decision.__dict__,
            "context": context,
            "status": "pending_review"
        }
        
        # In production, this would write to a queue or database
        logger.critical(f"MANUAL REVIEW REQUIRED: {escalation_log}")
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process with confidence assessment
        Override this in derived classes
        """
        # Extract context from input
        context = input_data.get("context", {})
        
        # Make decision with confidence assessment
        decision = await self.make_decision(input_data, context)
        
        # Return result with confidence metadata
        return {
            "result": input_data,  # Placeholder - implement actual processing
            "confidence": decision.confidence,
            "requires_human": decision.requires_human,
            "risk_level": decision.risk_level,
            "reasoning": decision.reasoning
        }
        
    def get_confidence_report(self) -> Dict[str, Any]:
        """Get confidence metrics report"""
        return {
            "agent_id": self.agent_id,
            "confidence_metrics": self.confidence_metrics,
            "recent_decisions": [
                {
                    "action": d.action,
                    "confidence": d.confidence,
                    "risk_level": d.risk_level,
                    "requires_human": d.requires_human,
                    "timestamp": d.timestamp.isoformat()
                }
                for d in self.confidence_history[-5:]  # Last 5 decisions
            ],
            "escalation_rate": (
                self.confidence_metrics["escalated_decisions"] / 
                max(1, self.confidence_metrics["total_decisions"])
            )
        }


# Example implementation for property operations
class PropertyConfidenceAgent(ConfidenceAgent):
    """
    Property-specific agent with confidence thresholds
    """
    
    def __init__(self):
        super().__init__(
            agent_id="property_confidence",
            name="Property Confidence Agent",
            description="Handles property operations with confidence assessment"
        )
        
    async def validate_input_with_score(self, input_data: Dict[str, Any]) -> float:
        """Property-specific validation"""
        score = await super().validate_input_with_score(input_data)
        
        # Check for parcel ID
        if "parcel_id" in input_data:
            parcel_id = input_data["parcel_id"]
            if parcel_id and len(parcel_id) >= 10:
                score *= 1.0
            else:
                score *= 0.5
                
        # Check for county
        if "county" not in input_data:
            score *= 0.7  # Reduce confidence without county
            
        return score
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process property operation with confidence"""
        
        # Determine operation type based on input
        operation_type = "read"  # Default
        if input_data.get("action") == "update":
            operation_type = "write"
        elif input_data.get("action") == "delete":
            operation_type = "delete"
        elif input_data.get("value", 0) > 0:
            operation_type = "financial"
            
        # Add context
        context = {
            "operation_type": operation_type,
            "action": input_data.get("action", "query"),
            "required_fields": ["parcel_id", "county"],
            "bulk_operation": input_data.get("bulk", False),
            "irreversible": operation_type == "delete"
        }
        
        input_data["context"] = context
        
        # Process with confidence assessment
        result = await super().process(input_data)
        
        # Add property-specific processing here
        # ...
        
        return result


if __name__ == "__main__":
    # Example usage
    import asyncio
    
    async def test_confidence_agent():
        agent = PropertyConfidenceAgent()
        
        # Test with high confidence operation
        high_conf_input = {
            "parcel_id": "1234567890",
            "county": "Broward",
            "action": "query"
        }
        
        result = await agent.process(high_conf_input)
        print(f"High confidence result: {result}")
        
        # Test with low confidence operation
        low_conf_input = {
            "parcel_id": "123",  # Invalid
            "action": "delete",
            "value": 500000
        }
        
        result = await agent.process(low_conf_input)
        print(f"Low confidence result (should escalate): {result}")
        
        # Get confidence report
        report = agent.get_confidence_report()
        print(f"Confidence report: {report}")
    
    asyncio.run(test_confidence_agent())
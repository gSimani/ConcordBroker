# ConcordBroker Agent Optimization Plan
*Based on Comprehensive Audit & OpenAI Agent Principles*

## Current State Analysis

### 🔴 Critical Issues
- **73+ agents** with 42% dormant
- **4+ orchestrator implementations** causing confusion
- **Mixed languages** (Python/JS) for similar functions
- **3 different frameworks** (Custom, LangChain, LangGraph)
- **No clear agent lifecycle management**

### 🟡 Opportunities
- Strong foundation with active data pipeline agents
- Working AI chatbot integration
- Functional property search and analysis
- Good coverage of data sources

## Optimized Agent Architecture

### Phase 1: Immediate Cleanup (Week 1)

#### 1. Remove Dormant Agents
```bash
# Agents to remove/archive
apps/agents/nal_*.py (7 files)
apps/agents/filter_validation_agent.py
apps/agents/schema_migration_agent.py
apps/agents/ComprehensiveDataAnalyzer.js
apps/agents/DataFlowFixer.js
apps/api/agents/content_generation_agent.py
apps/api/agents/document_processing_agent.py
apps/api/agents/advanced_chain_optimizer.py
apps/api/agents/chain_of_thought_matcher.py
```

#### 2. Consolidate Orchestrators
Keep only ONE master orchestrator:
```python
# apps/agents/unified_orchestrator.py
class UnifiedOrchestrator:
    """Single source of truth for all agent coordination"""
    def __init__(self):
        self.agents = {}
        self.register_agents()
    
    def register_agents(self):
        # Register all active agents
        self.agents['property_search'] = PropertySearchAgent()
        self.agents['tax_deed'] = TaxDeedAgent()
        self.agents['sunbiz'] = SunbizAgent()
        self.agents['ai_chat'] = AIChatAgent()
```

### Phase 2: Implement Core Agent System (Week 2)

#### New Agent Hierarchy

```
UnifiedOrchestrator (Manager Pattern)
├── DataPipelineAgent (Single Agent)
│   ├── FloridaDataCollector (Tool)
│   ├── TaxDeedScraper (Tool)
│   ├── SunbizSync (Tool)
│   └── DatabaseWriter (Tool)
│
├── PropertyAnalysisAgent (Single Agent)
│   ├── MarketAnalyzer (Tool)
│   ├── ROICalculator (Tool)
│   ├── ComparablesFinder (Tool)
│   └── RiskAssessor (Tool)
│
├── AIAssistantAgent (Single Agent)
│   ├── NaturalLanguageParser (Tool)
│   ├── SemanticSearch (Tool)
│   ├── ResponseGenerator (Tool)
│   └── ContextManager (Tool)
│
└── MonitoringAgent (Single Agent)
    ├── HealthChecker (Tool)
    ├── AlertManager (Tool)
    ├── MetricsCollector (Tool)
    └── ErrorRecovery (Tool)
```

### Phase 3: Standardized Implementation (Week 3)

#### Base Agent Template
```python
# apps/agents/base/enhanced_agent.py
from typing import Dict, List, Any
from abc import ABC, abstractmethod
import asyncio
from enum import Enum

class AgentStatus(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    COMPLETED = "completed"

class EnhancedAgent(ABC):
    """Base class following OpenAI principles"""
    
    def __init__(self, name: str, model: str = "gpt-4"):
        self.name = name
        self.model = model
        self.tools = {}
        self.guardrails = []
        self.status = AgentStatus.IDLE
        self.confidence_threshold = 0.7
        self.max_retries = 3
        self.register_tools()
        self.setup_guardrails()
    
    @abstractmethod
    def register_tools(self):
        """Register all tools for this agent"""
        pass
    
    @abstractmethod
    def setup_guardrails(self):
        """Setup safety guardrails"""
        pass
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution loop with error handling"""
        self.status = AgentStatus.PROCESSING
        retries = 0
        
        while retries < self.max_retries:
            try:
                # Validate input
                if not self.validate_input(task):
                    raise ValueError("Invalid input")
                
                # Check guardrails
                for guardrail in self.guardrails:
                    if not guardrail.check(task):
                        return self.escalate_to_human(task, "Guardrail violation")
                
                # Process task
                result = await self.process(task)
                
                # Validate output
                if self.confidence_score(result) < self.confidence_threshold:
                    return self.escalate_to_human(task, "Low confidence")
                
                self.status = AgentStatus.COMPLETED
                return result
                
            except Exception as e:
                retries += 1
                if retries >= self.max_retries:
                    self.status = AgentStatus.ERROR
                    return self.handle_error(e, task)
    
    @abstractmethod
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Core processing logic"""
        pass
    
    def escalate_to_human(self, task: Dict, reason: str):
        """Escalate to human intervention"""
        return {
            "status": "escalated",
            "reason": reason,
            "task": task,
            "agent": self.name
        }
```

### Phase 4: Implement Guardrails (Week 4)

#### Layered Guardrail System
```python
# apps/agents/guardrails/guardrail_system.py
class GuardrailSystem:
    def __init__(self):
        self.layers = [
            InputValidation(),
            PIIFilter(),
            RateLimiter(),
            FinancialLimits(),
            SafetyClassifier(),
            OutputValidator()
        ]
    
    def check_all(self, context):
        for layer in self.layers:
            result = layer.check(context)
            if not result.passed:
                return result
        return GuardrailResult(passed=True)

class ConcordBrokerGuardrails:
    # Property-specific guardrails
    MAX_PROPERTY_VALUE = 10_000_000
    MAX_BULK_OPERATIONS = 100
    REQUIRE_HUMAN_APPROVAL_THRESHOLD = 100_000
    
    # Data access guardrails
    REQUIRED_FIELDS = ['county', 'parcel_id']
    PII_FIELDS = ['owner_name', 'owner_address', 'ssn']
    
    # Rate limits
    MAX_API_CALLS_PER_MINUTE = 60
    MAX_DB_QUERIES_PER_SECOND = 10
```

### Phase 5: Optimized AI Chatbot Agent (Priority)

```python
# apps/agents/ai_chatbot_agent.py
class AIChatbotAgent(EnhancedAgent):
    """Optimized chatbot following OpenAI principles"""
    
    def __init__(self):
        super().__init__("AIChatbot", "gpt-4")
        self.context_window = []
        self.max_context_size = 10
    
    def register_tools(self):
        self.tools = {
            'property_search': PropertySearchTool(),
            'tax_deed_lookup': TaxDeedLookupTool(),
            'market_analysis': MarketAnalysisTool(),
            'roi_calculator': ROICalculatorTool(),
            'sunbiz_search': SunbizSearchTool(),
            'generate_report': ReportGeneratorTool()
        }
    
    def setup_guardrails(self):
        self.guardrails = [
            RelevanceClassifier(),  # Ensure on-topic
            PIIProtection(),         # Protect sensitive data
            FinancialAdviceLimit(),  # No investment advice
            ResponseLengthLimit(),   # Keep responses concise
            FactualityChecker()      # Verify claims
        ]
    
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        user_query = task['query']
        
        # 1. Parse intent
        intent = await self.parse_intent(user_query)
        
        # 2. Select appropriate tools
        selected_tools = self.select_tools(intent)
        
        # 3. Execute tool chain
        results = []
        for tool in selected_tools:
            result = await tool.execute(task)
            results.append(result)
            task['context'] = results  # Pass context forward
        
        # 4. Generate response
        response = await self.generate_response(results, user_query)
        
        # 5. Update context
        self.update_context(user_query, response)
        
        return {
            'response': response,
            'confidence': self.calculate_confidence(results),
            'sources': [r['source'] for r in results if 'source' in r]
        }
    
    async def parse_intent(self, query: str):
        """Use NLP to understand user intent"""
        prompt = f"""
        Analyze this query and identify the intent:
        Query: {query}
        
        Possible intents:
        - property_search: Looking for properties
        - tax_deed_info: Asking about tax deeds
        - market_analysis: Requesting market data
        - investment_advice: Seeking ROI/investment info
        - entity_lookup: Looking up business entities
        
        Return the primary intent and confidence score.
        """
        # Call LLM for intent classification
        return await self.llm_call(prompt)
    
    def select_tools(self, intent):
        """Select tools based on intent"""
        tool_mapping = {
            'property_search': ['property_search', 'market_analysis'],
            'tax_deed_info': ['tax_deed_lookup', 'property_search'],
            'market_analysis': ['market_analysis', 'roi_calculator'],
            'investment_advice': ['roi_calculator', 'market_analysis', 'generate_report'],
            'entity_lookup': ['sunbiz_search', 'property_search']
        }
        return [self.tools[name] for name in tool_mapping.get(intent['type'], [])]
```

## Implementation Timeline

### Week 1: Cleanup
- [ ] Archive dormant agents
- [ ] Remove duplicate orchestrators
- [ ] Document remaining agents

### Week 2: Core System
- [ ] Implement UnifiedOrchestrator
- [ ] Create EnhancedAgent base class
- [ ] Migrate priority agents to new base

### Week 3: Standardization
- [ ] Convert JS agents to Python
- [ ] Implement agent registry
- [ ] Setup dependency management

### Week 4: Guardrails & Safety
- [ ] Implement layered guardrails
- [ ] Add human escalation
- [ ] Setup monitoring

### Week 5: Testing & Optimization
- [ ] Performance testing
- [ ] Error recovery testing
- [ ] Load testing

## Success Metrics

### Performance Targets
- **Response Time**: < 2s for chatbot queries
- **Success Rate**: > 85% task completion
- **Error Rate**: < 5% system errors
- **Uptime**: > 99.5% availability

### Quality Metrics
- **Confidence Score**: Average > 0.8
- **Human Escalation**: < 10% of requests
- **User Satisfaction**: > 4.5/5 rating

### Resource Optimization
- **Agent Count**: Reduce from 73 to ~20
- **Memory Usage**: Reduce by 50%
- **CPU Usage**: Reduce by 40%
- **Maintenance Time**: Reduce by 60%

## Configuration Management

### Agent Configuration
```yaml
# config/agents.yaml
agents:
  data_pipeline:
    enabled: true
    model: gpt-3.5-turbo
    max_retries: 3
    timeout: 30s
    tools:
      - florida_data_collector
      - tax_deed_scraper
      - sunbiz_sync
    guardrails:
      - rate_limiter: 60/min
      - data_validator: strict
  
  ai_chatbot:
    enabled: true
    model: gpt-4
    max_context: 10
    confidence_threshold: 0.7
    tools:
      - property_search
      - market_analysis
      - roi_calculator
    guardrails:
      - pii_filter: enabled
      - response_limit: 500_words
      - factuality_check: enabled
```

## Monitoring Dashboard

### Key Metrics to Track
```python
# apps/monitoring/agent_dashboard.py
class AgentDashboard:
    def __init__(self):
        self.metrics = {
            'agent_health': {},
            'performance': {},
            'errors': {},
            'usage': {}
        }
    
    def track_metrics(self):
        return {
            'total_agents': self.count_active_agents(),
            'success_rate': self.calculate_success_rate(),
            'avg_response_time': self.calculate_avg_response(),
            'error_rate': self.calculate_error_rate(),
            'human_escalations': self.count_escalations(),
            'top_tools_used': self.get_top_tools(),
            'guardrail_violations': self.count_violations()
        }
```

## Continuous Improvement Process

### Weekly Review
1. Analyze agent performance metrics
2. Review error logs and patterns
3. Update instructions based on failures
4. Optimize slow-performing agents
5. Add new guardrails as needed

### Monthly Review
1. Evaluate agent architecture
2. Consider new tool additions
3. Review human escalation patterns
4. Update model selections
5. Refine confidence thresholds

## Conclusion

This optimization plan will:
- **Reduce complexity** from 73 to ~20 well-defined agents
- **Improve maintainability** with standardized patterns
- **Enhance reliability** with comprehensive guardrails
- **Boost performance** through efficient orchestration
- **Enable scalability** with modular architecture

The new system follows OpenAI's principles while addressing ConcordBroker's specific needs for property intelligence and investment analysis.
# Agent Design Principles for ConcordBroker
*Based on OpenAI's Practical Guide to Building Agents*

## Table of Contents
1. [Core Agent Architecture](#core-agent-architecture)
2. [Agent Design Patterns](#agent-design-patterns)
3. [Tool Design and Management](#tool-design-and-management)
4. [Orchestration Strategies](#orchestration-strategies)
5. [Guardrails and Safety](#guardrails-and-safety)
6. [Implementation Guidelines](#implementation-guidelines)
7. [Claude Code Rules](#claude-code-rules)

---

## Core Agent Architecture

### What is an Agent?
An agent is a system that **independently accomplishes tasks on your behalf** with these core characteristics:
- Uses an LLM to manage workflow execution and make decisions
- Has access to various tools to interact with external systems
- Operates within clearly defined guardrails
- Recognizes when workflows are complete
- Can proactively correct its actions if needed

### Three Fundamental Components

```python
# Basic Agent Structure
agent = Agent(
    name="agent_name",           # 1. Identity
    model="gpt-4o",              # 2. Model (reasoning engine)
    instructions="...",          # 3. Instructions (behavior guidelines)
    tools=[...],                 # 4. Tools (capabilities)
    guardrails=[...]            # 5. Guardrails (safety constraints)
)
```

### When to Build an Agent

Build agents for workflows that have:
1. **Complex decision-making** - Nuanced judgment, exceptions, context-sensitive decisions
2. **Difficult-to-maintain rules** - Systems with unwieldy, intricate rulesets
3. **Heavy reliance on unstructured data** - Natural language, document interpretation

---

## Agent Design Patterns

### Pattern 1: Single Agent Systems

**Best for:** Simple to moderate complexity workflows

```python
# ConcordBroker Example: Property Analysis Agent
property_agent = Agent(
    name="PropertyAnalysisAgent",
    instructions="""
    You analyze property data and provide investment insights.
    1. Retrieve property details from database
    2. Analyze market trends
    3. Calculate ROI projections
    4. Generate investment recommendations
    """,
    tools=[
        query_property_database,
        calculate_roi,
        analyze_market_trends,
        generate_report
    ]
)
```

**When to use:**
- Workflow can be handled by one decision-maker
- Tools are distinct and well-defined (<15 tools)
- Logic is relatively linear

### Pattern 2: Manager Pattern (Agents as Tools)

**Best for:** Complex workflows with specialized domains

```python
# ConcordBroker Example: Real Estate Manager Agent
manager_agent = Agent(
    name="RealEstateManager",
    instructions="Coordinate specialized agents for comprehensive property analysis",
    tools=[
        tax_deed_agent.as_tool("Analyze tax deed opportunities"),
        sunbiz_agent.as_tool("Research business entities"),
        market_agent.as_tool("Perform market analysis"),
        legal_agent.as_tool("Review legal documents")
    ]
)
```

### Pattern 3: Decentralized Pattern (Agent Handoffs)

**Best for:** Workflows with distinct phases and specialized expertise

```python
# ConcordBroker Example: Customer Service Flow
triage_agent = Agent(
    name="TriageAgent",
    instructions="Assess inquiries and route to appropriate specialist",
    handoffs=[
        property_search_agent,
        investment_advisor_agent,
        transaction_support_agent
    ]
)
```

---

## Tool Design and Management

### Three Types of Tools

#### 1. Data Tools (Information Retrieval)
```python
# ConcordBroker Examples
@function_tool
def query_tax_deeds(status="upcoming", county="Broward"):
    """Retrieve tax deed auction data"""
    return supabase.table('tax_deed_bidding_items').select('*').eq('status', status).execute()

@function_tool  
def search_sunbiz(entity_name):
    """Search Florida business entities"""
    return sunbiz_api.search(entity_name)
```

#### 2. Action Tools (System Interactions)
```python
# ConcordBroker Examples
@function_tool
def update_property_tracking(property_id, status):
    """Update property tracking status"""
    return supabase.table('tracked_properties').update({'status': status}).eq('id', property_id).execute()

@function_tool
def send_alert(user_id, message):
    """Send notification to user"""
    return notification_service.send(user_id, message)
```

#### 3. Orchestration Tools (Agent Coordination)
```python
# Agents as tools for other agents
research_agent.as_tool(
    tool_name="deep_research",
    tool_description="Perform comprehensive property research"
)
```

### Tool Design Best Practices

1. **Standardized Definitions** - Consistent naming, clear parameters, detailed descriptions
2. **Reusability** - Design tools to work across multiple agents
3. **Version Management** - Track tool versions and changes
4. **Error Handling** - Graceful failures with informative messages
5. **Risk Assessment** - Classify tools by risk level (low/medium/high)

---

## Orchestration Strategies

### Execution Loop Pattern
Every agent needs a "run" loop that:
1. Processes input
2. Makes decisions
3. Calls tools
4. Evaluates results
5. Determines if task is complete
6. Returns output or continues

```python
# Basic execution pattern
async def run_agent(agent, input_message):
    while not task_complete:
        # 1. Process current state
        decision = agent.decide(context)
        
        # 2. Execute tool if needed
        if decision.requires_tool:
            result = await execute_tool(decision.tool, decision.params)
            context.update(result)
        
        # 3. Check completion
        if agent.is_complete(context):
            task_complete = True
            
        # 4. Safety check
        if iterations > MAX_ITERATIONS:
            return escalate_to_human()
    
    return final_output
```

### Multi-Agent Coordination

#### Sequential Processing
```python
# ConcordBroker: Property acquisition flow
flow = [
    search_agent,      # Find properties
    analysis_agent,    # Analyze opportunities
    valuation_agent,   # Calculate values
    decision_agent     # Make recommendations
]

for agent in flow:
    result = await agent.run(context)
    context.update(result)
```

#### Parallel Processing
```python
# ConcordBroker: Comprehensive property analysis
async def analyze_property(property_id):
    tasks = [
        tax_assessment_agent.analyze(property_id),
        market_comp_agent.analyze(property_id),
        sunbiz_entity_agent.analyze(property_id),
        permit_history_agent.analyze(property_id)
    ]
    results = await asyncio.gather(*tasks)
    return synthesize_results(results)
```

---

## Guardrails and Safety

### Layered Defense Strategy

```python
# ConcordBroker guardrail implementation
class PropertyDataGuardrails:
    def __init__(self):
        self.validators = [
            self.check_pii_filter,
            self.validate_property_id,
            self.check_data_access_permissions,
            self.validate_financial_limits,
            self.detect_suspicious_patterns
        ]
    
    async def validate(self, input_data, context):
        for validator in self.validators:
            result = await validator(input_data, context)
            if not result.is_safe:
                return GuardrailViolation(result.reason)
        return GuardrailPassed()
```

### Types of Guardrails

1. **Input Validation**
   - PII filtering
   - SQL injection prevention
   - Input length limits
   - Format validation

2. **Business Logic Guards**
   - Transaction limits
   - Rate limiting
   - Access control
   - Workflow state validation

3. **Output Validation**
   - Data accuracy checks
   - Consistency validation
   - Compliance verification

4. **Safety Classifiers**
   - Relevance checking
   - Jailbreak detection
   - Harmful content filtering

### Human-in-the-Loop Triggers

```python
# ConcordBroker: When to escalate to humans
ESCALATION_TRIGGERS = {
    'high_value_transaction': lambda amt: amt > 100000,
    'suspicious_activity': lambda score: score > 0.8,
    'repeated_failures': lambda count: count > 3,
    'sensitive_operation': lambda op: op in ['delete_all', 'transfer_ownership'],
    'low_confidence': lambda conf: conf < 0.6
}
```

---

## Implementation Guidelines

### 1. Start Simple, Iterate
```python
# Phase 1: Single agent with basic tools
basic_agent = Agent(
    name="PropertySearchAgent",
    tools=[search_properties, get_details]
)

# Phase 2: Add more capabilities
enhanced_agent = Agent(
    name="PropertySearchAgent",
    tools=[search_properties, get_details, analyze_market, calculate_roi]
)

# Phase 3: Multi-agent system
system = MultiAgentSystem([
    search_agent,
    analysis_agent,
    recommendation_agent
])
```

### 2. Instruction Engineering

**Best Practices:**
- Use existing documents (SOPs, policies, scripts)
- Break down complex tasks into steps
- Define clear actions for each step
- Capture edge cases explicitly
- Use templates for similar patterns

```python
# ConcordBroker instruction template
PROPERTY_ANALYSIS_TEMPLATE = """
You are analyzing property {property_id} in {county} County.

Step 1: Retrieve property details
- Get tax assessment data
- Fetch sales history
- Check permit records

Step 2: Analyze market conditions
- Compare with similar properties
- Review recent sales in area
- Calculate price trends

Step 3: Identify opportunities
- Flag undervalued properties
- Note improvement potential
- Check for distressed indicators

Step 4: Generate recommendation
- Summarize findings
- Provide investment score
- List key risks and opportunities

If property data is incomplete: {incomplete_data_handler}
If market data unavailable: {no_market_data_handler}
"""
```

### 3. Model Selection Strategy

```python
# ConcordBroker model selection by task
MODEL_SELECTION = {
    'simple_search': 'gpt-3.5-turbo',        # Fast, cheap
    'data_extraction': 'gpt-4-turbo',        # Accurate parsing
    'complex_analysis': 'gpt-4o',            # Advanced reasoning
    'document_review': 'claude-3-opus',      # Long context
    'quick_classification': 'gpt-3.5-turbo', # Speed priority
}
```

### 4. Testing and Evaluation

```python
# ConcordBroker agent testing framework
class AgentTestSuite:
    def __init__(self, agent):
        self.agent = agent
        self.test_cases = []
        
    def test_happy_path(self):
        """Test normal workflow execution"""
        pass
        
    def test_edge_cases(self):
        """Test boundary conditions"""
        pass
        
    def test_error_handling(self):
        """Test failure scenarios"""
        pass
        
    def test_guardrails(self):
        """Test safety mechanisms"""
        pass
        
    def test_performance(self):
        """Test speed and resource usage"""
        pass
```

---

## Claude Code Rules

### PERMANENT RULES FOR CLAUDE CODE IN CONCORDBROKER

```markdown
# CLAUDE CODE OPERATIONAL RULES
# These rules MUST be followed in all interactions

## 1. AGENT DESIGN PRINCIPLES
- Always start with single-agent systems before considering multi-agent architectures
- Use the manager pattern when coordinating >3 specialized domains
- Implement guardrails BEFORE deploying any agent to production
- Every agent MUST have clear success/failure conditions

## 2. TOOL DEVELOPMENT STANDARDS
- Tools must be atomic (do one thing well)
- Tools must have comprehensive error handling
- Tools must be versioned and documented
- Risk assessment required for all action tools
- Data tools should cache results when appropriate

## 3. SAFETY AND GUARDRAILS
- NEVER expose PII without explicit user consent
- ALWAYS validate inputs before database operations
- Implement rate limiting on all external API calls
- Log all high-risk operations for audit
- Escalate to human when confidence < 70%

## 4. CONCORDBROKER SPECIFIC RULES

### Data Access
- Property data queries must include county filter
- Sunbiz searches require entity name or ID
- Tax deed queries default to 'upcoming' status
- Always verify parcel IDs format before queries

### Workflow Standards
- Property analysis requires minimum 3 data sources
- Investment recommendations need ROI calculation
- Market comparisons use 6-month window
- Alert users for properties with >20% value change

### Code Patterns
```python
# Standard agent initialization
agent = Agent(
    name="ConcordBroker_{purpose}",
    model=MODEL_SELECTION[complexity_level],
    instructions=load_template(workflow_type),
    tools=get_tools_for_workflow(workflow_type),
    guardrails=STANDARD_GUARDRAILS + workflow_specific_guards
)

# Standard error handling
try:
    result = await agent.execute(task)
except GuardrailViolation as e:
    log_violation(e)
    return escalate_to_human(task, e)
except ToolError as e:
    return agent.retry_with_fallback(task, e)
```

## 5. DEVELOPMENT WORKFLOW
1. Define success criteria
2. Create minimal agent
3. Add tools incrementally
4. Implement guardrails
5. Test with real data
6. Monitor and iterate

## 6. MONITORING AND MAINTENANCE
- Track agent success rates
- Monitor tool usage patterns
- Review guardrail violations weekly
- Update instructions based on failures
- Maintain tool version compatibility

## 7. PROHIBITED ACTIONS
- NEVER hardcode credentials
- NEVER bypass guardrails
- NEVER auto-approve financial transactions
- NEVER delete data without backup
- NEVER expose internal system details

## 8. REQUIRED DOCUMENTATION
Every agent must have:
- Purpose statement
- Workflow diagram
- Tool dependencies
- Guardrail specifications
- Test coverage report
- Deployment checklist
```

---

## Practical Examples for ConcordBroker

### Example 1: Tax Deed Auction Agent

```python
class TaxDeedAuctionAgent:
    def __init__(self):
        self.agent = Agent(
            name="TaxDeedAuctionSpecialist",
            model="gpt-4o",
            instructions="""
            You help users identify and analyze tax deed auction opportunities.
            
            Workflow:
            1. Search upcoming auctions by criteria
            2. Analyze property fundamentals
            3. Calculate potential ROI
            4. Identify risks and opportunities
            5. Generate investment recommendation
            
            Always verify:
            - Property has clear title
            - No environmental issues
            - Accurate tax assessment
            - Market comparables available
            """,
            tools=[
                search_tax_deeds,
                get_property_details,
                calculate_roi,
                check_title_status,
                analyze_comparables,
                generate_report
            ],
            guardrails=[
                ValidatePropertyID(),
                CheckDataPermissions(),
                FinancialLimits(max_bid=500000),
                RequireHumanApproval(threshold=100000)
            ]
        )
```

### Example 2: Intelligent Property Search

```python
class SmartPropertySearch:
    def __init__(self):
        self.search_agent = Agent(
            name="PropertySearchAssistant",
            model="gpt-4-turbo",
            instructions="""
            Help users find properties matching their investment criteria.
            Understand natural language queries and translate to database filters.
            """,
            tools=[natural_language_to_sql, execute_search, rank_results]
        )
        
        self.analysis_agent = Agent(
            name="PropertyAnalyst",
            model="gpt-4o",
            instructions="Analyze search results and provide insights",
            tools=[analyze_properties, identify_opportunities, create_summary]
        )
    
    async def search(self, user_query):
        # Parse user intent
        search_params = await self.search_agent.parse_query(user_query)
        
        # Execute search
        results = await self.search_agent.search(search_params)
        
        # Analyze results
        insights = await self.analysis_agent.analyze(results)
        
        return {
            'properties': results,
            'insights': insights,
            'recommendations': self.generate_recommendations(results, insights)
        }
```

---

## Conclusion

Building effective agents requires:
1. **Clear problem definition** - Know when agents add value
2. **Incremental development** - Start simple, add complexity gradually
3. **Robust safety measures** - Layer guardrails throughout
4. **Continuous monitoring** - Track performance and iterate
5. **Human oversight** - Know when to escalate

Remember: Agents are tools to augment human capabilities, not replace human judgment. Design them to handle routine complexity while preserving human control over critical decisions.
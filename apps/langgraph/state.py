"""
State Schemas for LangGraph Workflows
Define the state structure for different workflows
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field

class PropertySearchState(TypedDict):
    """State for property search workflow"""
    # Input
    query: str
    filters: Dict[str, Any]
    user_id: Optional[str]
    session_id: str
    
    # Processing
    parsed_intent: Optional[str]
    extracted_entities: Optional[Dict[str, Any]]
    search_strategy: Optional[str]
    
    # Database query
    sql_query: Optional[str]
    raw_results: Optional[List[Dict]]
    
    # Enrichment
    enriched_results: Optional[List[Dict]]
    sunbiz_matches: Optional[List[Dict]]
    
    # Output
    final_results: Optional[List[Dict]]
    total_count: Optional[int]
    page: int
    page_size: int
    
    # Metadata
    execution_time: Optional[float]
    cache_hit: bool
    confidence_score: Optional[float]
    refinement_suggestions: Optional[List[str]]
    error: Optional[str]
    retry_count: int

class DataPipelineState(TypedDict):
    """State for data pipeline workflow"""
    # Input
    source_type: str  # 'florida_parcels', 'sunbiz', 'permits', etc.
    source_url: Optional[str]
    source_file: Optional[str]
    
    # Download
    download_status: Optional[str]
    downloaded_file: Optional[str]
    file_size: Optional[int]
    
    # Validation
    validation_status: Optional[str]
    validation_errors: Optional[List[Dict]]
    record_count: Optional[int]
    
    # Transformation
    transformed_data: Optional[List[Dict]]
    transformation_errors: Optional[List[str]]
    
    # Loading
    load_status: Optional[str]
    loaded_count: Optional[int]
    failed_count: Optional[int]
    
    # Metadata
    started_at: datetime
    completed_at: Optional[datetime]
    error: Optional[str]
    retry_count: int

class EntityMatchingState(TypedDict):
    """State for entity matching workflow"""
    # Input
    property_owner: str
    property_address: str
    property_city: str
    
    # Matching strategies
    exact_match_results: Optional[List[Dict]]
    fuzzy_match_results: Optional[List[Dict]]
    officer_match_results: Optional[List[Dict]]
    
    # Scoring
    match_scores: Optional[Dict[str, float]]
    best_match: Optional[Dict]
    confidence: Optional[float]
    
    # Human review
    needs_review: bool
    review_reason: Optional[str]
    reviewed_by: Optional[str]
    review_decision: Optional[str]
    
    # Output
    final_match: Optional[Dict]
    match_type: Optional[str]  # 'exact', 'fuzzy', 'officer', 'none'
    
    # Metadata
    execution_time: Optional[float]
    strategies_tried: List[str]
    error: Optional[str]

class OrchestratorState(TypedDict):
    """State for master orchestrator workflow"""
    # Workflow management
    active_workflows: Dict[str, str]  # workflow_id -> status
    scheduled_workflows: List[Dict]
    completed_workflows: List[Dict]
    
    # Agent status
    agent_statuses: Dict[str, str]
    agent_health: Dict[str, Dict]
    
    # Database status
    database_status: str
    table_statistics: Dict[str, int]
    
    # Performance metrics
    total_records_processed: int
    success_rate: float
    average_processing_time: float
    
    # Alerts
    active_alerts: List[Dict]
    resolved_alerts: List[Dict]
    
    # Metadata
    last_health_check: datetime
    uptime_hours: float
    error_log: List[Dict]

class EvaluationState(TypedDict):
    """State for evaluation workflow"""
    # Input
    dataset_name: str
    target_function: str
    evaluators: List[str]
    
    # Execution
    test_cases: List[Dict]
    predictions: List[Dict]
    
    # Evaluation
    scores: Dict[str, float]
    detailed_results: List[Dict]
    
    # Analysis
    error_analysis: Optional[Dict]
    improvement_suggestions: Optional[List[str]]
    
    # Output
    final_score: float
    pass_fail: bool
    report: Optional[str]
    
    # Metadata
    evaluation_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    model_version: str

# Pydantic models for validation
class PropertyFilter(BaseModel):
    """Validated property filter"""
    city: Optional[str] = Field(None, description="City name")
    min_value: Optional[float] = Field(None, ge=0, description="Minimum property value")
    max_value: Optional[float] = Field(None, ge=0, description="Maximum property value")
    property_type: Optional[str] = Field(None, description="Property type code")
    year_built_min: Optional[int] = Field(None, ge=1800, description="Minimum year built")
    year_built_max: Optional[int] = Field(None, le=2025, description="Maximum year built")
    owner_name: Optional[str] = Field(None, description="Property owner name")
    address: Optional[str] = Field(None, description="Property address")
    
    class Config:
        extra = "allow"  # Allow additional fields

class WorkflowConfig(BaseModel):
    """Configuration for workflow execution"""
    max_retries: int = Field(3, ge=0, le=10)
    timeout_seconds: int = Field(300, ge=10, le=3600)
    enable_caching: bool = Field(True)
    enable_streaming: bool = Field(True)
    human_in_loop: bool = Field(False)
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation continuity")
    
class WorkflowResult(BaseModel):
    """Standard result format for workflows"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float = 0.0
    workflow_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
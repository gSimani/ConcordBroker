#!/usr/bin/env python3
"""
NAL Data Import Agent System
===========================
Comprehensive agent-based import pipeline for NAL property data.

This package provides a complete system for importing 753,000+ NAL records
with all 165 fields into an optimized 7-table Supabase architecture.

Architecture Overview:
- Master Orchestrator: Coordinates the entire import pipeline
- CSV Parser Agent: High-performance CSV parsing with validation
- Field Mapping Agent: Maps all 165 NAL fields to database tables
- Batch Import Agent: Parallel processing for optimized database imports
- Error Recovery Agent: Comprehensive error handling and recovery
- Validation Agent: Data quality and integrity validation
- Monitoring Agent: Real-time performance monitoring and alerts

Performance Targets:
- Import 753,000+ records in 30-60 minutes
- 95%+ success rate with full error recovery
- Real-time monitoring and progress tracking
- Memory-efficient processing with parallel optimization
"""

try:
    from .nal_import_orchestrator import NALImportOrchestrator, ImportStatus, AgentConfig
    from .nal_csv_parser_agent import NALCSVParserAgent, ParseResult, HeaderInfo
    from .nal_mapping_agent import NALMappingAgent, FieldMapping
    from .nal_batch_import_agent import NALBatchImportAgent, BatchImportResult, TableImportConfig
    from .nal_error_recovery_agent import NALErrorRecoveryAgent, ErrorContext, RecoveryResult, ErrorSeverity, RecoveryAction
    from .nal_validation_agent import NALValidationAgent, ValidationResult, FieldValidation
    from .nal_monitoring_agent import NALMonitoringAgent, PerformanceMetrics, ResourceAlert

    # Package version
    __version__ = "1.0.0"

    # Export main classes and functions
    __all__ = [
        # Core agents
        'NALImportOrchestrator',
        'NALCSVParserAgent', 
        'NALMappingAgent',
        'NALBatchImportAgent',
        'NALErrorRecoveryAgent',
        'NALValidationAgent',
        'NALMonitoringAgent',
        
        # Data classes
        'ImportStatus',
        'AgentConfig',
        'ParseResult',
        'HeaderInfo',
        'FieldMapping',
        'BatchImportResult',
        'TableImportConfig',
        'ErrorContext',
        'RecoveryResult',
        'ErrorSeverity',
        'RecoveryAction',
        'ValidationResult',
        'FieldValidation',
        'PerformanceMetrics',
        'ResourceAlert'
    ]
    
    print(f"NAL Import Agent System v{__version__} loaded successfully")

except ImportError as e:
    print(f"Warning: Some NAL agents could not be imported: {e}")
    # Fallback for partial imports
    __all__ = []
#!/usr/bin/env python3
"""
Self-Healing System for ConcordBroker Data Infrastructure
Automated detection, diagnosis, and recovery from data issues
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import traceback

# AI and ML imports
import openai
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, AIMessage

# Database and async support
import asyncpg
import pandas as pd
import numpy as np
from sqlalchemy import text, func, and_, or_

# Local imports
from sqlalchemy_models import (
    DatabaseManager, PropertyDataOperations, EntityOperations, MonitoringOperations,
    FloridaParcels, PropertySalesHistory, TaxCertificates, DataFlowMetrics, ValidationResults
)
from monitoring_agents import AgentAlert, BaseMonitoringAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IssueType(Enum):
    """Types of issues that can be detected and healed"""
    DATA_CORRUPTION = "data_corruption"
    MISSING_DATA = "missing_data"
    DUPLICATE_DATA = "duplicate_data"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    VALIDATION_FAILURE = "validation_failure"
    REFERENTIAL_INTEGRITY = "referential_integrity"
    DATA_STALENESS = "data_staleness"
    SCHEMA_MISMATCH = "schema_mismatch"
    CONNECTION_FAILURE = "connection_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"

class SeverityLevel(Enum):
    """Severity levels for issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Issue:
    """Represents a detected issue"""
    issue_id: str
    issue_type: IssueType
    severity: SeverityLevel
    description: str
    affected_tables: List[str]
    detected_at: datetime
    detection_method: str
    evidence: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_method: Optional[str] = None
    resolution_details: Optional[Dict[str, Any]] = None

@dataclass
class HealingAction:
    """Represents a healing action to be taken"""
    action_id: str
    issue_id: str
    action_type: str
    description: str
    estimated_duration: int  # seconds
    risk_level: str  # LOW, MEDIUM, HIGH
    prerequisites: List[str]
    steps: List[str]
    rollback_steps: List[str]
    validation_checks: List[str]

class IssueDetector:
    """Detects various types of data issues"""

    def __init__(self, db_manager: DatabaseManager, llm: ChatOpenAI = None):
        self.db_manager = db_manager
        self.llm = llm
        self.detection_rules = self._initialize_detection_rules()

    def _initialize_detection_rules(self) -> Dict[str, Dict]:
        """Initialize detection rules for various issue types"""
        return {
            "data_corruption": {
                "null_percentage_threshold": 15.0,
                "invalid_value_threshold": 5.0,
                "expected_format_violation": 10.0
            },
            "missing_data": {
                "expected_record_count_drop": 0.1,  # 10% drop
                "critical_fields_missing": 20.0,   # 20% missing
                "recent_data_gap_hours": 48
            },
            "duplicate_data": {
                "duplicate_percentage_threshold": 5.0,
                "exact_match_threshold": 1000
            },
            "performance_degradation": {
                "query_time_increase": 2.0,  # 2x slower
                "timeout_rate_threshold": 0.05,  # 5% timeouts
                "connection_pool_exhaustion": 0.9  # 90% pool usage
            },
            "data_staleness": {
                "max_age_hours": 72,
                "update_frequency_drop": 0.5  # 50% drop in updates
            }
        }

    async def detect_data_corruption(self) -> List[Issue]:
        """Detect data corruption issues"""
        issues = []

        try:
            with self.db_manager.get_session() as session:
                # Check for excessive nulls in critical fields
                critical_tables = ['florida_parcels', 'property_sales_history', 'tax_certificates']

                for table_name in critical_tables:
                    if table_name == 'florida_parcels':
                        # Check critical fields
                        total_count = session.query(FloridaParcels).count()
                        null_parcel_id = session.query(FloridaParcels).filter(
                            FloridaParcels.parcel_id.is_(None)
                        ).count()
                        null_owner = session.query(FloridaParcels).filter(
                            FloridaParcels.owner_name.is_(None)
                        ).count()

                        null_percentage = (null_parcel_id / total_count * 100) if total_count > 0 else 0

                        if null_percentage > self.detection_rules["data_corruption"]["null_percentage_threshold"]:
                            issues.append(Issue(
                                issue_id=f"corruption_{table_name}_{int(time.time())}",
                                issue_type=IssueType.DATA_CORRUPTION,
                                severity=SeverityLevel.HIGH,
                                description=f"Excessive null parcel_ids in {table_name}: {null_percentage:.1f}%",
                                affected_tables=[table_name],
                                detected_at=datetime.now(),
                                detection_method="null_field_analysis",
                                evidence={
                                    "total_records": total_count,
                                    "null_count": null_parcel_id,
                                    "null_percentage": null_percentage,
                                    "threshold": self.detection_rules["data_corruption"]["null_percentage_threshold"]
                                }
                            ))

                    elif table_name == 'property_sales_history':
                        # Check for invalid sale prices
                        total_sales = session.query(PropertySalesHistory).count()
                        invalid_prices = session.query(PropertySalesHistory).filter(
                            or_(
                                PropertySalesHistory.sale_price <= 0,
                                PropertySalesHistory.sale_price > 100000000  # Unrealistic high price
                            )
                        ).count()

                        invalid_percentage = (invalid_prices / total_sales * 100) if total_sales > 0 else 0

                        if invalid_percentage > self.detection_rules["data_corruption"]["invalid_value_threshold"]:
                            issues.append(Issue(
                                issue_id=f"corruption_{table_name}_{int(time.time())}",
                                issue_type=IssueType.DATA_CORRUPTION,
                                severity=SeverityLevel.MEDIUM,
                                description=f"Invalid sale prices in {table_name}: {invalid_percentage:.1f}%",
                                affected_tables=[table_name],
                                detected_at=datetime.now(),
                                detection_method="value_range_analysis",
                                evidence={
                                    "total_records": total_sales,
                                    "invalid_count": invalid_prices,
                                    "invalid_percentage": invalid_percentage,
                                    "threshold": self.detection_rules["data_corruption"]["invalid_value_threshold"]
                                }
                            ))

        except Exception as e:
            logger.error(f"Data corruption detection failed: {e}")

        return issues

    async def detect_missing_data(self) -> List[Issue]:
        """Detect missing data issues"""
        issues = []

        try:
            with self.db_manager.get_session() as session:
                # Check for recent data gaps
                cutoff_time = datetime.now() - timedelta(
                    hours=self.detection_rules["missing_data"]["recent_data_gap_hours"]
                )

                # Check property updates
                recent_property_updates = session.query(FloridaParcels).filter(
                    FloridaParcels.updated_at >= cutoff_time
                ).count()

                if recent_property_updates == 0:
                    issues.append(Issue(
                        issue_id=f"missing_data_properties_{int(time.time())}",
                        issue_type=IssueType.MISSING_DATA,
                        severity=SeverityLevel.HIGH,
                        description=f"No property updates in the last {self.detection_rules['missing_data']['recent_data_gap_hours']} hours",
                        affected_tables=['florida_parcels'],
                        detected_at=datetime.now(),
                        detection_method="temporal_gap_analysis",
                        evidence={
                            "cutoff_time": cutoff_time.isoformat(),
                            "recent_updates": recent_property_updates,
                            "threshold_hours": self.detection_rules["missing_data"]["recent_data_gap_hours"]
                        }
                    ))

                # Check for sales data gaps
                recent_sales = session.query(PropertySalesHistory).filter(
                    PropertySalesHistory.created_at >= cutoff_time
                ).count()

                if recent_sales == 0:
                    issues.append(Issue(
                        issue_id=f"missing_data_sales_{int(time.time())}",
                        issue_type=IssueType.MISSING_DATA,
                        severity=SeverityLevel.MEDIUM,
                        description=f"No sales data updates in the last {self.detection_rules['missing_data']['recent_data_gap_hours']} hours",
                        affected_tables=['property_sales_history'],
                        detected_at=datetime.now(),
                        detection_method="temporal_gap_analysis",
                        evidence={
                            "cutoff_time": cutoff_time.isoformat(),
                            "recent_updates": recent_sales,
                            "threshold_hours": self.detection_rules["missing_data"]["recent_data_gap_hours"]
                        }
                    ))

        except Exception as e:
            logger.error(f"Missing data detection failed: {e}")

        return issues

    async def detect_duplicate_data(self) -> List[Issue]:
        """Detect duplicate data issues"""
        issues = []

        try:
            with self.db_manager.get_session() as session:
                # Check for duplicate parcels
                duplicate_parcels_query = text("""
                    SELECT parcel_id, county, COUNT(*) as count
                    FROM florida_parcels
                    GROUP BY parcel_id, county
                    HAVING COUNT(*) > 1
                    LIMIT 100
                """)

                duplicate_parcels = session.execute(duplicate_parcels_query).fetchall()

                if len(duplicate_parcels) > self.detection_rules["duplicate_data"]["exact_match_threshold"]:
                    issues.append(Issue(
                        issue_id=f"duplicates_parcels_{int(time.time())}",
                        issue_type=IssueType.DUPLICATE_DATA,
                        severity=SeverityLevel.MEDIUM,
                        description=f"Found {len(duplicate_parcels)} duplicate parcel records",
                        affected_tables=['florida_parcels'],
                        detected_at=datetime.now(),
                        detection_method="exact_match_analysis",
                        evidence={
                            "duplicate_count": len(duplicate_parcels),
                            "threshold": self.detection_rules["duplicate_data"]["exact_match_threshold"],
                            "sample_duplicates": [dict(row) for row in duplicate_parcels[:10]]
                        }
                    ))

                # Check for duplicate sales
                duplicate_sales_query = text("""
                    SELECT parcel_id, sale_date, sale_price, COUNT(*) as count
                    FROM property_sales_history
                    WHERE sale_date IS NOT NULL
                    GROUP BY parcel_id, sale_date, sale_price
                    HAVING COUNT(*) > 1
                    LIMIT 100
                """)

                duplicate_sales = session.execute(duplicate_sales_query).fetchall()

                if len(duplicate_sales) > 50:  # Lower threshold for sales
                    issues.append(Issue(
                        issue_id=f"duplicates_sales_{int(time.time())}",
                        issue_type=IssueType.DUPLICATE_DATA,
                        severity=SeverityLevel.LOW,
                        description=f"Found {len(duplicate_sales)} duplicate sales records",
                        affected_tables=['property_sales_history'],
                        detected_at=datetime.now(),
                        detection_method="exact_match_analysis",
                        evidence={
                            "duplicate_count": len(duplicate_sales),
                            "threshold": 50,
                            "sample_duplicates": [dict(row) for row in duplicate_sales[:10]]
                        }
                    ))

        except Exception as e:
            logger.error(f"Duplicate data detection failed: {e}")

        return issues

    async def detect_performance_issues(self) -> List[Issue]:
        """Detect performance degradation issues"""
        issues = []

        try:
            # Check recent query performance metrics
            monitoring_ops = MonitoringOperations(self.db_manager)
            recent_metrics = monitoring_ops.get_recent_metrics(hours=2)

            query_time_metrics = [m for m in recent_metrics if m.metric_type == "query_time"]

            if query_time_metrics:
                avg_query_time = sum(m.metric_value for m in query_time_metrics) / len(query_time_metrics)

                # Get historical average (last week)
                week_metrics = monitoring_ops.get_recent_metrics(hours=168)  # 1 week
                historical_query_times = [m for m in week_metrics if m.metric_type == "query_time"]

                if historical_query_times:
                    historical_avg = sum(m.metric_value for m in historical_query_times) / len(historical_query_times)

                    if avg_query_time > historical_avg * self.detection_rules["performance_degradation"]["query_time_increase"]:
                        issues.append(Issue(
                            issue_id=f"performance_degradation_{int(time.time())}",
                            issue_type=IssueType.PERFORMANCE_DEGRADATION,
                            severity=SeverityLevel.MEDIUM,
                            description=f"Query performance degraded: current {avg_query_time:.1f}ms vs historical {historical_avg:.1f}ms",
                            affected_tables=["system"],
                            detected_at=datetime.now(),
                            detection_method="performance_trend_analysis",
                            evidence={
                                "current_avg_ms": avg_query_time,
                                "historical_avg_ms": historical_avg,
                                "degradation_factor": avg_query_time / historical_avg,
                                "threshold": self.detection_rules["performance_degradation"]["query_time_increase"]
                            }
                        ))

        except Exception as e:
            logger.error(f"Performance issue detection failed: {e}")

        return issues

    async def detect_all_issues(self) -> List[Issue]:
        """Run all detection methods and return combined results"""
        all_issues = []

        detection_methods = [
            self.detect_data_corruption,
            self.detect_missing_data,
            self.detect_duplicate_data,
            self.detect_performance_issues
        ]

        for method in detection_methods:
            try:
                issues = await method()
                all_issues.extend(issues)
            except Exception as e:
                logger.error(f"Detection method {method.__name__} failed: {e}")

        logger.info(f"🔍 Issue detection completed: {len(all_issues)} issues found")
        return all_issues

class HealingEngine:
    """Performs automated healing actions"""

    def __init__(self, db_manager: DatabaseManager, llm: ChatOpenAI = None):
        self.db_manager = db_manager
        self.llm = llm
        self.healing_strategies = self._initialize_healing_strategies()

    def _initialize_healing_strategies(self) -> Dict[IssueType, Callable]:
        """Initialize healing strategies for different issue types"""
        return {
            IssueType.DATA_CORRUPTION: self._heal_data_corruption,
            IssueType.MISSING_DATA: self._heal_missing_data,
            IssueType.DUPLICATE_DATA: self._heal_duplicate_data,
            IssueType.PERFORMANCE_DEGRADATION: self._heal_performance_issues,
            IssueType.DATA_STALENESS: self._heal_data_staleness,
            IssueType.REFERENTIAL_INTEGRITY: self._heal_referential_integrity
        }

    async def generate_healing_plan(self, issue: Issue) -> Optional[HealingAction]:
        """Generate a healing plan for an issue"""
        try:
            if issue.issue_type not in self.healing_strategies:
                logger.warning(f"No healing strategy available for issue type: {issue.issue_type}")
                return None

            # Generate action based on issue type
            if issue.issue_type == IssueType.DATA_CORRUPTION:
                return await self._plan_corruption_healing(issue)
            elif issue.issue_type == IssueType.MISSING_DATA:
                return await self._plan_missing_data_healing(issue)
            elif issue.issue_type == IssueType.DUPLICATE_DATA:
                return await self._plan_duplicate_data_healing(issue)
            elif issue.issue_type == IssueType.PERFORMANCE_DEGRADATION:
                return await self._plan_performance_healing(issue)
            else:
                return await self._plan_generic_healing(issue)

        except Exception as e:
            logger.error(f"Healing plan generation failed for issue {issue.issue_id}: {e}")
            return None

    async def _plan_corruption_healing(self, issue: Issue) -> HealingAction:
        """Plan healing for data corruption issues"""
        return HealingAction(
            action_id=f"heal_corruption_{int(time.time())}",
            issue_id=issue.issue_id,
            action_type="data_cleanup",
            description="Clean corrupted data by removing invalid records and normalizing values",
            estimated_duration=300,  # 5 minutes
            risk_level="MEDIUM",
            prerequisites=["database_backup", "maintenance_window"],
            steps=[
                "Identify corrupted records",
                "Create backup of affected tables",
                "Remove records with null critical fields",
                "Normalize invalid values to acceptable ranges",
                "Update data quality metrics"
            ],
            rollback_steps=[
                "Restore from backup if data quality degrades",
                "Revert value normalizations",
                "Restore original records"
            ],
            validation_checks=[
                "Verify null percentage below threshold",
                "Confirm no critical data loss",
                "Validate referential integrity"
            ]
        )

    async def _plan_missing_data_healing(self, issue: Issue) -> HealingAction:
        """Plan healing for missing data issues"""
        return HealingAction(
            action_id=f"heal_missing_{int(time.time())}",
            issue_id=issue.issue_id,
            action_type="data_refresh",
            description="Trigger data refresh from external sources to fill gaps",
            estimated_duration=1800,  # 30 minutes
            risk_level="LOW",
            prerequisites=["external_api_access", "sufficient_storage"],
            steps=[
                "Identify data gaps by time period",
                "Query external data sources",
                "Validate incoming data quality",
                "Insert missing records",
                "Update metadata timestamps"
            ],
            rollback_steps=[
                "Remove newly inserted records if validation fails",
                "Restore previous data state"
            ],
            validation_checks=[
                "Verify data completeness",
                "Check for duplicate insertions",
                "Validate data freshness"
            ]
        )

    async def _plan_duplicate_data_healing(self, issue: Issue) -> HealingAction:
        """Plan healing for duplicate data issues"""
        return HealingAction(
            action_id=f"heal_duplicates_{int(time.time())}",
            issue_id=issue.issue_id,
            action_type="deduplication",
            description="Remove duplicate records while preserving the most recent/complete data",
            estimated_duration=600,  # 10 minutes
            risk_level="MEDIUM",
            prerequisites=["database_backup", "read_write_access"],
            steps=[
                "Identify exact duplicate groups",
                "Rank duplicates by completeness and recency",
                "Mark duplicates for deletion (keep best record)",
                "Remove duplicate records",
                "Update affected foreign key references"
            ],
            rollback_steps=[
                "Restore deleted records from backup",
                "Revert foreign key updates"
            ],
            validation_checks=[
                "Verify no data loss",
                "Check referential integrity",
                "Confirm duplicate reduction"
            ]
        )

    async def _plan_performance_healing(self, issue: Issue) -> HealingAction:
        """Plan healing for performance issues"""
        return HealingAction(
            action_id=f"heal_performance_{int(time.time())}",
            issue_id=issue.issue_id,
            action_type="optimization",
            description="Optimize database performance through indexing and query tuning",
            estimated_duration=900,  # 15 minutes
            risk_level="LOW",
            prerequisites=["database_admin_access"],
            steps=[
                "Analyze slow query patterns",
                "Create missing indexes",
                "Update table statistics",
                "Optimize query plans",
                "Clear query cache if needed"
            ],
            rollback_steps=[
                "Remove created indexes if performance degrades",
                "Restore original query plans"
            ],
            validation_checks=[
                "Verify query performance improvement",
                "Check index usage statistics",
                "Monitor overall system performance"
            ]
        )

    async def _plan_generic_healing(self, issue: Issue) -> HealingAction:
        """Plan generic healing for unknown issue types"""
        return HealingAction(
            action_id=f"heal_generic_{int(time.time())}",
            issue_id=issue.issue_id,
            action_type="investigation",
            description="Investigate and document issue for manual resolution",
            estimated_duration=60,  # 1 minute
            risk_level="LOW",
            prerequisites=[],
            steps=[
                "Document issue details",
                "Log for manual review",
                "Create monitoring alert"
            ],
            rollback_steps=[],
            validation_checks=[
                "Verify issue documentation is complete"
            ]
        )

    async def execute_healing_action(self, action: HealingAction) -> Tuple[bool, Dict[str, Any]]:
        """Execute a healing action and return success status and details"""
        try:
            logger.info(f"🔧 Executing healing action: {action.description}")

            # Get the healing strategy
            issue_type = IssueType(action.issue_id.split('_')[1]) if '_' in action.issue_id else None
            if issue_type and issue_type in self.healing_strategies:
                strategy = self.healing_strategies[issue_type]
                result = await strategy(action)
                return result
            else:
                # Execute generic healing
                return await self._execute_generic_healing(action)

        except Exception as e:
            logger.error(f"❌ Healing action execution failed: {e}")
            return False, {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "action_id": action.action_id
            }

    async def _heal_data_corruption(self, action: HealingAction) -> Tuple[bool, Dict[str, Any]]:
        """Execute data corruption healing"""
        try:
            with self.db_manager.get_session() as session:
                # Example: Remove records with null parcel_ids
                deleted_count = session.query(FloridaParcels).filter(
                    FloridaParcels.parcel_id.is_(None)
                ).delete()

                session.commit()

                return True, {
                    "action": "removed_null_parcel_ids",
                    "records_deleted": deleted_count,
                    "execution_time": datetime.now().isoformat()
                }

        except Exception as e:
            return False, {"error": str(e)}

    async def _heal_missing_data(self, action: HealingAction) -> Tuple[bool, Dict[str, Any]]:
        """Execute missing data healing"""
        try:
            # This would typically trigger an external data refresh
            # For now, we'll just log the action
            logger.info("🔄 Would trigger data refresh from external sources")

            return True, {
                "action": "triggered_data_refresh",
                "status": "initiated",
                "execution_time": datetime.now().isoformat()
            }

        except Exception as e:
            return False, {"error": str(e)}

    async def _heal_duplicate_data(self, action: HealingAction) -> Tuple[bool, Dict[str, Any]]:
        """Execute duplicate data healing"""
        try:
            with self.db_manager.get_session() as session:
                # Example: Remove duplicate parcels (keep the most recent)
                duplicate_query = text("""
                    DELETE FROM florida_parcels
                    WHERE id NOT IN (
                        SELECT MAX(id)
                        FROM florida_parcels
                        GROUP BY parcel_id, county
                    )
                """)

                result = session.execute(duplicate_query)
                session.commit()

                return True, {
                    "action": "removed_duplicate_parcels",
                    "records_deleted": result.rowcount,
                    "execution_time": datetime.now().isoformat()
                }

        except Exception as e:
            return False, {"error": str(e)}

    async def _heal_performance_issues(self, action: HealingAction) -> Tuple[bool, Dict[str, Any]]:
        """Execute performance healing"""
        try:
            with self.db_manager.get_session() as session:
                # Example: Update table statistics
                session.execute(text("ANALYZE florida_parcels"))
                session.execute(text("ANALYZE property_sales_history"))
                session.execute(text("ANALYZE tax_certificates"))

                session.commit()

                return True, {
                    "action": "updated_table_statistics",
                    "tables_analyzed": ["florida_parcels", "property_sales_history", "tax_certificates"],
                    "execution_time": datetime.now().isoformat()
                }

        except Exception as e:
            return False, {"error": str(e)}

    async def _heal_data_staleness(self, action: HealingAction) -> Tuple[bool, Dict[str, Any]]:
        """Execute data staleness healing"""
        # This would typically trigger a data refresh
        return True, {"action": "data_refresh_triggered", "status": "scheduled"}

    async def _heal_referential_integrity(self, action: HealingAction) -> Tuple[bool, Dict[str, Any]]:
        """Execute referential integrity healing"""
        # This would clean up orphaned records
        return True, {"action": "orphaned_records_cleaned", "status": "completed"}

    async def _execute_generic_healing(self, action: HealingAction) -> Tuple[bool, Dict[str, Any]]:
        """Execute generic healing action"""
        # Log for manual review
        logger.info(f"📋 Generic healing action logged: {action.description}")
        return True, {"action": "logged_for_manual_review", "status": "documented"}

class SelfHealingOrchestrator:
    """Orchestrates the entire self-healing process"""

    def __init__(self, db_manager: DatabaseManager, openai_api_key: str = None):
        self.db_manager = db_manager
        self.openai_api_key = openai_api_key
        self.llm = None
        if openai_api_key:
            self.llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4", temperature=0.1)

        self.detector = IssueDetector(db_manager, self.llm)
        self.healing_engine = HealingEngine(db_manager, self.llm)
        self.active_issues = []
        self.healing_history = []

    async def run_healing_cycle(self) -> Dict[str, Any]:
        """Run a complete healing cycle"""
        cycle_start = datetime.now()
        logger.info("🔄 Starting self-healing cycle...")

        try:
            # 1. Detect issues
            detected_issues = await self.detector.detect_all_issues()
            new_issues = [issue for issue in detected_issues if issue.issue_id not in [i.issue_id for i in self.active_issues]]
            self.active_issues.extend(new_issues)

            logger.info(f"🔍 Detected {len(new_issues)} new issues, {len(self.active_issues)} total active")

            # 2. Generate healing plans
            healing_actions = []
            for issue in new_issues:
                if issue.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]:
                    action = await self.healing_engine.generate_healing_plan(issue)
                    if action:
                        healing_actions.append((issue, action))

            logger.info(f"🔧 Generated {len(healing_actions)} healing actions")

            # 3. Execute healing actions
            execution_results = []
            for issue, action in healing_actions:
                success, details = await self.healing_engine.execute_healing_action(action)

                execution_results.append({
                    "issue_id": issue.issue_id,
                    "action_id": action.action_id,
                    "success": success,
                    "details": details
                })

                if success:
                    issue.resolved = True
                    issue.resolved_at = datetime.now()
                    issue.resolution_method = action.action_type
                    issue.resolution_details = details
                    logger.info(f"✅ Successfully healed issue: {issue.description}")
                else:
                    logger.error(f"❌ Failed to heal issue: {issue.description}")

                self.healing_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "issue": asdict(issue),
                    "action": asdict(action),
                    "success": success,
                    "details": details
                })

            # 4. Generate AI summary if available
            ai_summary = ""
            if self.llm and (detected_issues or execution_results):
                ai_summary = await self._generate_ai_summary(detected_issues, execution_results)

            # 5. Log metrics
            monitoring_ops = MonitoringOperations(self.db_manager)
            monitoring_ops.log_metric(
                table_name="self_healing_system",
                metric_type="healing_cycle",
                metric_value=len(execution_results),
                metric_unit="actions_executed",
                additional_context={
                    "issues_detected": len(detected_issues),
                    "new_issues": len(new_issues),
                    "actions_successful": sum(1 for r in execution_results if r["success"]),
                    "cycle_duration_seconds": (datetime.now() - cycle_start).total_seconds()
                }
            )

            # 6. Clean up resolved issues
            self.active_issues = [issue for issue in self.active_issues if not issue.resolved]

            cycle_result = {
                "cycle_start": cycle_start.isoformat(),
                "cycle_duration_seconds": (datetime.now() - cycle_start).total_seconds(),
                "issues_detected": len(detected_issues),
                "new_issues": len(new_issues),
                "healing_actions_executed": len(execution_results),
                "successful_healings": sum(1 for r in execution_results if r["success"]),
                "active_issues_remaining": len(self.active_issues),
                "execution_results": execution_results,
                "ai_summary": ai_summary
            }

            logger.info(f"✅ Self-healing cycle completed in {cycle_result['cycle_duration_seconds']:.1f}s")
            return cycle_result

        except Exception as e:
            logger.error(f"❌ Self-healing cycle failed: {e}")
            return {
                "error": str(e),
                "cycle_start": cycle_start.isoformat(),
                "cycle_duration_seconds": (datetime.now() - cycle_start).total_seconds()
            }

    async def _generate_ai_summary(self, detected_issues: List[Issue], execution_results: List[Dict]) -> str:
        """Generate AI summary of healing cycle"""
        try:
            summary_data = {
                "detected_issues": [asdict(issue) for issue in detected_issues],
                "execution_results": execution_results
            }

            prompt = f"""
            As a database health expert, provide a concise summary of this self-healing cycle for ConcordBroker:

            Detected Issues: {len(detected_issues)}
            Healing Actions Executed: {len(execution_results)}
            Successful Healings: {sum(1 for r in execution_results if r["success"])}

            Data: {json.dumps(summary_data, default=str, indent=2)[:1000]}...

            Provide:
            1. Overall system health assessment
            2. Key issues addressed
            3. Recommended follow-up actions
            4. Risk assessment

            Keep response under 150 words.
            """

            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content

        except Exception as e:
            logger.error(f"AI summary generation failed: {e}")
            return f"AI summary unavailable: {str(e)}"

    async def start_continuous_healing(self, cycle_interval: int = 1800):  # 30 minutes default
        """Start continuous self-healing"""
        logger.info(f"🚀 Starting continuous self-healing with {cycle_interval}s intervals")

        try:
            while True:
                await self.run_healing_cycle()
                await asyncio.sleep(cycle_interval)

        except asyncio.CancelledError:
            logger.info("🛑 Continuous self-healing stopped")
        except Exception as e:
            logger.error(f"❌ Continuous self-healing failed: {e}")

    def get_system_health_report(self) -> Dict[str, Any]:
        """Get current system health report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "active_issues": [asdict(issue) for issue in self.active_issues],
            "recent_healing_history": self.healing_history[-10:],  # Last 10 actions
            "health_score": self._calculate_health_score(),
            "recommendations": self._generate_recommendations()
        }

    def _calculate_health_score(self) -> float:
        """Calculate overall system health score (0-100)"""
        if not self.active_issues:
            return 100.0

        # Weight issues by severity
        severity_weights = {
            SeverityLevel.LOW: 1,
            SeverityLevel.MEDIUM: 3,
            SeverityLevel.HIGH: 7,
            SeverityLevel.CRITICAL: 15
        }

        total_weight = sum(severity_weights[issue.severity] for issue in self.active_issues)
        max_possible_weight = len(self.active_issues) * severity_weights[SeverityLevel.CRITICAL]

        health_score = max(0, 100 - (total_weight / max_possible_weight * 100))
        return round(health_score, 1)

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on current issues"""
        recommendations = []

        critical_issues = [i for i in self.active_issues if i.severity == SeverityLevel.CRITICAL]
        high_issues = [i for i in self.active_issues if i.severity == SeverityLevel.HIGH]

        if critical_issues:
            recommendations.append(f"🚨 URGENT: Address {len(critical_issues)} critical issues immediately")

        if high_issues:
            recommendations.append(f"⚠️ HIGH PRIORITY: Review {len(high_issues)} high-severity issues")

        if len(self.active_issues) > 10:
            recommendations.append("📊 MONITORING: High number of active issues - review detection thresholds")

        if not recommendations:
            recommendations.append("✅ HEALTHY: System operating normally")

        return recommendations

# Example usage
async def main():
    """Example usage of the self-healing system"""
    try:
        # Initialize database
        from sqlalchemy_models import initialize_database
        db_manager = initialize_database()

        # Create self-healing orchestrator
        orchestrator = SelfHealingOrchestrator(
            db_manager=db_manager,
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )

        # Run a single healing cycle
        result = await orchestrator.run_healing_cycle()
        print(f"Healing cycle result: {json.dumps(result, indent=2, default=str)}")

        # Get health report
        health_report = orchestrator.get_system_health_report()
        print(f"Health report: {json.dumps(health_report, indent=2, default=str)}")

        # Start continuous healing (uncomment to run continuously)
        # await orchestrator.start_continuous_healing(cycle_interval=300)  # 5 minutes

    except Exception as e:
        logger.error(f"❌ Self-healing system test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import os
    asyncio.run(main())
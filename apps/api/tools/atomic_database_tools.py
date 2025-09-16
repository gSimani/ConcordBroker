"""
Atomic Database Tools for ConcordBroker
Each tool performs ONE specific database operation with comprehensive error handling
Based on Self-Improving Agent principles from arxiv:2504.15228
"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from datetime import datetime
import logging
import asyncio
from functools import wraps
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Decorator for atomic tool validation
def atomic_tool(operation_name: str):
    """
    Decorator to ensure tools are atomic and have proper error handling
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            operation_id = f"{operation_name}_{start_time.timestamp()}"
            
            logger.info(f"[{operation_id}] Starting {operation_name}")
            
            try:
                # Validate inputs
                if hasattr(func, '__annotations__'):
                    for param, expected_type in func.__annotations__.items():
                        if param in kwargs:
                            value = kwargs[param]
                            if value is not None and not isinstance(value, expected_type):
                                raise TypeError(f"Parameter '{param}' must be {expected_type}, got {type(value)}")
                
                # Execute operation
                result = await func(*args, **kwargs)
                
                # Log success
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"[{operation_id}] Completed {operation_name} in {duration:.2f}s")
                
                return {
                    "success": True,
                    "operation": operation_name,
                    "result": result,
                    "duration": duration,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                # Log error
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"[{operation_id}] Failed {operation_name}: {str(e)}")
                
                return {
                    "success": False,
                    "operation": operation_name,
                    "error": str(e),
                    "duration": duration,
                    "timestamp": datetime.now().isoformat()
                }
                
        return wrapper
    return decorator


@dataclass
class ValidationResult:
    """Result of input validation"""
    valid: bool
    errors: List[str]
    warnings: List[str]


class ParcelIDValidator:
    """Atomic tool for validating parcel IDs"""
    
    @staticmethod
    @atomic_tool("validate_parcel_id")
    async def validate(parcel_id: str) -> ValidationResult:
        """
        Single purpose: Validate a parcel ID format
        Returns validation result with specific errors/warnings
        """
        errors = []
        warnings = []
        
        # Check if parcel_id exists
        if not parcel_id:
            errors.append("Parcel ID is required")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)
        
        # Check length
        if len(parcel_id) < 10:
            errors.append(f"Parcel ID too short: {len(parcel_id)} chars (minimum 10)")
        elif len(parcel_id) > 30:
            warnings.append(f"Parcel ID unusually long: {len(parcel_id)} chars")
        
        # Check format (alphanumeric with possible dashes)
        valid_chars = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-")
        invalid_chars = set(parcel_id.upper()) - valid_chars
        if invalid_chars:
            errors.append(f"Invalid characters in parcel ID: {invalid_chars}")
        
        # Check pattern (example: should start with digits)
        if parcel_id and not parcel_id[0].isdigit():
            warnings.append("Parcel ID typically starts with a digit")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


class PropertyFetcher:
    """Atomic tool for fetching property data"""
    
    def __init__(self, database_connection):
        self.db = database_connection
    
    @atomic_tool("fetch_property")
    async def fetch_by_parcel_id(self, parcel_id: str, county: Optional[str] = None) -> Dict[str, Any]:
        """
        Single purpose: Fetch property data by parcel ID
        Returns property data or empty dict if not found
        """
        # First validate parcel ID
        validator = ParcelIDValidator()
        validation = await validator.validate(parcel_id)
        
        if not validation.valid:
            raise ValueError(f"Invalid parcel ID: {', '.join(validation.errors)}")
        
        # Build query
        query = {"parcel_id": parcel_id}
        if county:
            query["county"] = county
        
        # Execute query with timeout
        try:
            async with asyncio.timeout(5.0):  # 5 second timeout
                result = await self.db.florida_parcels.find_one(query)
                
                if result:
                    # Remove internal fields
                    result.pop("_id", None)
                    return result
                else:
                    return {}
                    
        except asyncio.TimeoutError:
            raise TimeoutError("Database query timed out after 5 seconds")


class PropertyUpdater:
    """Atomic tool for updating property data"""
    
    def __init__(self, database_connection):
        self.db = database_connection
    
    @atomic_tool("update_property_field")
    async def update_single_field(self, 
                                  parcel_id: str, 
                                  field_name: str, 
                                  new_value: Any,
                                  county: Optional[str] = None) -> bool:
        """
        Single purpose: Update a single field in property record
        Returns True if updated, False if not found
        """
        # Validate parcel ID
        validator = ParcelIDValidator()
        validation = await validator.validate(parcel_id)
        
        if not validation.valid:
            raise ValueError(f"Invalid parcel ID: {', '.join(validation.errors)}")
        
        # Validate field name
        prohibited_fields = ["_id", "parcel_id", "created_at"]
        if field_name in prohibited_fields:
            raise ValueError(f"Cannot update protected field: {field_name}")
        
        # Build query and update
        query = {"parcel_id": parcel_id}
        if county:
            query["county"] = county
        
        update = {
            "$set": {
                field_name: new_value,
                "updated_at": datetime.now().isoformat()
            }
        }
        
        # Execute update
        result = await self.db.florida_parcels.update_one(query, update)
        
        return result.modified_count > 0


class PropertyCounter:
    """Atomic tool for counting properties"""
    
    def __init__(self, database_connection):
        self.db = database_connection
    
    @atomic_tool("count_properties")
    async def count_by_criteria(self, criteria: Dict[str, Any]) -> int:
        """
        Single purpose: Count properties matching criteria
        Returns count as integer
        """
        # Validate criteria
        if not isinstance(criteria, dict):
            raise TypeError("Criteria must be a dictionary")
        
        # Remove any dangerous operators
        dangerous_ops = ["$where", "$function", "$accumulator", "$code"]
        for op in dangerous_ops:
            if op in str(criteria):
                raise ValueError(f"Dangerous operator not allowed: {op}")
        
        # Execute count with timeout
        try:
            async with asyncio.timeout(10.0):  # 10 second timeout for counts
                count = await self.db.florida_parcels.count_documents(criteria)
                return count
                
        except asyncio.TimeoutError:
            raise TimeoutError("Count operation timed out after 10 seconds")


class PropertySearcher:
    """Atomic tool for searching properties"""
    
    def __init__(self, database_connection):
        self.db = database_connection
    
    @atomic_tool("search_properties")
    async def search(self, 
                    criteria: Dict[str, Any],
                    limit: int = 10,
                    offset: int = 0,
                    sort_by: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Single purpose: Search properties with criteria
        Returns list of matching properties
        """
        # Validate limit and offset
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("Limit must be a positive integer")
        if not isinstance(offset, int) or offset < 0:
            raise ValueError("Offset must be a non-negative integer")
        if limit > 100:
            raise ValueError("Limit cannot exceed 100 records")
        
        # Build sort
        sort = []
        if sort_by:
            if sort_by.startswith("-"):
                sort = [(sort_by[1:], -1)]
            else:
                sort = [(sort_by, 1)]
        
        # Execute search
        try:
            async with asyncio.timeout(15.0):  # 15 second timeout
                cursor = self.db.florida_parcels.find(criteria)
                
                if sort:
                    cursor = cursor.sort(sort)
                
                cursor = cursor.skip(offset).limit(limit)
                
                results = []
                async for doc in cursor:
                    doc.pop("_id", None)
                    results.append(doc)
                
                return results
                
        except asyncio.TimeoutError:
            raise TimeoutError("Search operation timed out after 15 seconds")


class TaxDeedFetcher:
    """Atomic tool for fetching tax deed data"""
    
    def __init__(self, database_connection):
        self.db = database_connection
    
    @atomic_tool("fetch_tax_deed")
    async def fetch_by_status(self, 
                              status: str = "upcoming",
                              county: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Single purpose: Fetch tax deed sales by status
        Returns list of tax deed records
        """
        # Validate status
        valid_statuses = ["upcoming", "past", "cancelled", "all"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        
        # Build query
        query = {}
        if status != "all":
            query["status"] = status
        if county:
            query["county"] = county
        
        # Execute query
        try:
            async with asyncio.timeout(10.0):
                cursor = self.db.tax_deed_sales.find(query).limit(100)
                
                results = []
                async for doc in cursor:
                    doc.pop("_id", None)
                    results.append(doc)
                
                return results
                
        except asyncio.TimeoutError:
            raise TimeoutError("Tax deed fetch timed out after 10 seconds")


class BulkOperationValidator:
    """Atomic tool for validating bulk operations"""
    
    @staticmethod
    @atomic_tool("validate_bulk_operation")
    async def validate(operation_type: str, 
                       record_count: int,
                       require_confirmation: bool = True) -> Dict[str, Any]:
        """
        Single purpose: Validate if bulk operation is safe to proceed
        Returns validation result with risk assessment
        """
        risk_level = "low"
        warnings = []
        requires_escalation = False
        
        # Check operation type risk
        high_risk_ops = ["delete", "permanent_delete", "mass_update"]
        if operation_type in high_risk_ops:
            risk_level = "high"
            warnings.append(f"High-risk operation: {operation_type}")
            
        # Check record count
        if record_count > 1000:
            risk_level = "critical"
            warnings.append(f"Large number of records: {record_count}")
            requires_escalation = True
        elif record_count > 100:
            if risk_level != "critical":
                risk_level = "high"
            warnings.append(f"Significant number of records: {record_count}")
        
        # Check if confirmation required
        if require_confirmation and risk_level in ["high", "critical"]:
            requires_escalation = True
        
        return {
            "approved": not requires_escalation,
            "risk_level": risk_level,
            "warnings": warnings,
            "requires_escalation": requires_escalation,
            "record_count": record_count,
            "operation_type": operation_type
        }


class TransactionLogger:
    """Atomic tool for logging database transactions"""
    
    def __init__(self, database_connection):
        self.db = database_connection
    
    @atomic_tool("log_transaction")
    async def log(self,
                  operation: str,
                  target: str,
                  user: str,
                  details: Dict[str, Any],
                  success: bool) -> str:
        """
        Single purpose: Log a database transaction
        Returns transaction ID
        """
        transaction_id = f"txn_{datetime.now().timestamp()}"
        
        log_entry = {
            "transaction_id": transaction_id,
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "target": target,
            "user": user,
            "details": details,
            "success": success
        }
        
        # Store in audit log
        await self.db.audit_log.insert_one(log_entry)
        
        # Log to file/monitoring system
        if success:
            logger.info(f"Transaction {transaction_id}: {operation} on {target} by {user}")
        else:
            logger.error(f"Failed transaction {transaction_id}: {operation} on {target} by {user}")
        
        return transaction_id


# Composite tool builder using atomic tools
class CompositePropertyOperation:
    """
    Example of building complex operations from atomic tools
    """
    
    def __init__(self, database_connection):
        self.fetcher = PropertyFetcher(database_connection)
        self.updater = PropertyUpdater(database_connection)
        self.counter = PropertyCounter(database_connection)
        self.logger = TransactionLogger(database_connection)
    
    async def update_property_with_validation(self,
                                              parcel_id: str,
                                              updates: Dict[str, Any],
                                              user: str) -> Dict[str, Any]:
        """
        Composite operation: Fetch, validate, update, log
        Built from atomic tools
        """
        results = {
            "parcel_id": parcel_id,
            "updates_applied": [],
            "errors": [],
            "transaction_ids": []
        }
        
        # Step 1: Fetch current property (atomic)
        fetch_result = await self.fetcher.fetch_by_parcel_id(parcel_id)
        
        if not fetch_result["success"]:
            results["errors"].append(f"Failed to fetch property: {fetch_result.get('error')}")
            return results
        
        if not fetch_result["result"]:
            results["errors"].append("Property not found")
            return results
        
        # Step 2: Apply updates one by one (atomic)
        for field, value in updates.items():
            update_result = await self.updater.update_single_field(
                parcel_id, field, value
            )
            
            if update_result["success"]:
                results["updates_applied"].append(field)
                
                # Step 3: Log each successful update (atomic)
                txn_id = await self.logger.log(
                    operation="update",
                    target=f"{parcel_id}.{field}",
                    user=user,
                    details={"old": fetch_result["result"].get(field), "new": value},
                    success=True
                )
                results["transaction_ids"].append(txn_id["result"])
            else:
                results["errors"].append(f"Failed to update {field}: {update_result.get('error')}")
        
        return results


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_atomic_tools():
        # Test parcel ID validation
        validator = ParcelIDValidator()
        
        # Valid parcel ID
        result = await validator.validate("1234567890")
        print(f"Valid parcel: {result}")
        
        # Invalid parcel ID
        result = await validator.validate("123")
        print(f"Invalid parcel: {result}")
        
        # Test bulk operation validation
        bulk_validator = BulkOperationValidator()
        
        # Safe operation
        result = await bulk_validator.validate("update", 50)
        print(f"Safe bulk op: {result}")
        
        # Risky operation
        result = await bulk_validator.validate("delete", 5000)
        print(f"Risky bulk op: {result}")
    
    asyncio.run(test_atomic_tools())
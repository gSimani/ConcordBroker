"""
Zod-inspired Python Validation for ConcordBroker
Runtime data validation for pipeline agents and API
"""

from typing import Optional, Dict, Any, List, Union, Tuple
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum
import re

# ============================================
# ENUMS
# ============================================

class PropertyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"
    SOLD = "SOLD"

class EntityStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DISSOLVED = "DISSOLVED"
    ADMIN_DISSOLVED = "ADMIN_DISSOLVED"
    WITHDRAWN = "WITHDRAWN"

class PaymentStatus(str, Enum):
    PAID = "PAID"
    UNPAID = "UNPAID"
    PARTIAL = "PARTIAL"
    DELINQUENT = "DELINQUENT"

class MatchStatus(str, Enum):
    MATCHED = "matched"
    PARTIAL = "partial"
    UNMATCHED = "unmatched"
    POLYGON_ONLY = "polygon_only"

# ============================================
# PROPERTY SCHEMAS
# ============================================

class FloridaParcel(BaseModel):
    """Florida Parcel validation schema"""
    
    # Required fields
    parcel_id: str = Field(..., min_length=1, max_length=50)
    county: str = Field(..., min_length=1, max_length=50)
    year: int = Field(..., ge=2000, le=2050)
    
    # Geometry (optional)
    geometry: Optional[Dict[str, Any]] = None
    centroid: Optional[Dict[str, Any]] = None
    area_sqft: Optional[float] = Field(None, gt=0)
    perimeter_ft: Optional[float] = Field(None, gt=0)
    
    # Ownership
    owner_name: Optional[str] = Field(None, max_length=255)
    owner_addr1: Optional[str] = Field(None, max_length=255)
    owner_addr2: Optional[str] = Field(None, max_length=255)
    owner_city: Optional[str] = Field(None, max_length=100)
    owner_state: Optional[str] = Field(None, min_length=2, max_length=2)
    owner_zip: Optional[str] = None
    
    # Physical address
    phy_addr1: Optional[str] = Field(None, max_length=255)
    phy_addr2: Optional[str] = Field(None, max_length=255)
    phy_city: Optional[str] = Field(None, max_length=100)
    phy_state: str = Field(default="FL", min_length=2, max_length=2)
    phy_zipcd: Optional[str] = None
    
    # Legal description
    legal_desc: Optional[str] = None
    subdivision: Optional[str] = Field(None, max_length=255)
    lot: Optional[str] = Field(None, max_length=50)
    block: Optional[str] = Field(None, max_length=50)
    
    # Property characteristics
    property_use: Optional[str] = Field(None, max_length=10)
    property_use_desc: Optional[str] = Field(None, max_length=255)
    land_use_code: Optional[str] = Field(None, max_length=10)
    zoning: Optional[str] = Field(None, max_length=50)
    
    # Valuations
    just_value: Optional[float] = Field(None, ge=0)
    assessed_value: Optional[float] = Field(None, ge=0)
    taxable_value: Optional[float] = Field(None, ge=0)
    land_value: Optional[float] = Field(None, ge=0)
    building_value: Optional[float] = Field(None, ge=0)
    
    # Property details
    year_built: Optional[int] = Field(None, ge=1800, le=2050)
    total_living_area: Optional[float] = Field(None, ge=0)
    bedrooms: Optional[int] = Field(None, ge=0, le=100)
    bathrooms: Optional[float] = Field(None, ge=0, le=100)
    stories: Optional[float] = Field(None, ge=0, le=100)
    units: Optional[int] = Field(None, ge=0)
    
    # Land measurements
    land_sqft: Optional[float] = Field(None, ge=0)
    land_acres: Optional[float] = Field(None, ge=0)
    
    # Sales information
    sale_date: Optional[datetime] = None
    sale_price: Optional[float] = Field(None, ge=0)
    sale_qualification: Optional[str] = Field(None, max_length=10)
    
    # Data quality flags
    match_status: Optional[MatchStatus] = None
    discrepancy_reason: Optional[str] = Field(None, max_length=100)
    is_redacted: bool = False
    data_source: Optional[str] = Field(None, max_length=20)
    
    # Metadata
    import_date: datetime = Field(default_factory=datetime.now)
    update_date: Optional[datetime] = None
    data_hash: Optional[str] = Field(None, max_length=64)
    
    @validator('owner_zip', 'phy_zipcd')
    def validate_zip(cls, v):
        if v and not re.match(r'^\d{5}(-\d{4})?$', v):
            raise ValueError('Invalid ZIP code format')
        return v
    
    @validator('owner_state', 'phy_state')
    def validate_state(cls, v):
        if v and len(v) != 2:
            raise ValueError('State must be 2 characters')
        return v.upper() if v else v
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }

class PropertySale(BaseModel):
    """Property sale transaction schema"""
    
    parcel_id: str = Field(..., min_length=1, max_length=50)
    county: str = Field(..., min_length=1, max_length=50)
    
    # Sale information
    sale_date: datetime
    sale_price: float = Field(..., gt=0)
    sale_type: Optional[str] = Field(None, max_length=50)
    qualification_code: Optional[str] = Field(None, max_length=10)
    
    # Parties
    grantor_name: Optional[str] = Field(None, max_length=255)
    grantee_name: Optional[str] = Field(None, max_length=255)
    
    # Property details
    property_address: Optional[str] = Field(None, max_length=255)
    property_use_code: Optional[str] = Field(None, max_length=10)
    
    # Valuations at sale
    just_value_at_sale: Optional[float] = Field(None, ge=0)
    assessed_value_at_sale: Optional[float] = Field(None, ge=0)
    
    # Analysis metrics
    price_per_sqft: Optional[float] = Field(None, gt=0)
    sale_ratio: Optional[float] = Field(None, ge=0, le=10)
    
    # Sale type flags
    is_qualified_sale: bool = False
    is_arms_length: bool = False
    is_foreclosure: bool = False
    is_reo_sale: bool = False
    is_short_sale: bool = False
    
    # Entity flags
    is_corporate_buyer: bool = False
    is_corporate_seller: bool = False
    buyer_entity_type: Optional[str] = Field(None, max_length=50)
    seller_entity_type: Optional[str] = Field(None, max_length=50)
    
    # Recording info
    or_book: Optional[str] = Field(None, max_length=20)
    or_page: Optional[str] = Field(None, max_length=20)
    instrument_number: Optional[str] = Field(None, max_length=30)
    
    import_date: datetime = Field(default_factory=datetime.now)

# ============================================
# BUSINESS ENTITY SCHEMAS
# ============================================

class SunbizCorporate(BaseModel):
    """Sunbiz corporate entity schema"""
    
    doc_number: str = Field(..., max_length=12)
    entity_name: Optional[str] = Field(None, max_length=200)
    status: Optional[EntityStatus] = None
    filing_date: Optional[date] = None
    state_country: Optional[str] = Field(None, max_length=50)
    
    # Principal Address
    prin_addr1: Optional[str] = Field(None, max_length=100)
    prin_addr2: Optional[str] = Field(None, max_length=100)
    prin_city: Optional[str] = Field(None, max_length=50)
    prin_state: Optional[str] = Field(None, min_length=2, max_length=2)
    prin_zip: Optional[str] = None
    
    # Mailing Address
    mail_addr1: Optional[str] = Field(None, max_length=100)
    mail_addr2: Optional[str] = Field(None, max_length=100)
    mail_city: Optional[str] = Field(None, max_length=50)
    mail_state: Optional[str] = Field(None, min_length=2, max_length=2)
    mail_zip: Optional[str] = None
    
    # Additional Info
    ein: Optional[str] = None
    registered_agent: Optional[str] = Field(None, max_length=100)
    
    # Metadata
    file_type: Optional[str] = Field(None, max_length=20)
    subtype: Optional[str] = Field(None, max_length=20)
    source_file: Optional[str] = Field(None, max_length=100)
    import_date: datetime = Field(default_factory=datetime.now)
    update_date: Optional[datetime] = None
    
    @validator('ein')
    def validate_ein(cls, v):
        if v and not re.match(r'^\d{2}-\d{7}$', v):
            raise ValueError('Invalid EIN format (should be XX-XXXXXXX)')
        return v

# ============================================
# ASSESSMENT SCHEMAS
# ============================================

class NAVAssessment(BaseModel):
    """Non-ad valorem assessment schema"""
    
    parcel_id: str = Field(..., min_length=1, max_length=50)
    county: str = Field(..., min_length=1, max_length=50)
    tax_year: int = Field(..., ge=2000, le=2050)
    
    # Property identification
    owner_name: Optional[str] = Field(None, max_length=255)
    property_address: Optional[str] = Field(None, max_length=255)
    
    # Assessment totals
    total_nav_amount: float = Field(..., ge=0)
    total_assessments: int = Field(..., ge=0)
    
    # Common assessment types
    cdd_amount: Optional[float] = Field(None, ge=0)
    hoa_amount: Optional[float] = Field(None, ge=0)
    special_district_amount: Optional[float] = Field(None, ge=0)
    
    # Payment status
    payment_status: Optional[PaymentStatus] = None
    delinquent_amount: Optional[float] = Field(None, ge=0)
    
    import_date: datetime = Field(default_factory=datetime.now)

# ============================================
# PIPELINE VALIDATION
# ============================================

class PipelineDataValidator:
    """Data validator for pipeline agents"""
    
    @staticmethod
    def validate_property(data: Dict[str, Any]) -> Tuple[bool, Optional[FloridaParcel], List[str]]:
        """Validate property data"""
        try:
            parcel = FloridaParcel(**data)
            return True, parcel, []
        except Exception as e:
            errors = str(e).split('\n')
            return False, None, errors
    
    @staticmethod
    def validate_sale(data: Dict[str, Any]) -> Tuple[bool, Optional[PropertySale], List[str]]:
        """Validate sale data"""
        try:
            sale = PropertySale(**data)
            return True, sale, []
        except Exception as e:
            errors = str(e).split('\n')
            return False, None, errors
    
    @staticmethod
    def validate_entity(data: Dict[str, Any]) -> Tuple[bool, Optional[SunbizCorporate], List[str]]:
        """Validate entity data"""
        try:
            entity = SunbizCorporate(**data)
            return True, entity, []
        except Exception as e:
            errors = str(e).split('\n')
            return False, None, errors
    
    @staticmethod
    def validate_batch(schema_class, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Batch validation with statistics"""
        valid = []
        invalid = []
        
        for item in items:
            try:
                validated = schema_class(**item)
                valid.append(validated)
            except Exception as e:
                invalid.append({
                    'item': item,
                    'errors': str(e).split('\n')
                })
        
        total = len(items)
        valid_count = len(valid)
        invalid_count = len(invalid)
        
        return {
            'valid': valid,
            'invalid': invalid,
            'stats': {
                'total': total,
                'valid': valid_count,
                'invalid': invalid_count,
                'success_rate': (valid_count / total * 100) if total > 0 else 0
            }
        }

# ============================================
# CUSTOM VALIDATORS
# ============================================

class FloridaValidators:
    """Florida-specific validation utilities"""
    
    @staticmethod
    def is_valid_parcel_id(parcel_id: str) -> bool:
        """Validate Florida parcel ID format"""
        if not parcel_id:
            return False
        # Florida parcel IDs typically follow county-specific formats
        pattern = r'^[0-9A-Z\-\.]+$'
        return bool(re.match(pattern, parcel_id)) and 10 <= len(parcel_id) <= 30
    
    @staticmethod
    def is_valid_florida_zip(zip_code: str) -> bool:
        """Validate Florida ZIP code"""
        if not zip_code or len(zip_code) < 5:
            return False
        # Florida ZIP codes range from 32003 to 34997
        try:
            num_zip = int(zip_code[:5])
            return 32003 <= num_zip <= 34997
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_county(county: str) -> bool:
        """Validate Florida county name"""
        florida_counties = {
            'BROWARD', 'MIAMI-DADE', 'PALM BEACH', 'MONROE',
            'COLLIER', 'LEE', 'ORANGE', 'HILLSBOROUGH',
            'PINELLAS', 'DUVAL', 'BREVARD', 'VOLUSIA',
            'MARTIN', 'ST. LUCIE', 'INDIAN RIVER', 'OKEECHOBEE',
            'HIGHLANDS', 'POLK', 'OSCEOLA', 'SEMINOLE',
            'CHARLOTTE', 'SARASOTA', 'MANATEE', 'PASCO'
        }
        return county.upper() in florida_counties
    
    @staticmethod
    def validate_property_use_code(code: str) -> bool:
        """Validate Florida DOR property use codes"""
        if not code:
            return False
        
        # Florida DOR codes are typically 3-4 digits
        if not code.isdigit() or not (3 <= len(code) <= 4):
            return False
        
        # First digit indicates general category
        # 0 = Residential, 1 = Commercial, 2 = Industrial, etc.
        first_digit = int(code[0])
        return 0 <= first_digit <= 9
    
    @staticmethod
    def clean_owner_name(name: str) -> str:
        """Clean and standardize owner names"""
        if not name:
            return ""
        
        # Remove common suffixes and clean up
        name = name.upper()
        name = re.sub(r'\s+', ' ', name)  # Multiple spaces to single
        name = re.sub(r'[^\w\s\-\&\.]', '', name)  # Remove special chars
        name = name.strip()
        
        return name

# ============================================
# VALIDATION MIDDLEWARE
# ============================================

class ValidationMiddleware:
    """Validation middleware for API and pipeline"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.validator = PipelineDataValidator()
        self.florida_validator = FloridaValidators()
    
    def validate_incoming_data(self, data_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate incoming data based on type"""
        
        validators = {
            'property': self.validator.validate_property,
            'sale': self.validator.validate_sale,
            'entity': self.validator.validate_entity,
            'assessment': lambda d: self._validate_assessment(d)
        }
        
        validator = validators.get(data_type)
        if not validator:
            return {
                'success': False,
                'errors': [f'Unknown data type: {data_type}']
            }
        
        success, validated_data, errors = validator(data)
        
        if self.logger:
            if success:
                self.logger.info(f"Validation successful for {data_type}")
            else:
                self.logger.error(f"Validation failed for {data_type}: {errors}")
        
        return {
            'success': success,
            'data': validated_data.dict() if validated_data else None,
            'errors': errors
        }
    
    def _validate_assessment(self, data: Dict[str, Any]) -> Tuple[bool, Optional[NAVAssessment], List[str]]:
        """Validate assessment data"""
        try:
            assessment = NAVAssessment(**data)
            return True, assessment, []
        except Exception as e:
            errors = str(e).split('\n')
            return False, None, errors
    
    def validate_batch_import(
        self, 
        data_type: str, 
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate batch import data"""
        
        schema_map = {
            'property': FloridaParcel,
            'sale': PropertySale,
            'entity': SunbizCorporate,
            'assessment': NAVAssessment
        }
        
        schema_class = schema_map.get(data_type)
        if not schema_class:
            return {
                'success': False,
                'errors': [f'Unknown data type: {data_type}']
            }
        
        result = self.validator.validate_batch(schema_class, items)
        
        if self.logger:
            stats = result['stats']
            self.logger.info(
                f"Batch validation for {data_type}: "
                f"{stats['valid']}/{stats['total']} valid "
                f"({stats['success_rate']:.1f}% success rate)"
            )
        
        return result

# Export main components
__all__ = [
    'FloridaParcel',
    'PropertySale',
    'SunbizCorporate',
    'NAVAssessment',
    'PipelineDataValidator',
    'FloridaValidators',
    'ValidationMiddleware'
]
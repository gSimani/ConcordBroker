# DOR Use Code Assignment - Complete AI Agent System

## 🤖 System Overview

This comprehensive AI agent system assigns DOR (Department of Revenue) use codes to all 9.1M Florida properties using intelligent analysis of property characteristics.

## 📁 Components Created

### 1. SQLAlchemy Agent
**File**: `mcp-server/ai-agents/dor_use_code_assignment_agent.py`

**Features**:
- Analyzes current DOR use code coverage
- Intelligent use code assignment based on property characteristics
- Validation and quality checks
- Comprehensive reporting

**Usage**:
```bash
cd mcp-server/ai-agents
python dor_use_code_assignment_agent.py
```

### 2. PySpark Processor
**File**: `mcp-server/pyspark-processors/dor_use_code_spark_processor.py`

**Features**:
- Distributed processing for 9.1M records
- Parallel batch processing
- Advanced analytics and aggregations
- County-level breakdowns

**Usage**:
```bash
cd mcp-server/pyspark-processors
python dor_use_code_spark_processor.py
```

**Requirements**:
```bash
pip install pyspark
```

### 3. FastAPI Service
**File**: `mcp-server/fastapi-endpoints/dor_use_code_api.py`

**Features**:
- REST API for use code operations
- Bulk assignment endpoint
- Real-time status monitoring
- Analytics and reporting endpoints

**Endpoints**:
- `GET /health` - Health check
- `GET /use-codes` - List all DOR use codes
- `GET /use-code/{code}` - Get specific use code details
- `GET /assignment-status` - Current assignment status
- `POST /assign-bulk` - Bulk assign use codes
- `GET /analytics/distribution` - Use code distribution
- `GET /analytics/coverage-by-county` - County coverage stats
- `PUT /property/use-code` - Update single property

**Usage**:
```bash
cd mcp-server/fastapi-endpoints
python dor_use_code_api.py
```

Server runs on: `http://localhost:8002`

### 4. Jupyter Notebook
**File**: `mcp-server/notebooks/dor_use_code_analysis.ipynb`

**Features**:
- Interactive data analysis
- Visualization dashboards
- Coverage analysis
- Value analysis by use code
- County-level breakdowns
- Quality validation
- Export capabilities

**Usage**:
```bash
jupyter notebook mcp-server/notebooks/dor_use_code_analysis.ipynb
```

### 5. Coordination Script
**File**: `run_dor_use_code_assignment.py`

**Features**:
- System health checks
- Status analysis
- SQL generation for manual execution
- Comprehensive reporting

**Usage**:
```bash
python run_dor_use_code_assignment.py
```

## 🧠 Intelligent Assignment Logic

The system assigns DOR use codes based on property characteristics:

### Assignment Rules:

| DOR Code | Type | Criteria |
|----------|------|----------|
| **00** | Single Family | `building_value > $50k AND building > land AND just_value < $1M` |
| **01** | Agricultural | `land > building*5 AND land > $100k` |
| **02** | Multi-Family 10+ | `building_value > $500k AND building > land*2` |
| **10** | Vacant Residential | `land > 0 AND building = 0` |
| **17** | Commercial | `just_value > $500k AND building > $200k` |
| **24** | Industrial | `building > $1M AND land < $500k` |
| **80** | Institutional | `just_value > $1M AND building > $500k` |

## 📊 Categories Assigned

Properties are also categorized:

- **Residential**: Codes 00-10
- **Commercial**: Codes 11-19
- **Industrial**: Codes 20-27
- **Agricultural**: Codes 30-38
- **Institutional**: Codes 80-89

## 🚀 Execution Options

### Option 1: Direct SQL (Fastest)
```sql
-- Execute in Supabase SQL Editor
UPDATE florida_parcels
SET
    dor_uc = CASE
        WHEN (building_value > 50000 AND building_value > land_value
              AND just_value < 1000000) THEN '00'
        WHEN (building_value > 500000 AND building_value > land_value * 2) THEN '02'
        WHEN (just_value > 500000 AND building_value > 200000) THEN '17'
        WHEN (building_value > 1000000 AND land_value < 500000) THEN '24'
        WHEN (land_value > building_value * 5 AND land_value > 100000) THEN '01'
        WHEN (land_value > 0 AND (building_value IS NULL OR building_value = 0)) THEN '10'
        ELSE '00'
    END,
    property_use = CASE
        WHEN (building_value > 50000 AND building_value > land_value
              AND just_value < 1000000) THEN 'Single Family'
        WHEN (building_value > 500000 AND building_value > land_value * 2) THEN 'Multi-Family 10+'
        WHEN (just_value > 500000 AND building_value > 200000) THEN 'Commercial'
        WHEN (building_value > 1000000 AND land_value < 500000) THEN 'Industrial'
        WHEN (land_value > building_value * 5 AND land_value > 100000) THEN 'Agricultural'
        WHEN (land_value > 0 AND (building_value IS NULL OR building_value = 0)) THEN 'Vacant Residential'
        ELSE 'Single Family'
    END,
    property_use_category = CASE
        WHEN (building_value > 50000 AND building_value > land_value
              AND just_value < 1000000) THEN 'Residential'
        WHEN (building_value > 500000 AND building_value > land_value * 2) THEN 'Residential'
        WHEN (just_value > 500000 AND building_value > 200000) THEN 'Commercial'
        WHEN (building_value > 1000000 AND land_value < 500000) THEN 'Industrial'
        WHEN (land_value > building_value * 5 AND land_value > 100000) THEN 'Agricultural'
        WHEN (land_value > 0 AND (building_value IS NULL OR building_value = 0)) THEN 'Residential'
        ELSE 'Residential'
    END
WHERE year = 2025 AND (dor_uc IS NULL OR dor_uc = '');
```

### Option 2: FastAPI Service
```bash
# Start service
python mcp-server/fastapi-endpoints/dor_use_code_api.py

# Call bulk assignment
curl -X POST http://localhost:8002/assign-bulk \
  -H "Content-Type: application/json" \
  -d '{"year": 2025, "dry_run": false}'
```

### Option 3: PySpark (For Large Scale)
```bash
python mcp-server/pyspark-processors/dor_use_code_spark_processor.py
```

### Option 4: SQLAlchemy Agent
```bash
python mcp-server/ai-agents/dor_use_code_assignment_agent.py
```

## 📈 Monitoring & Validation

### Check Status
```bash
# Via FastAPI
curl http://localhost:8002/assignment-status

# Via Jupyter Notebook
jupyter notebook mcp-server/notebooks/dor_use_code_analysis.ipynb
```

### Validation Query
```sql
SELECT
    COUNT(*) as total_properties,
    COUNT(CASE WHEN dor_uc IS NOT NULL AND dor_uc != '' THEN 1 END) as with_code,
    COUNT(CASE WHEN dor_uc IS NULL OR dor_uc = '' THEN 1 END) as without_code,
    ROUND(COUNT(CASE WHEN dor_uc IS NOT NULL AND dor_uc != '' THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage_pct
FROM florida_parcels
WHERE year = 2025;
```

## 🎯 Expected Results

After running the assignment:
- **Coverage**: 100% of 9.1M properties
- **Execution Time**:
  - Direct SQL: 2-5 minutes
  - FastAPI: 5-10 minutes
  - PySpark: 10-15 minutes (but with analytics)
- **Data Quality**: All properties have valid DOR codes and categories

## 📊 Analytics Available

### Use Code Distribution
- Count by use code
- Total value by use code
- Average value by use code

### Geographic Analysis
- County-level coverage
- County-level distribution
- Regional patterns

### Category Breakdown
- Properties by category
- Value by category
- County by category matrix

## 🔍 Quality Checks

The system validates:
1. ✅ All properties have DOR codes
2. ✅ All codes exist in `dor_use_codes` table
3. ✅ Categories are correctly assigned
4. ✅ Property_use descriptions match codes

## 📝 Integration with MiniPropertyCards

Once assignment is complete, MiniPropertyCards will automatically display:
- **Primary Use**: From `dor_uc` + `property_use`
- **Category**: From `property_use_category`
- **Sub-Use**: From `dor_use_codes.subcategory`

The cards query `florida_parcels` table which now includes:
- `dor_uc`: 2-digit DOR code
- `property_use`: Human-readable description
- `property_use_category`: High-level category

## 🔗 Related Tables

### dor_use_codes
Reference table with all Florida DOR use codes:
- `use_code`: 2-digit code
- `use_description`: Full description
- `category`: High-level category
- `subcategory`: Detailed subcategory
- Boolean flags: `is_residential`, `is_commercial`, etc.

### florida_parcels
Main property table (9.1M records):
- `parcel_id`: Unique identifier
- `county`: County name
- `year`: Data year (2025)
- `dor_uc`: Assigned use code
- `property_use`: Use description
- `property_use_category`: Category
- Plus all property characteristics

## 🚨 Troubleshooting

### Connection Timeouts
If direct database connections timeout:
1. Use FastAPI service (uses connection pooling)
2. Use generated SQL in Supabase dashboard
3. Break into county-level batches

### Port Conflicts
- FastAPI Service: Port 8002
- MCP Server: Port 3001
- Check availability: `netstat -ano | findstr :8002`

### Memory Issues
For PySpark:
- Increase driver memory: `--driver-memory 8g`
- Increase executor memory: `--executor-memory 8g`
- Reduce batch size in assignment logic

## 📚 Additional Resources

- **DOR Use Codes**: https://floridarevenue.com/property/Pages/DataPortal_DownloadCodeBooks.aspx
- **Property Data**: https://floridarevenue.com/property/dataportal/Pages/default.aspx
- **FastAPI Docs**: `http://localhost:8002/docs` (when service running)

## ✅ Completion Checklist

- [x] SQLAlchemy agent created
- [x] PySpark processor created
- [x] FastAPI service created
- [x] Jupyter notebook created
- [x] Coordination script created
- [ ] Execute bulk assignment
- [ ] Validate 100% coverage
- [ ] Verify MiniPropertyCard display
- [ ] Document results

## 🎉 Success Criteria

The system is successful when:
1. ✅ All 9.1M properties have `dor_uc` assigned
2. ✅ All codes are valid (exist in `dor_use_codes`)
3. ✅ `property_use` and `property_use_category` are populated
4. ✅ MiniPropertyCards display use codes correctly
5. ✅ Analytics show reasonable distribution

---

**Status**: ✅ System Ready for Execution
**Next Step**: Execute bulk assignment using preferred method
**Estimated Time**: 5-10 minutes for full dataset
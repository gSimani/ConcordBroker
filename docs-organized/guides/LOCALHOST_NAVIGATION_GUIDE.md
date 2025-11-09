# 🏠 ConcordBroker Localhost Navigation Guide

## 🚀 All Services Now Running!

### ✅ Service Status
- **React Frontend**: http://localhost:5174 *(Port 5174 - adjusted from 5173)*
- **Python API**: http://localhost:8000
- **MCP Server**: http://localhost:3005
- **API Documentation**: http://localhost:8000/docs
- **MCP Health Check**: http://localhost:3005/health

---

## 📑 Major Pages & Features

### 🏠 **1. Homepage**
**URL**: http://localhost:5174/

**Features**:
- Dashboard overview
- Quick property search
- Market insights
- Recent activity feed
- Navigation to all major sections

---

### 🔍 **2. Property Search**
**URL**: http://localhost:5174/properties

**Features**:
- Advanced property filters
- Search by parcel ID, address, owner
- County selection (67 Florida counties)
- Property type filtering
- Map integration with Google Maps

**Sample Searches**:
- Parcel ID: `064210010010`
- Address: `123 Main St`
- Owner: `Smith`

---

### 🏡 **3. Property Profile Page**
**URL**: http://localhost:5174/property/[PARCEL_ID]

**Example**: http://localhost:5174/property/064210010010

**Comprehensive Tabs**:
1. **Overview Tab**
   - Property address & details
   - Owner information
   - Land & building square footage
   - Year built, bedrooms, bathrooms
   - Property use codes

2. **Ownership Tab**
   - Current owner details
   - Mailing address
   - Corporate ownership (Sunbiz integration)
   - Entity status & incorporation info

3. **Sales History Tab**
   - Historical sales transactions
   - Sale prices & dates
   - Buyer/seller information
   - Document numbers
   - Qualification codes

4. **Tax Deed Sales Tab**
   - Upcoming tax deed auctions
   - Past auction results
   - Certificate information
   - Bidding details
   - Redemption status

5. **Taxes Tab**
   - Current tax assessments
   - Millage rates
   - Exemptions (homestead, senior, veteran)
   - School vs. non-school taxes

6. **Permits Tab**
   - Building permits history
   - Permit types & status
   - Contractor information
   - Estimated values

7. **Sunbiz Tab**
   - Business entity information
   - Officers & registered agents
   - Annual reports
   - Entity filings

8. **Analysis Tab**
   - Market value analysis
   - Investment metrics
   - Comparable sales
   - ROI estimates

---

### 📊 **4. Tax Deed Sales**
**URL**: http://localhost:5174/tax-deed-sales

**Features**:
- Live auction calendar
- Upcoming auctions by county
- Past auction results
- Bidding information
- Property details for each auction

**Filter Options**:
- Auction status (Upcoming, Completed, Cancelled, Redeemed)
- County selection
- Date ranges
- Bid amounts

---

### 🏢 **5. Business Entity Search**
**URL**: http://localhost:5174/entities

**Features**:
- Sunbiz entity lookup
- Officer information
- Corporate property ownership
- Entity status tracking
- Document number search

---

### 🎯 **6. AI Property Search**
**URL**: http://localhost:5174/ai-search

**Features**:
- Natural language property queries
- Intelligent search suggestions
- Market analysis integration
- Investment opportunity identification

---

### 📈 **7. Analytics Dashboard**
**URL**: http://localhost:5174/analytics

**Features**:
- Market trends by county
- Property value analytics
- Investment performance metrics
- Tax deed success rates

---

## 🔧 **API Endpoints**

### **Property API** (Port 8000)
```
GET  /api/properties              # List properties
GET  /api/property/{parcel_id}    # Get specific property
GET  /api/search/properties       # Search properties
GET  /api/tax-deeds               # Tax deed sales
GET  /api/sunbiz/entities         # Business entities
```

### **MCP API** (Port 3005)
```
GET  /health                      # Service health
GET  /api/supabase/{table}        # Database queries
POST /api/vercel/deploy           # Deploy to Vercel
POST /api/railway/deploy          # Deploy to Railway
```

---

## 🗺️ **Sample Property URLs**

### **Broward County Properties**:
- http://localhost:5174/property/064210010010
- http://localhost:5174/property/064210020030
- http://localhost:5174/property/064230040050

### **Miami-Dade Properties**:
- http://localhost:5174/property/30301234567890
- http://localhost:5174/property/30301111222333

### **Palm Beach Properties**:
- http://localhost:5174/property/504023456789012

---

## 🧪 **Testing Features**

### **Data Verification**:
```bash
# Run complete data verification
python run_data_verification.py

# Quick data mapping check
python run_data_verification.py --quick

# Test specific property
python run_data_verification.py --sample-parcel 064210010010
```

### **Visual Testing**:
- All tabs should display data correctly
- Maps should load with property locations
- Tax deed information should be current
- Business entity data should be integrated

---

## 📱 **Mobile-Responsive Design**

All pages are optimized for:
- Desktop (1920x1080+)
- Tablet (768px-1024px)
- Mobile (360px-768px)

---

## 🔍 **Quick Test Checklist**

### ✅ **Homepage Test**:
1. Go to http://localhost:5174
2. Verify dashboard loads
3. Check search functionality
4. Navigate to different sections

### ✅ **Property Search Test**:
1. Go to http://localhost:5174/properties
2. Search for parcel ID: `064210010010`
3. Verify results display
4. Click through to property profile

### ✅ **Property Profile Test**:
1. Go to http://localhost:5174/property/064210010010
2. Check all 8 tabs load correctly:
   - Overview ✅
   - Ownership ✅
   - Sales History ✅
   - Tax Deed Sales ✅
   - Taxes ✅
   - Permits ✅
   - Sunbiz ✅
   - Analysis ✅

### ✅ **Tax Deed Test**:
1. Go to http://localhost:5174/tax-deed-sales
2. Verify auction listings
3. Check filter functionality
4. Test property links

### ✅ **API Test**:
1. Go to http://localhost:8000/docs
2. Test API endpoints
3. Verify data responses

---

## 🛠️ **Troubleshooting**

### **If Frontend Won't Load**:
```bash
cd apps/web
npm install
npm run dev
```

### **If API Won't Start**:
```bash
cd apps/api
pip install -r requirements.txt
python property_live_api.py
```

### **If MCP Server Issues**:
```bash
cd mcp-server
npm install
npm start
```

### **Database Connection Issues**:
- Check `.env.mcp` file exists
- Verify Supabase credentials
- Test connection: `python test_supabase_connection.py`

---

## 🎯 **Key Testing Scenarios**

1. **Property Lookup**: Search → Select → View all tabs
2. **Tax Deed Flow**: Browse auctions → View property → Check bidding
3. **Business Entity**: Search company → View officers → Check properties
4. **Data Verification**: Run verification scripts → Check reports
5. **API Integration**: Test all endpoints → Verify responses

---

*Navigate to any of these URLs to explore the full ConcordBroker application!*
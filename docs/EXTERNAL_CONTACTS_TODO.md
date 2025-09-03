# 🚨 EXTERNAL CONTACTS & ACTIONS REQUIRED

**Last Updated:** 2025-01-03  
**Status:** IMMEDIATE ACTION REQUIRED

---

## 📞 REQUIRED EXTERNAL CONTACTS

### 1. ⭐ FLORIDA DOR - Property Tax Data (NAL/SDF Files)
**CRITICAL: Must contact to get Broward County assessment roll data**

**Contact Information:**
- 📧 **Email:** PTOTechnology@floridarevenue.com
- 📞 **Phone:** 850-717-6570
- 📠 **Fax:** 850-488-9482
- 🌐 **Portal:** https://floridarevenue.com/property/Pages/DataPortal_RequestAssessmentRollGISData.aspx

**What to Request:**
```
Subject: Broward County NAL/SDF Data Request - County Code 16

Hello,

We are requesting access to the following assessment roll data files for Broward County (County Code 16):

1. NAL (Name-Address-Legal) file - Latest available
2. SDF (Sale Data File) - Latest available
3. Both preliminary (July) and final (October) rolls for 2024
4. Documentation/User Guide if updated from 2024 version

Please provide download instructions or temporary download link.

Thank you,
[Your Name]
ConcordBroker Data Team
```

**Expected Response:** Download link via email (files >10MB)
**Timeline:** Usually 1-2 business days

---

### 2. 📋 BROWARD COUNTY OFFICIAL RECORDS
**Alternative data access arrangements needed**

**Contact Information:**
- 📞 **Main Office:** 954-357-5100
- 📞 **Records Division:** 954-357-7000
- 🌐 **Web Portal:** https://officialrecords.broward.org/AcclaimWeb
- 📧 **General Inquiries:** records@broward.org

**What to Request:**
- Bulk data export options for recorded documents
- FTP access availability (reference: ftp://crpublic@bcftp.broward.org)
- API or web service availability
- Cost for bulk data purchase
- Daily export file formats (DOC/NME/LGL/LNK)

**Alternative if No Bulk Access:**
- Sign up for Recording Notification Service (free email alerts)
- Implement web scraping solution (ready to deploy)

---

### 3. 📊 BROWARD COUNTY PROPERTY APPRAISER (BCPA)
**Data purchase or partnership needed**

**Contact Information:**
- 📞 **Main Office:** 954-357-6830
- 📞 **GIS Department:** 954-357-6859
- 🌐 **Website:** https://bcpa.net/
- 🌐 **Search Portal:** https://web.bcpa.net/BcpaClient/
- 📧 **Email:** martykiar@bcpa.net (Property Appraiser)

**What to Request:**
- GIS data purchase options and pricing
- Bulk parcel data export availability
- API access for commercial users
- Data update frequency
- File formats available (Shapefile, CSV, etc.)

**GeoHub Access (BETA):**
- 🌐 **URL:** https://geohub-bcgis.opendata.arcgis.com/
- Currently in BETA - check for available datasets

---

### 4. 🏢 ENRICHMENT DATA PROVIDERS
**For missing contact information**

**Clearbit:**
- 🌐 **URL:** https://clearbit.com/
- 📧 **Sales:** sales@clearbit.com
- 💰 **Pricing:** Enterprise plans for bulk enrichment

**ZoomInfo:**
- 🌐 **URL:** https://www.zoominfo.com/
- 📞 **Sales:** 1-866-904-9666
- 💰 **Pricing:** Custom enterprise pricing

**LinkedIn Sales Navigator:**
- 🌐 **URL:** https://business.linkedin.com/sales-solutions/
- 💰 **Pricing:** $99.99/month per seat (Team plan)

---

## ✅ DATA SOURCES READY TO IMPLEMENT

### ✅ FLORIDA SUNBIZ - READY NOW!
**No contact needed - we have working credentials**

**SFTP Access:**
```
Host: sftp.floridados.gov
Username: Public
Password: PubAccess1845!
Port: 22
Directory: /public/daily/ (daily files)
          /public/quarterly/ (full dataset)
```

**Action:** Implementing automated daily sync at 8:00 AM ET

---

## 📊 TRACKING DASHBOARD

| Source | Status | Contact Required | Implementation |
|--------|--------|-----------------|----------------|
| Florida DOR | 🔴 Blocked | YES - Email/Call | Waiting for access |
| Sunbiz | ✅ Ready | NO | Implementing now |
| Official Records | 🟡 Partial | YES - Explore options | Scraper ready |
| BCPA | 🟡 Partial | OPTIONAL | Scraper ready |
| Enrichment | 🔴 Needed | YES - Sales call | Evaluating providers |

---

## 📝 SAMPLE SCRIPTS FOR CALLS

### When Calling Florida DOR:
"Hi, I'm calling about obtaining Broward County property assessment roll data files. We need the NAL and SDF files for County Code 16. Can you help me with the process to request these files? We already have the 2024 User Guide but need the actual data files."

### When Calling BCPA:
"Hello, we're building a real estate investment analysis platform and need access to Broward County parcel data. Do you offer bulk data exports or API access for commercial users? We're particularly interested in property characteristics, ownership, and assessment values."

### When Calling Broward Records:
"Hi, I'm inquiring about bulk access to official recorded documents data. We're looking for daily exports of deeds, mortgages, and liens. Is there an FTP service or API available, or do you offer data purchase options?"

---

## 🚀 IMMEDIATE ACTIONS WE'RE TAKING NOW

1. **Implementing Sunbiz SFTP loader** - Starting immediately
2. **Building BCPA web scraper** - Playwright automation ready
3. **Creating Official Records scraper** - Fallback solution
4. **Setting up data quality monitoring** - For all sources
5. **Implementing scoring algorithm** - Based on available data

---

## 📅 FOLLOW-UP SCHEDULE

- [ ] **TODAY:** Email Florida DOR for NAL/SDF access
- [ ] **TODAY:** Call BCPA about data purchase options  
- [ ] **TOMORROW:** Follow up on Florida DOR if no response
- [ ] **THIS WEEK:** Schedule demos with enrichment providers
- [ ] **NEXT WEEK:** Evaluate responses and adjust strategy

---

**Note:** This document should be updated as contacts are made and access is obtained.
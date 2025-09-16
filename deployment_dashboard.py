"""
Property Appraiser Deployment Dashboard
FastAPI-based web interface for monitoring deployment progress
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from supabase import create_client, Client

# Load environment
from dotenv import load_dotenv
load_dotenv('.env.mcp')

# Initialize FastAPI app
app = FastAPI(
    title="Property Appraiser Deployment Dashboard",
    description="Monitor Florida Property Appraiser data loading progress",
    version="1.0.0"
)

# Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Models
class DeploymentStatus(BaseModel):
    stage: str
    status: str
    records_processed: int
    total_expected: int
    completion_percentage: float
    errors: List[str]
    last_updated: str

class CountyProgress(BaseModel):
    county: str
    status: str
    records: int
    files_processed: int
    processing_time: float
    anomalies: int

# Global status tracking
deployment_status = DeploymentStatus(
    stage="not_started",
    status="waiting",
    records_processed=0,
    total_expected=9700000,
    completion_percentage=0.0,
    errors=[],
    last_updated=datetime.now().isoformat()
)

county_progress = {}

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard HTML"""

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Property Appraiser Deployment Dashboard</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }

            .container {
                max-width: 1200px;
                margin: 0 auto;
            }

            .header {
                text-align: center;
                margin-bottom: 30px;
            }

            .status-card {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }

            .progress-bar {
                width: 100%;
                height: 30px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 15px;
                overflow: hidden;
                margin: 10px 0;
            }

            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #4CAF50, #8BC34A);
                border-radius: 15px;
                transition: width 0.5s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
            }

            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }

            .stat-item {
                background: rgba(255, 255, 255, 0.1);
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }

            .stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #4CAF50;
            }

            .county-list {
                max-height: 400px;
                overflow-y: auto;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 8px;
                padding: 10px;
            }

            .county-item {
                display: flex;
                justify-content: space-between;
                padding: 8px;
                margin: 4px 0;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }

            .btn {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                margin: 5px;
                font-size: 14px;
            }

            .btn:hover {
                background: #45a049;
            }

            .btn-danger {
                background: #f44336;
            }

            .btn-danger:hover {
                background: #da190b;
            }

            .error-list {
                background: rgba(244, 67, 54, 0.2);
                border-left: 4px solid #f44336;
                padding: 10px;
                margin: 10px 0;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏠 Property Appraiser Deployment Dashboard</h1>
                <p>Florida Property Data Loading System</p>
            </div>

            <div class="status-card">
                <h2>🚀 Deployment Status</h2>
                <div id="deployment-status">
                    <p><strong>Stage:</strong> <span id="current-stage">Loading...</span></p>
                    <p><strong>Status:</strong> <span id="current-status">Loading...</span></p>

                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill" style="width: 0%">0%</div>
                    </div>

                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-number" id="records-processed">0</div>
                            <div>Records Processed</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number" id="counties-completed">0</div>
                            <div>Counties Completed</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number" id="anomalies-detected">0</div>
                            <div>Anomalies Detected</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number" id="data-quality">0</div>
                            <div>Quality Score</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="status-card">
                <h2>🎛️ Controls</h2>
                <button class="btn" onclick="checkSchema()">Check Schema</button>
                <button class="btn" onclick="startDeployment()">Start Data Loading</button>
                <button class="btn" onclick="refreshStatus()">Refresh Status</button>
                <button class="btn btn-danger" onclick="stopDeployment()">Stop Process</button>
            </div>

            <div class="status-card">
                <h2>📊 County Progress</h2>
                <div id="county-progress" class="county-list">
                    Loading county information...
                </div>
            </div>

            <div class="status-card" id="errors-section" style="display: none;">
                <h2>⚠️ Errors & Warnings</h2>
                <div id="error-list" class="error-list"></div>
            </div>
        </div>

        <script>
            // Auto-refresh every 5 seconds
            setInterval(refreshStatus, 5000);

            // Initial load
            refreshStatus();

            async function refreshStatus() {
                try {
                    const response = await fetch('/api/status');
                    const data = await response.json();

                    document.getElementById('current-stage').textContent = data.stage;
                    document.getElementById('current-status').textContent = data.status;
                    document.getElementById('records-processed').textContent = data.records_processed.toLocaleString();

                    const percentage = data.completion_percentage;
                    const progressFill = document.getElementById('progress-fill');
                    progressFill.style.width = percentage + '%';
                    progressFill.textContent = percentage.toFixed(1) + '%';

                    // Update errors if any
                    if (data.errors.length > 0) {
                        document.getElementById('errors-section').style.display = 'block';
                        document.getElementById('error-list').innerHTML =
                            data.errors.map(error => `<div>${error}</div>`).join('');
                    }

                } catch (error) {
                    console.error('Error fetching status:', error);
                }
            }

            async function refreshCountyProgress() {
                try {
                    const response = await fetch('/api/counties');
                    const data = await response.json();

                    const countyList = document.getElementById('county-progress');
                    countyList.innerHTML = data.map(county => `
                        <div class="county-item">
                            <span><strong>${county.county}</strong></span>
                            <span>${county.status} | ${county.records.toLocaleString()} records</span>
                        </div>
                    `).join('');

                } catch (error) {
                    console.error('Error fetching county progress:', error);
                }
            }

            async function checkSchema() {
                try {
                    const response = await fetch('/api/check-schema');
                    const data = await response.json();
                    alert(`Schema Status: ${data.exists ? 'Deployed' : 'Not Deployed'}`);
                } catch (error) {
                    alert('Error checking schema: ' + error.message);
                }
            }

            async function startDeployment() {
                if (confirm('Start Property Appraiser data loading? This may take several hours.')) {
                    try {
                        const response = await fetch('/api/start-deployment', {method: 'POST'});
                        const data = await response.json();
                        alert('Deployment started: ' + data.message);
                    } catch (error) {
                        alert('Error starting deployment: ' + error.message);
                    }
                }
            }

            async function stopDeployment() {
                if (confirm('Stop the current deployment process?')) {
                    try {
                        const response = await fetch('/api/stop-deployment', {method: 'POST'});
                        const data = await response.json();
                        alert('Deployment stopped: ' + data.message);
                    } catch (error) {
                        alert('Error stopping deployment: ' + error.message);
                    }
                }
            }

            // Refresh county progress every 10 seconds
            setInterval(refreshCountyProgress, 10000);
            refreshCountyProgress();
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)

@app.get("/api/status")
async def get_status():
    """Get current deployment status"""
    return deployment_status

@app.get("/api/counties")
async def get_county_progress():
    """Get progress for all counties"""
    return list(county_progress.values())

@app.get("/api/check-schema")
async def check_schema():
    """Check if database schema is deployed"""
    try:
        result = supabase.table('florida_parcels').select("*").limit(1).execute()
        return {"exists": True, "message": "Schema is deployed"}
    except Exception as e:
        return {"exists": False, "message": f"Schema not deployed: {str(e)}"}

@app.post("/api/start-deployment")
async def start_deployment(background_tasks: BackgroundTasks):
    """Start the data loading process"""
    global deployment_status

    if deployment_status.status == "running":
        raise HTTPException(status_code=400, detail="Deployment already running")

    deployment_status.stage = "initializing"
    deployment_status.status = "running"
    deployment_status.last_updated = datetime.now().isoformat()

    # Start background task
    background_tasks.add_task(run_deployment)

    return {"message": "Deployment started", "status": "running"}

@app.post("/api/stop-deployment")
async def stop_deployment():
    """Stop the data loading process"""
    global deployment_status

    deployment_status.status = "stopped"
    deployment_status.last_updated = datetime.now().isoformat()

    return {"message": "Deployment stop requested", "status": "stopped"}

async def run_deployment():
    """Background task to run the actual deployment"""
    global deployment_status, county_progress

    try:
        # Import and run the loader
        from property_appraiser_data_loader import PropertyAppraiserLoader

        deployment_status.stage = "loading_data"
        deployment_status.status = "running"

        loader = PropertyAppraiserLoader()

        # Start with major counties
        test_counties = ['BROWARD', 'PALM BEACH', 'MIAMI-DADE']

        results = []
        for county in test_counties:
            if deployment_status.status == "stopped":
                break

            deployment_status.stage = f"processing_{county}"

            result = loader.process_county_data(county)
            results.append(result)

            # Update progress
            county_progress[county] = CountyProgress(
                county=county,
                status=result.get('status', 'unknown'),
                records=result.get('total_records', 0),
                files_processed=result.get('files_processed', 0),
                processing_time=result.get('processing_time', 0),
                anomalies=result.get('anomalies', 0)
            )

            deployment_status.records_processed += result.get('total_records', 0)
            deployment_status.completion_percentage = min(
                (deployment_status.records_processed / deployment_status.total_expected) * 100,
                100.0
            )

        deployment_status.stage = "completed"
        deployment_status.status = "completed"

    except Exception as e:
        deployment_status.stage = "error"
        deployment_status.status = "error"
        deployment_status.errors.append(f"Deployment error: {str(e)}")

    deployment_status.last_updated = datetime.now().isoformat()

@app.get("/api/database-stats")
async def get_database_stats():
    """Get current database statistics"""
    try:
        # Get total record count
        result = supabase.table('florida_parcels').select('*', count='exact').limit(1).execute()
        total_records = result.count if hasattr(result, 'count') else 0

        # Get county breakdown
        county_query = supabase.table('florida_parcels').select('county', count='exact').execute()

        return {
            "total_records": total_records,
            "counties_loaded": len(set([r['county'] for r in county_query.data])) if county_query.data else 0,
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        return {"error": str(e), "total_records": 0, "counties_loaded": 0}

if __name__ == "__main__":
    import uvicorn
    print("Starting Property Appraiser Deployment Dashboard...")
    print("Access dashboard at: http://localhost:8080")
    print("API documentation at: http://localhost:8080/docs")

    uvicorn.run(app, host="0.0.0.0", port=8080)
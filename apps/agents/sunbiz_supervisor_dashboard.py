"""
SUNBIZ SUPERVISOR DASHBOARD API
================================
REST API for monitoring and controlling the Sunbiz Supervisor Agent
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import psycopg2
from urllib.parse import urlparse
import json
import os

app = FastAPI(title="Sunbiz Supervisor Dashboard", version="1.0.0")

# Database configuration
DB_URL = os.getenv('DATABASE_URL', 
    "postgres://postgres.pmispwtdngkcmsrsjwbp:West%40Boca613!@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require")

def get_db_connection():
    """Get database connection"""
    parsed = urlparse(DB_URL)
    return psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path.lstrip('/'),
        user=parsed.username,
        password=parsed.password.replace('%40', '@') if parsed.password else None,
        sslmode='require'
    )

# ==================== MODELS ====================

class TaskRequest(BaseModel):
    task_name: str
    priority: int = 3
    parameters: Optional[Dict] = {}

class ConfigUpdate(BaseModel):
    update_schedule: Optional[str] = None
    health_check_interval: Optional[int] = None
    enable_auto_recovery: Optional[bool] = None
    max_retries: Optional[int] = None

# ==================== ENDPOINTS ====================

@app.get("/")
async def dashboard():
    """Serve the dashboard HTML interface"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sunbiz Supervisor Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container { max-width: 1400px; margin: 0 auto; }
            h1 { 
                color: white; 
                text-align: center; 
                margin-bottom: 30px;
                font-size: 2.5em;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            }
            .grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                gap: 20px; 
            }
            .card {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: transform 0.2s;
            }
            .card:hover { transform: translateY(-2px); }
            .card h2 { 
                color: #333; 
                margin-bottom: 15px;
                font-size: 1.2em;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }
            .status { 
                display: inline-block; 
                padding: 5px 10px; 
                border-radius: 20px; 
                font-size: 0.9em;
                font-weight: bold;
            }
            .status.active { background: #10b981; color: white; }
            .status.idle { background: #3b82f6; color: white; }
            .status.error { background: #ef4444; color: white; }
            .metric { 
                display: flex; 
                justify-content: space-between; 
                margin: 10px 0;
                padding: 8px;
                background: #f3f4f6;
                border-radius: 5px;
            }
            .metric-label { color: #6b7280; }
            .metric-value { font-weight: bold; color: #1f2937; }
            button {
                background: #667eea;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1em;
                transition: background 0.2s;
            }
            button:hover { background: #5a67d8; }
            .refresh-btn {
                position: fixed;
                bottom: 30px;
                right: 30px;
                border-radius: 50%;
                width: 60px;
                height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            }
            .chart {
                height: 200px;
                margin-top: 15px;
                background: #f9fafb;
                border-radius: 5px;
                display: flex;
                align-items: flex-end;
                padding: 10px;
                gap: 5px;
            }
            .bar {
                flex: 1;
                background: #667eea;
                border-radius: 3px 3px 0 0;
                min-height: 20px;
                position: relative;
            }
            .bar:hover { background: #5a67d8; }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            .loading { animation: pulse 1.5s infinite; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Sunbiz Supervisor Dashboard</h1>
            
            <div class="grid">
                <!-- Status Card -->
                <div class="card">
                    <h2>System Status</h2>
                    <div id="status-content" class="loading">Loading...</div>
                </div>
                
                <!-- Metrics Card -->
                <div class="card">
                    <h2>Performance Metrics</h2>
                    <div id="metrics-content" class="loading">Loading...</div>
                </div>
                
                <!-- Recent Tasks Card -->
                <div class="card">
                    <h2>Recent Tasks</h2>
                    <div id="tasks-content" class="loading">Loading...</div>
                </div>
                
                <!-- Health Status Card -->
                <div class="card">
                    <h2>Health Checks</h2>
                    <div id="health-content" class="loading">Loading...</div>
                </div>
                
                <!-- Daily Progress Card -->
                <div class="card">
                    <h2>Daily Progress</h2>
                    <div id="progress-content" class="loading">Loading...</div>
                    <div class="chart" id="daily-chart"></div>
                </div>
                
                <!-- Controls Card -->
                <div class="card">
                    <h2>Controls</h2>
                    <div style="display: flex; flex-direction: column; gap: 10px;">
                        <button onclick="triggerUpdate()">🔄 Trigger Daily Update</button>
                        <button onclick="runHealthCheck()">🏥 Run Health Check</button>
                        <button onclick="runAudit()">📊 Run Audit</button>
                        <button onclick="clearErrors()">🧹 Clear Errors</button>
                    </div>
                </div>
            </div>
        </div>
        
        <button class="refresh-btn" onclick="refreshDashboard()">🔄</button>
        
        <script>
            async function refreshDashboard() {
                // Fetch status
                fetch('/api/status')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('status-content').innerHTML = `
                            <div class="status ${data.status}">${data.status.toUpperCase()}</div>
                            <div class="metric">
                                <span class="metric-label">Uptime</span>
                                <span class="metric-value">${data.uptime}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Last Update</span>
                                <span class="metric-value">${data.last_update || 'Never'}</span>
                            </div>
                        `;
                    });
                
                // Fetch metrics
                fetch('/api/metrics')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('metrics-content').innerHTML = `
                            <div class="metric">
                                <span class="metric-label">Total Updates</span>
                                <span class="metric-value">${data.total_updates}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Success Rate</span>
                                <span class="metric-value">${data.success_rate}%</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Records Processed</span>
                                <span class="metric-value">${data.total_records.toLocaleString()}</span>
                            </div>
                        `;
                    });
                
                // Fetch recent tasks
                fetch('/api/tasks/recent')
                    .then(r => r.json())
                    .then(data => {
                        let html = '';
                        data.tasks.forEach(task => {
                            html += `
                                <div class="metric">
                                    <span class="metric-label">${task.task_name}</span>
                                    <span class="status ${task.status}">${task.status}</span>
                                </div>
                            `;
                        });
                        document.getElementById('tasks-content').innerHTML = html || 'No recent tasks';
                    });
                
                // Fetch health status
                fetch('/api/health')
                    .then(r => r.json())
                    .then(data => {
                        let html = '';
                        Object.entries(data.checks).forEach(([key, value]) => {
                            const status = value.includes('healthy') ? '✅' : '❌';
                            html += `
                                <div class="metric">
                                    <span class="metric-label">${key}</span>
                                    <span>${status} ${value}</span>
                                </div>
                            `;
                        });
                        document.getElementById('health-content').innerHTML = html;
                    });
                
                // Fetch daily progress
                fetch('/api/progress/daily')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('progress-content').innerHTML = `
                            <div class="metric">
                                <span class="metric-label">Files Today</span>
                                <span class="metric-value">${data.files_today}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Records Today</span>
                                <span class="metric-value">${data.records_today.toLocaleString()}</span>
                            </div>
                        `;
                        
                        // Update chart
                        let chartHTML = '';
                        data.hourly_data.forEach(hour => {
                            const height = (hour.count / data.max_count * 150) + 20;
                            chartHTML += `<div class="bar" style="height: ${height}px" title="${hour.hour}: ${hour.count} records"></div>`;
                        });
                        document.getElementById('daily-chart').innerHTML = chartHTML;
                    });
            }
            
            async function triggerUpdate() {
                if (confirm('Trigger daily update now?')) {
                    fetch('/api/tasks/trigger', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({task_name: 'daily_update'})
                    }).then(() => {
                        alert('Update triggered!');
                        refreshDashboard();
                    });
                }
            }
            
            async function runHealthCheck() {
                fetch('/api/health/check', {method: 'POST'})
                    .then(() => {
                        alert('Health check initiated!');
                        refreshDashboard();
                    });
            }
            
            async function runAudit() {
                if (confirm('Run comprehensive audit?')) {
                    fetch('/api/tasks/trigger', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({task_name: 'audit'})
                    }).then(() => alert('Audit started!'));
                }
            }
            
            async function clearErrors() {
                if (confirm('Clear all error logs?')) {
                    fetch('/api/errors/clear', {method: 'DELETE'})
                        .then(() => {
                            alert('Errors cleared!');
                            refreshDashboard();
                        });
                }
            }
            
            // Auto-refresh every 30 seconds
            setInterval(refreshDashboard, 30000);
            
            // Initial load
            refreshDashboard();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/status")
async def get_status():
    """Get current supervisor status"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT status, last_update, metrics
                FROM sunbiz_supervisor_status
                ORDER BY created_at DESC
                LIMIT 1
            """)
            result = cur.fetchone()
            
            if result:
                status, last_update, metrics = result
                
                # Calculate uptime
                if metrics and 'uptime_start' in metrics:
                    uptime_start = datetime.fromisoformat(metrics['uptime_start'])
                    uptime = str(datetime.now() - uptime_start).split('.')[0]
                else:
                    uptime = "Unknown"
                
                return {
                    "status": status,
                    "last_update": last_update.isoformat() if last_update else None,
                    "uptime": uptime,
                    "metrics": metrics
                }
        
        conn.close()
        return {"status": "unknown", "uptime": "0:00:00"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics")
async def get_metrics():
    """Get performance metrics"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get metrics from supervisor status
            cur.execute("""
                SELECT metrics
                FROM sunbiz_supervisor_status
                ORDER BY created_at DESC
                LIMIT 1
            """)
            result = cur.fetchone()
            
            if result and result[0]:
                metrics = result[0]
                
                # Calculate success rate
                total = metrics.get('total_updates', 0)
                successful = metrics.get('successful_updates', 0)
                success_rate = (successful / total * 100) if total > 0 else 0
                
                return {
                    "total_updates": total,
                    "successful_updates": successful,
                    "failed_updates": metrics.get('failed_updates', 0),
                    "total_records": metrics.get('total_records', 0),
                    "success_rate": round(success_rate, 1)
                }
        
        conn.close()
        return {
            "total_updates": 0,
            "successful_updates": 0,
            "failed_updates": 0,
            "total_records": 0,
            "success_rate": 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def get_health():
    """Get health check results"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT metric_type, is_healthy, details
                FROM sunbiz_health_metrics
                WHERE measured_at >= NOW() - INTERVAL '1 hour'
                ORDER BY measured_at DESC
            """)
            
            results = cur.fetchall()
            
            health_status = {
                "is_healthy": True,
                "checks": {},
                "timestamp": datetime.now().isoformat()
            }
            
            seen = set()
            for metric_type, is_healthy, details in results:
                if metric_type not in seen:
                    seen.add(metric_type)
                    health_status["checks"][metric_type] = (
                        "healthy" if is_healthy else f"unhealthy: {details.get('result', 'unknown')}"
                    )
                    if not is_healthy:
                        health_status["is_healthy"] = False
        
        conn.close()
        return health_status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/recent")
async def get_recent_tasks():
    """Get recent task executions"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT task_id, task_name, status, start_time, end_time, records_processed
                FROM sunbiz_task_log
                ORDER BY start_time DESC
                LIMIT 10
            """)
            
            tasks = []
            for row in cur.fetchall():
                task_id, task_name, status, start_time, end_time, records = row
                tasks.append({
                    "task_id": task_id,
                    "task_name": task_name,
                    "status": status,
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None,
                    "records_processed": records or 0
                })
        
        conn.close()
        return {"tasks": tasks}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/progress/daily")
async def get_daily_progress():
    """Get today's processing progress"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Today's stats
            cur.execute("""
                SELECT COUNT(*), COALESCE(SUM(records_processed), 0)
                FROM florida_daily_processed_files
                WHERE DATE(processed_at) = CURRENT_DATE
                AND status = 'completed'
            """)
            files_today, records_today = cur.fetchone()
            
            # Hourly breakdown
            cur.execute("""
                SELECT 
                    EXTRACT(HOUR FROM processed_at) as hour,
                    SUM(records_processed) as count
                FROM florida_daily_processed_files
                WHERE DATE(processed_at) = CURRENT_DATE
                GROUP BY EXTRACT(HOUR FROM processed_at)
                ORDER BY hour
            """)
            
            hourly_data = []
            max_count = 0
            for hour, count in cur.fetchall():
                hourly_data.append({"hour": int(hour), "count": count or 0})
                max_count = max(max_count, count or 0)
        
        conn.close()
        
        return {
            "files_today": files_today or 0,
            "records_today": int(records_today or 0),
            "hourly_data": hourly_data,
            "max_count": max_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks/trigger")
async def trigger_task(task: TaskRequest, background_tasks: BackgroundTasks):
    """Trigger a supervisor task"""
    # This would normally communicate with the supervisor agent
    # For now, we'll just log the request
    
    return {
        "message": f"Task '{task.task_name}' triggered",
        "task_id": f"{task.task_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }

@app.post("/api/health/check")
async def trigger_health_check():
    """Trigger immediate health check"""
    return {"message": "Health check initiated"}

@app.delete("/api/errors/clear")
async def clear_errors():
    """Clear error logs"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE sunbiz_task_log
                SET errors = NULL
                WHERE errors IS NOT NULL
            """)
            conn.commit()
        conn.close()
        
        return {"message": "Error logs cleared"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/config")
async def update_config(config: ConfigUpdate):
    """Update supervisor configuration"""
    # This would update the configuration file or database
    return {"message": "Configuration updated", "config": config.dict()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
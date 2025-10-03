#!/usr/bin/env python3
"""
Real-time Monitoring Dashboard Server for ConcordBroker AI System
Web-based dashboard for monitoring all AI agents, data flow, and system health
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os

# Web framework imports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import uvicorn

# Data processing
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

# Database and monitoring
import requests
import asyncpg
from sqlalchemy import text

# Local imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agents.sqlalchemy_models import DatabaseManager, initialize_database, MonitoringOperations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashboardDataCollector:
    """Collects data from various sources for dashboard display"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.monitoring_ops = MonitoringOperations(db_manager)
        self.data_cache = {}
        self.cache_timeout = 60  # 1 minute

    async def get_system_overview(self) -> Dict[str, Any]:
        """Get high-level system overview metrics"""
        try:
            # Check cache
            cache_key = "system_overview"
            if self._is_cache_valid(cache_key):
                return self.data_cache[cache_key]["data"]

            overview = {
                "timestamp": datetime.now().isoformat(),
                "system_health": await self._get_system_health(),
                "data_metrics": await self._get_data_metrics(),
                "agent_status": await self._get_agent_status(),
                "performance_metrics": await self._get_performance_metrics()
            }

            # Cache the result
            self.data_cache[cache_key] = {
                "data": overview,
                "timestamp": time.time()
            }

            return overview

        except Exception as e:
            logger.error(f"Error getting system overview: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            # Get recent validation results
            recent_validations = self.monitoring_ops.get_recent_metrics(hours=24)
            validation_summary = self.monitoring_ops.get_validation_summary(hours=24)

            # Calculate health score
            success_rate = validation_summary.get("summary", {}).get("success_rate", 0)

            if success_rate >= 95:
                health_status = "EXCELLENT"
                health_color = "green"
            elif success_rate >= 85:
                health_status = "GOOD"
                health_color = "yellow"
            elif success_rate >= 70:
                health_status = "WARNING"
                health_color = "orange"
            else:
                health_status = "CRITICAL"
                health_color = "red"

            return {
                "status": health_status,
                "score": success_rate,
                "color": health_color,
                "validation_summary": validation_summary
            }

        except Exception as e:
            return {
                "status": "ERROR",
                "score": 0,
                "color": "red",
                "error": str(e)
            }

    async def _get_data_metrics(self) -> Dict[str, Any]:
        """Get data-related metrics"""
        try:
            with self.db_manager.get_session() as session:
                # Property counts
                property_count = session.execute(text("SELECT COUNT(*) FROM florida_parcels")).scalar()

                # Sales count
                sales_count = session.execute(text("SELECT COUNT(*) FROM property_sales_history")).scalar()

                # Tax certificates count
                tax_cert_count = session.execute(text("SELECT COUNT(*) FROM tax_certificates")).scalar()

                # Recent activity (last 24 hours)
                recent_updates = session.execute(text("""
                    SELECT COUNT(*) FROM florida_parcels
                    WHERE updated_at >= NOW() - INTERVAL '24 hours'
                """)).scalar()

                return {
                    "total_properties": property_count,
                    "total_sales": sales_count,
                    "total_tax_certificates": tax_cert_count,
                    "recent_updates_24h": recent_updates,
                    "data_freshness": "fresh" if recent_updates > 0 else "stale"
                }

        except Exception as e:
            return {"error": str(e)}

    async def _get_agent_status(self) -> Dict[str, Any]:
        """Get AI agent status from the orchestrator"""
        try:
            # Try to get status from AI system API
            response = requests.get("http://localhost:8003/ai-system/status", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "AI system not responding", "status_code": response.status_code}

        except Exception as e:
            return {"error": f"Cannot connect to AI system: {str(e)}"}

    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            # Try to get performance data from data orchestrator
            response = requests.get("http://localhost:8001/performance", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "Performance service not responding"}

        except Exception as e:
            return {"error": f"Cannot get performance metrics: {str(e)}"}

    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for live dashboard updates"""
        try:
            current_time = datetime.now()

            # Get recent metrics from database
            recent_metrics = self.monitoring_ops.get_recent_metrics(hours=1)

            # Process metrics for charting
            metrics_by_type = {}
            for metric in recent_metrics:
                metric_type = metric.metric_type
                if metric_type not in metrics_by_type:
                    metrics_by_type[metric_type] = []

                metrics_by_type[metric_type].append({
                    "timestamp": metric.timestamp.isoformat(),
                    "value": metric.metric_value,
                    "table": metric.table_name
                })

            return {
                "timestamp": current_time.isoformat(),
                "metrics": metrics_by_type,
                "alert_count": await self._get_active_alert_count()
            }

        except Exception as e:
            logger.error(f"Error getting real-time metrics: {e}")
            return {"error": str(e)}

    async def _get_active_alert_count(self) -> int:
        """Get count of active alerts"""
        try:
            # This would check the AI system for active alerts
            response = requests.get("http://localhost:8003/ai-system/status", timeout=3)
            if response.status_code == 200:
                data = response.json()
                return data.get("summary", {}).get("total_alerts", 0)
            return 0
        except:
            return 0

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.data_cache:
            return False

        cache_age = time.time() - self.data_cache[key]["timestamp"]
        return cache_age < self.cache_timeout

    async def generate_dashboard_charts(self) -> Dict[str, Any]:
        """Generate chart data for the dashboard"""
        try:
            charts = {}

            # 1. System Health Trend Chart
            health_data = await self._get_health_trend_data()
            charts["health_trend"] = self._create_health_trend_chart(health_data)

            # 2. Data Volume Chart
            volume_data = await self._get_data_volume_trend()
            charts["data_volume"] = self._create_data_volume_chart(volume_data)

            # 3. Performance Chart
            performance_data = await self._get_performance_trend()
            charts["performance"] = self._create_performance_chart(performance_data)

            # 4. Agent Activity Chart
            agent_data = await self._get_agent_activity_data()
            charts["agent_activity"] = self._create_agent_activity_chart(agent_data)

            return charts

        except Exception as e:
            logger.error(f"Error generating charts: {e}")
            return {"error": str(e)}

    async def _get_health_trend_data(self) -> List[Dict]:
        """Get health trend data over time"""
        try:
            # Get validation results from last 24 hours
            recent_validations = self.monitoring_ops.get_recent_metrics(
                table_name="system_health",
                hours=24
            )

            # Group by hour and calculate success rate
            hourly_data = {}
            for metric in recent_validations:
                hour = metric.timestamp.replace(minute=0, second=0, microsecond=0)
                if hour not in hourly_data:
                    hourly_data[hour] = {"total": 0, "success": 0}

                hourly_data[hour]["total"] += 1
                if metric.metric_value > 0:  # Assuming 1 = success, 0 = failure
                    hourly_data[hour]["success"] += 1

            # Convert to chart data
            chart_data = []
            for hour, data in sorted(hourly_data.items()):
                success_rate = (data["success"] / data["total"] * 100) if data["total"] > 0 else 0
                chart_data.append({
                    "timestamp": hour.isoformat(),
                    "success_rate": success_rate
                })

            return chart_data

        except Exception as e:
            logger.error(f"Error getting health trend data: {e}")
            return []

    def _create_health_trend_chart(self, data: List[Dict]) -> str:
        """Create health trend chart"""
        if not data:
            return json.dumps({})

        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['success_rate'],
            mode='lines+markers',
            name='System Health %',
            line=dict(color='green', width=3),
            marker=dict(size=6)
        ))

        fig.update_layout(
            title="System Health Trend (24 Hours)",
            xaxis_title="Time",
            yaxis_title="Success Rate (%)",
            yaxis=dict(range=[0, 100]),
            template="plotly_white",
            height=300
        )

        return json.dumps(fig, cls=PlotlyJSONEncoder)

    async def _get_data_volume_trend(self) -> List[Dict]:
        """Get data volume trend"""
        try:
            with self.db_manager.get_session() as session:
                # Get daily counts for the last 7 days
                query = text("""
                    SELECT
                        DATE(created_at) as date,
                        COUNT(*) as count,
                        'properties' as type
                    FROM florida_parcels
                    WHERE created_at >= NOW() - INTERVAL '7 days'
                    GROUP BY DATE(created_at)
                    UNION ALL
                    SELECT
                        DATE(created_at) as date,
                        COUNT(*) as count,
                        'sales' as type
                    FROM property_sales_history
                    WHERE created_at >= NOW() - INTERVAL '7 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """)

                result = session.execute(query).fetchall()
                return [{"date": row.date.isoformat(), "count": row.count, "type": row.type} for row in result]

        except Exception as e:
            logger.error(f"Error getting data volume trend: {e}")
            return []

    def _create_data_volume_chart(self, data: List[Dict]) -> str:
        """Create data volume chart"""
        if not data:
            return json.dumps({})

        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])

        fig = go.Figure()

        for data_type in df['type'].unique():
            type_data = df[df['type'] == data_type]
            fig.add_trace(go.Scatter(
                x=type_data['date'],
                y=type_data['count'],
                mode='lines+markers',
                name=f'{data_type.title()} Added',
                line=dict(width=2),
                marker=dict(size=5)
            ))

        fig.update_layout(
            title="Data Volume Trend (7 Days)",
            xaxis_title="Date",
            yaxis_title="Records Added",
            template="plotly_white",
            height=300
        )

        return json.dumps(fig, cls=PlotlyJSONEncoder)

    async def _get_performance_trend(self) -> List[Dict]:
        """Get performance trend data"""
        try:
            # Get query time metrics from the last 6 hours
            recent_metrics = self.monitoring_ops.get_recent_metrics(hours=6)
            query_time_metrics = [m for m in recent_metrics if m.metric_type == "query_time"]

            # Group by 30-minute intervals
            performance_data = []
            for metric in query_time_metrics:
                performance_data.append({
                    "timestamp": metric.timestamp.isoformat(),
                    "query_time": metric.metric_value,
                    "table": metric.table_name
                })

            return performance_data

        except Exception as e:
            logger.error(f"Error getting performance trend: {e}")
            return []

    def _create_performance_chart(self, data: List[Dict]) -> str:
        """Create performance chart"""
        if not data:
            return json.dumps({})

        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['query_time'],
            mode='lines+markers',
            name='Query Time (ms)',
            line=dict(color='blue', width=2),
            marker=dict(size=4)
        ))

        fig.update_layout(
            title="Query Performance Trend",
            xaxis_title="Time",
            yaxis_title="Query Time (ms)",
            template="plotly_white",
            height=300
        )

        return json.dumps(fig, cls=PlotlyJSONEncoder)

    async def _get_agent_activity_data(self) -> List[Dict]:
        """Get agent activity data"""
        try:
            # This would get data from the AI system about agent activity
            response = requests.get("http://localhost:8003/ai-system/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                agents = data.get("services", {}).get("agents", {}).get("agents", [])

                activity_data = []
                for agent in agents:
                    activity_data.append({
                        "agent_name": agent.get("agent_name", "Unknown"),
                        "status": agent.get("status", "Unknown"),
                        "alerts_count": agent.get("alerts_count", 0),
                        "last_check": agent.get("last_check", "")
                    })

                return activity_data

            return []

        except Exception as e:
            logger.error(f"Error getting agent activity: {e}")
            return []

    def _create_agent_activity_chart(self, data: List[Dict]) -> str:
        """Create agent activity chart"""
        if not data:
            return json.dumps({})

        df = pd.DataFrame(data)

        # Create a status distribution chart
        status_counts = df['status'].value_counts()

        fig = go.Figure(data=[go.Pie(
            labels=status_counts.index,
            values=status_counts.values,
            hole=0.4
        )])

        fig.update_layout(
            title="Agent Status Distribution",
            template="plotly_white",
            height=300
        )

        return json.dumps(fig, cls=PlotlyJSONEncoder)

class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return

        message_str = json.dumps(message, default=str)
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except:
                disconnected.append(connection)

        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

# Initialize FastAPI app
app = FastAPI(title="ConcordBroker AI Monitoring Dashboard", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db_manager = None
data_collector = None
websocket_manager = WebSocketManager()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global db_manager, data_collector

    try:
        # Initialize database connection
        db_manager = initialize_database()
        data_collector = DashboardDataCollector(db_manager)

        # Start background task for real-time updates
        asyncio.create_task(background_update_task())

        logger.info("✅ Dashboard server initialized")

    except Exception as e:
        logger.error(f"❌ Dashboard server initialization failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global db_manager

    if db_manager:
        db_manager.close()

    logger.info("✅ Dashboard server shutdown complete")

# Static files and templates
current_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

# Create static directory if it doesn't exist
static_dir = os.path.join(current_dir, "static")
os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/dashboard/overview")
async def get_dashboard_overview():
    """Get dashboard overview data"""
    if not data_collector:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    overview = await data_collector.get_system_overview()
    return overview

@app.get("/api/dashboard/charts")
async def get_dashboard_charts():
    """Get chart data for dashboard"""
    if not data_collector:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    charts = await data_collector.generate_dashboard_charts()
    return charts

@app.get("/api/dashboard/real-time")
async def get_real_time_data():
    """Get real-time metrics"""
    if not data_collector:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    metrics = await data_collector.get_real_time_metrics()
    return metrics

@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await websocket_manager.connect(websocket)

    try:
        while True:
            # Keep connection alive and listen for client messages
            await websocket.receive_text()

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

async def background_update_task():
    """Background task to send real-time updates to connected clients"""
    while True:
        try:
            if data_collector and websocket_manager.active_connections:
                # Get real-time data
                real_time_data = await data_collector.get_real_time_metrics()

                # Broadcast to all connected clients
                await websocket_manager.broadcast({
                    "type": "real_time_update",
                    "data": real_time_data
                })

            # Wait 10 seconds before next update
            await asyncio.sleep(10)

        except Exception as e:
            logger.error(f"Error in background update task: {e}")
            await asyncio.sleep(30)  # Wait longer on error

# Create dashboard HTML template
def create_dashboard_template():
    """Create the dashboard HTML template"""
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    os.makedirs(template_dir, exist_ok=True)

    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ConcordBroker AI Monitoring Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .status-indicator {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 10px;
        }
        .status-excellent { background-color: #4CAF50; }
        .status-good { background-color: #8BC34A; }
        .status-warning { background-color: #FF9800; }
        .status-critical { background-color: #F44336; }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }
        .metric-label {
            color: #666;
            margin-top: 5px;
        }
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
        }
        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
        }
        .connected { background-color: #4CAF50; }
        .disconnected { background-color: #F44336; }
        .alert-banner {
            background-color: #ff9800;
            color: white;
            padding: 10px;
            text-align: center;
            border-radius: 5px;
            margin-bottom: 20px;
            display: none;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="connection-status" id="connectionStatus">Connecting...</div>

    <div class="header">
        <h1>🤖 ConcordBroker AI Monitoring Dashboard</h1>
        <p>Real-time monitoring of data flow, AI agents, and system health</p>
        <p id="lastUpdate">Last updated: Loading...</p>
    </div>

    <div class="alert-banner" id="alertBanner">
        <strong>⚠️ System Alert:</strong> <span id="alertMessage"></span>
    </div>

    <div class="status-grid" id="statusGrid">
        <div class="loading">Loading system status...</div>
    </div>

    <div class="charts-grid" id="chartsGrid">
        <div class="loading">Loading charts...</div>
    </div>

    <script>
        let ws = null;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;

        // Initialize dashboard
        async function initDashboard() {
            await loadOverview();
            await loadCharts();
            connectWebSocket();

            // Auto-refresh every 30 seconds
            setInterval(async () => {
                await loadOverview();
                await loadCharts();
            }, 30000);
        }

        // Load overview data
        async function loadOverview() {
            try {
                const response = await fetch('/api/dashboard/overview');
                const data = await response.json();

                if (data.error) {
                    showAlert(data.error);
                    return;
                }

                updateStatusGrid(data);
                document.getElementById('lastUpdate').textContent =
                    `Last updated: ${new Date(data.timestamp).toLocaleString()}`;

            } catch (error) {
                console.error('Error loading overview:', error);
                showAlert('Failed to load system overview');
            }
        }

        // Update status grid
        function updateStatusGrid(data) {
            const grid = document.getElementById('statusGrid');
            const systemHealth = data.system_health || {};
            const dataMetrics = data.data_metrics || {};
            const agentStatus = data.agent_status || {};
            const performance = data.performance_metrics || {};

            grid.innerHTML = `
                <div class="status-card">
                    <div class="metric-label">
                        <span class="status-indicator status-${systemHealth.color || 'critical'}"></span>
                        System Health
                    </div>
                    <div class="metric-value">${systemHealth.score || 0}%</div>
                    <div class="metric-label">${systemHealth.status || 'Unknown'}</div>
                </div>

                <div class="status-card">
                    <div class="metric-label">Total Properties</div>
                    <div class="metric-value">${(dataMetrics.total_properties || 0).toLocaleString()}</div>
                    <div class="metric-label">Florida Parcels Database</div>
                </div>

                <div class="status-card">
                    <div class="metric-label">Sales Records</div>
                    <div class="metric-value">${(dataMetrics.total_sales || 0).toLocaleString()}</div>
                    <div class="metric-label">Transaction History</div>
                </div>

                <div class="status-card">
                    <div class="metric-label">Tax Certificates</div>
                    <div class="metric-value">${(dataMetrics.total_tax_certificates || 0).toLocaleString()}</div>
                    <div class="metric-label">Active Liens</div>
                </div>

                <div class="status-card">
                    <div class="metric-label">AI Agents</div>
                    <div class="metric-value">${agentStatus.summary?.active_agents || 0}</div>
                    <div class="metric-label">Active Monitoring</div>
                </div>

                <div class="status-card">
                    <div class="metric-label">Active Alerts</div>
                    <div class="metric-value">${agentStatus.summary?.total_alerts || 0}</div>
                    <div class="metric-label">Require Attention</div>
                </div>
            `;
        }

        // Load charts
        async function loadCharts() {
            try {
                const response = await fetch('/api/dashboard/charts');
                const charts = await response.json();

                if (charts.error) {
                    console.error('Charts error:', charts.error);
                    return;
                }

                updateCharts(charts);

            } catch (error) {
                console.error('Error loading charts:', error);
            }
        }

        // Update charts
        function updateCharts(charts) {
            const grid = document.getElementById('chartsGrid');

            grid.innerHTML = `
                <div class="chart-container">
                    <div id="healthChart"></div>
                </div>
                <div class="chart-container">
                    <div id="volumeChart"></div>
                </div>
                <div class="chart-container">
                    <div id="performanceChart"></div>
                </div>
                <div class="chart-container">
                    <div id="agentChart"></div>
                </div>
            `;

            // Render charts
            if (charts.health_trend) {
                Plotly.newPlot('healthChart', JSON.parse(charts.health_trend));
            }
            if (charts.data_volume) {
                Plotly.newPlot('volumeChart', JSON.parse(charts.data_volume));
            }
            if (charts.performance) {
                Plotly.newPlot('performanceChart', JSON.parse(charts.performance));
            }
            if (charts.agent_activity) {
                Plotly.newPlot('agentChart', JSON.parse(charts.agent_activity));
            }
        }

        // WebSocket connection
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;

            ws = new WebSocket(wsUrl);

            ws.onopen = function() {
                console.log('WebSocket connected');
                updateConnectionStatus(true);
                reconnectAttempts = 0;
            };

            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                if (message.type === 'real_time_update') {
                    handleRealTimeUpdate(message.data);
                }
            };

            ws.onclose = function() {
                console.log('WebSocket disconnected');
                updateConnectionStatus(false);

                if (reconnectAttempts < maxReconnectAttempts) {
                    setTimeout(() => {
                        reconnectAttempts++;
                        connectWebSocket();
                    }, 2000 * reconnectAttempts);
                }
            };

            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }

        // Handle real-time updates
        function handleRealTimeUpdate(data) {
            // Update any real-time elements here
            console.log('Real-time update:', data);

            if (data.alert_count && data.alert_count > 0) {
                showAlert(`${data.alert_count} active system alerts`);
            }
        }

        // Update connection status
        function updateConnectionStatus(connected) {
            const status = document.getElementById('connectionStatus');
            if (connected) {
                status.textContent = 'Connected';
                status.className = 'connection-status connected';
            } else {
                status.textContent = 'Disconnected';
                status.className = 'connection-status disconnected';
            }
        }

        // Show alert banner
        function showAlert(message) {
            const banner = document.getElementById('alertBanner');
            const messageSpan = document.getElementById('alertMessage');
            messageSpan.textContent = message;
            banner.style.display = 'block';

            // Auto-hide after 10 seconds
            setTimeout(() => {
                banner.style.display = 'none';
            }, 10000);
        }

        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', initDashboard);
    </script>
</body>
</html>'''

    template_path = os.path.join(template_dir, "dashboard.html")
    with open(template_path, 'w') as f:
        f.write(html_content)

    logger.info(f"✅ Created dashboard template: {template_path}")
    return template_path

# Main entry point
async def main():
    """Main entry point for testing the dashboard"""
    try:
        # Create dashboard template
        create_dashboard_template()

        logger.info("🚀 Starting ConcordBroker AI Monitoring Dashboard...")
        logger.info("📊 Dashboard will be available at: http://localhost:8004")
        logger.info("🔄 Real-time updates via WebSocket")

        # Start the dashboard server
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8004,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

    except Exception as e:
        logger.error(f"❌ Dashboard server failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Create template on import
    create_dashboard_template()
    asyncio.run(main())
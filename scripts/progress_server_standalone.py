#!/usr/bin/env python3
"""
Real-time Progress Monitoring Server (Standalone)
Optimized for 16GB RAM / 4-core ARM CPU Supabase
"""
import os
import requests
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Supabase REST API configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0')

def query_supabase(table, filters=None, order=None, limit=None):
    """Query Supabase via REST API"""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json'
    }

    params = {}
    if filters:
        for key, value in filters.items():
            params[key] = f'eq.{value}'
    if order:
        params['order'] = order
    if limit:
        params['limit'] = limit

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

# HTML Template with real-time progress bars
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>2023 NAL Upload - Live Progress</title>
    <meta http-equiv="refresh" content="5">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }
        h1 {
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .subtitle {
            text-align: center;
            margin-bottom: 40px;
            opacity: 0.9;
            font-size: 1.1em;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.15);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
            margin-bottom: 10px;
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .progress-section {
            background: rgba(255, 255, 255, 0.15);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 20px;
        }
        .progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .progress-title {
            font-size: 1.3em;
            font-weight: bold;
        }
        .progress-percent {
            font-size: 2em;
            font-weight: bold;
        }
        .progress-bar-container {
            width: 100%;
            height: 40px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 20px;
            overflow: hidden;
            position: relative;
        }
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
            border-radius: 20px;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.1em;
        }
        .progress-details {
            margin-top: 15px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }
        .detail-item {
            background: rgba(0, 0, 0, 0.2);
            padding: 10px 15px;
            border-radius: 10px;
        }
        .detail-label {
            font-size: 0.85em;
            opacity: 0.8;
        }
        .detail-value {
            font-size: 1.1em;
            font-weight: bold;
            margin-top: 5px;
        }
        .hardware-info {
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 15px;
        }
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            background: #00ff88;
            color: #000;
            font-weight: bold;
            font-size: 0.9em;
        }
        .loading {
            text-align: center;
            padding: 40px;
            font-size: 1.5em;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .pulse {
            animation: pulse 2s infinite;
        }
        .county-breakdown {
            background: rgba(255, 255, 255, 0.15);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 20px;
        }
        .county-breakdown-title {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 20px;
            text-align: center;
        }
        .county-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 10px;
        }
        .county-item {
            background: rgba(0, 0, 0, 0.2);
            padding: 12px 15px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .county-item.completed {
            background: rgba(0, 255, 136, 0.15);
            border-left: 3px solid #00ff88;
        }
        .county-item.current {
            background: rgba(0, 210, 255, 0.15);
            border-left: 3px solid #00d2ff;
            animation: pulse 2s infinite;
        }
        .county-icon {
            font-size: 1.2em;
        }
        .county-name {
            font-weight: 600;
            font-size: 0.95em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>2023 NAL Historical Data Upload</h1>
        <div class="subtitle">
            <span class="status-badge">LIVE</span> Real-time Progress Monitor
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Overall Progress</div>
                <div class="stat-value" id="overall-percent">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Files Processed</div>
                <div class="stat-value" id="files-done">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Rows</div>
                <div class="stat-value" id="total-rows">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Current County</div>
                <div class="stat-value" id="current-county" style="font-size: 1.8em;">--</div>
            </div>
        </div>

        <div class="progress-section">
            <div class="progress-header">
                <div class="progress-title">Upload Progress</div>
                <div class="progress-percent" id="progress-percent">0%</div>
            </div>
            <div class="progress-bar-container">
                <div class="progress-bar" id="progress-bar" style="width: 0%">
                    <span id="bar-text"></span>
                </div>
            </div>
            <div class="progress-details">
                <div class="detail-item">
                    <div class="detail-label">Current Phase</div>
                    <div class="detail-value" id="current-phase">--</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Elapsed Time</div>
                    <div class="detail-value" id="elapsed-time">--</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Est. Remaining</div>
                    <div class="detail-value" id="est-remaining">--</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Upload Speed</div>
                    <div class="detail-value" id="upload-speed">--</div>
                </div>
            </div>
        </div>

        <div class="county-breakdown">
            <div class="county-breakdown-title">County Breakdown</div>
            <div class="county-list" id="county-list">
                <!-- Counties will be populated dynamically -->
            </div>
        </div>

        <div class="hardware-info">
            <strong>Optimized for:</strong> 16GB RAM / 4-core ARM CPU / 150GB Disk<br>
            <strong>Batch Size:</strong> 1,500 rows | <strong>Total Files:</strong> 201 (67 counties × P/S/F)
        </div>

        <div class="loading pulse" id="loading">Loading progress data...</div>
    </div>

    <script>
        let startTime = null;

        async function updateProgress() {
            try {
                const response = await fetch('/api/progress');
                const data = await response.json();

                if (data.error) {
                    document.getElementById('loading').innerHTML = 'Error: ' + data.error;
                    return;
                }

                document.getElementById('loading').style.display = 'none';

                // Update stats
                document.getElementById('overall-percent').innerText = data.percent + '%';
                document.getElementById('files-done').innerText = data.done + '/' + data.total;
                document.getElementById('total-rows').innerText = (data.total_rows || 0).toLocaleString();
                document.getElementById('current-county').innerText = data.county || '--';

                // Update progress bar
                document.getElementById('progress-percent').innerText = data.percent + '%';
                document.getElementById('progress-bar').style.width = data.percent + '%';
                document.getElementById('bar-text').innerText = data.done + '/' + data.total + ' files';

                // Update details
                document.getElementById('current-phase').innerText = data.current || '--';

                // Calculate elapsed time
                if (!startTime && data.percent > 0) {
                    startTime = Date.now();
                }
                if (startTime) {
                    const elapsed = Math.floor((Date.now() - startTime) / 1000 / 60);
                    document.getElementById('elapsed-time').innerText = elapsed + ' min';

                    // Estimate remaining
                    if (data.percent > 0) {
                        const totalMin = (elapsed / data.percent) * 100;
                        const remaining = Math.floor(totalMin - elapsed);
                        document.getElementById('est-remaining').innerText = remaining + ' min';
                    }
                }

                // Upload speed (rows per second estimate)
                if (data.total_rows && startTime) {
                    const elapsedSec = (Date.now() - startTime) / 1000;
                    const rowsPerSec = Math.floor(data.total_rows / elapsedSec);
                    document.getElementById('upload-speed').innerText = rowsPerSec.toLocaleString() + ' rows/s';
                }

                // Update county breakdown
                const countyList = document.getElementById('county-list');
                if (data.recent_counties && data.recent_counties.length > 0) {
                    let html = '';

                    // Add current county first (if available)
                    if (data.county) {
                        html += `
                            <div class="county-item current">
                                <div class="county-icon">⏳</div>
                                <div class="county-name">${data.county}</div>
                            </div>
                        `;
                    }

                    // Add recently completed counties
                    data.recent_counties.forEach(county => {
                        html += `
                            <div class="county-item completed">
                                <div class="county-icon">✅</div>
                                <div class="county-name">${county.name}</div>
                            </div>
                        `;
                    });

                    countyList.innerHTML = html;
                } else if (data.county) {
                    // If no recent counties but current county exists
                    countyList.innerHTML = `
                        <div class="county-item current">
                            <div class="county-icon">⏳</div>
                            <div class="county-name">${data.county}</div>
                        </div>
                    `;
                }

            } catch (error) {
                document.getElementById('loading').innerHTML = 'Connection error: ' + error.message;
            }
        }

        // Update every 2 seconds
        setInterval(updateProgress, 2000);
        updateProgress();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/progress')
def get_progress():
    """Get latest progress from ingestion_progress table via Supabase REST API"""
    try:
        # Get latest progress for the current run
        progress_data = query_supabase(
            'ingestion_progress',
            filters={'run_id': '2023-full-load-v2'},
            order='created_at.desc',
            limit=1
        )

        if not progress_data or len(progress_data) == 0:
            return jsonify({
                'percent': 0,
                'done': 0,
                'total': 201,
                'county': None,
                'current': 'Initializing...',
                'total_rows': 0,
                'recent_counties': []
            })

        row = progress_data[0]

        # Get total rows uploaded so far (using PostgREST count)
        # For count, we need a special header
        url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
        headers = {
            'apikey': SUPABASE_SERVICE_ROLE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
            'Prefer': 'count=exact'
        }
        params = {'year': 'eq.2023', 'select': 'id'}  # Just count, don't fetch data

        response = requests.head(url, headers=headers, params=params)
        # PostgREST returns count in Content-Range header
        content_range = response.headers.get('Content-Range', '*/0')
        total_rows = int(content_range.split('/')[-1]) if content_range != '*/0' else 0

        # Get recent county history (last 10 completed)
        recent_data = query_supabase(
            'ingestion_progress',
            filters={'run_id': '2023-full-load-v2'},
            order='created_at.desc',
            limit=10
        )

        recent_counties = []
        for r in recent_data:
            if r.get('current') and 'ingested:' in r.get('current', ''):
                county_name = r.get('county')
                if county_name and county_name not in [rc['name'] for rc in recent_counties]:
                    recent_counties.append({
                        'name': county_name,
                        'status': 'completed'
                    })

        return jsonify({
            'percent': row.get('percent') or 0,
            'done': row.get('done') or 0,
            'total': row.get('total') or 201,
            'county': row.get('county'),
            'current': row.get('current'),
            'total_rows': total_rows,
            'timestamp': row.get('created_at'),
            'run_id': row.get('run_id'),
            'recent_counties': recent_counties[:6]  # Last 6 counties
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print('Starting Progress Monitor Server...')
    print('Open http://localhost:5555 in your browser')
    app.run(host='0.0.0.0', port=5555, debug=False)

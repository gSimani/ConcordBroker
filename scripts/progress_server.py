#!/usr/bin/env python3
"""
Real-time Progress Monitoring Server
Optimized for 16GB RAM / 4-core ARM CPU Supabase
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
from scripts.integrate_historical_data_psycopg2 import HistoricalDataIntegratorPG
import json

app = Flask(__name__)
CORS(app)

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
    """Get latest progress from ingestion_progress table"""
    ing = HistoricalDataIntegratorPG()
    if not ing.connect():
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        # Get latest progress for the current run
        ing.cursor.execute('''
            SELECT
                created_at,
                county,
                done,
                total,
                percent,
                current,
                run_id
            FROM public.ingestion_progress
            WHERE run_id = '2023-full-load-v2'
            ORDER BY created_at DESC
            LIMIT 1
        ''')

        row = ing.cursor.fetchone()

        if not row:
            return jsonify({
                'percent': 0,
                'done': 0,
                'total': 201,
                'county': None,
                'current': 'Initializing...',
                'total_rows': 0
            })

        timestamp, county, done, total, percent, current, run_id = row

        # Get total rows uploaded so far
        ing.cursor.execute('''
            SELECT COUNT(*)
            FROM public.florida_parcels
            WHERE year = 2023
        ''')
        total_rows = ing.cursor.fetchone()[0]

        return jsonify({
            'percent': percent or 0,
            'done': done or 0,
            'total': total or 201,
            'county': county,
            'current': current,
            'total_rows': total_rows,
            'timestamp': timestamp.isoformat() if timestamp else None,
            'run_id': run_id
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        ing.disconnect()

if __name__ == '__main__':
    print('Starting Progress Monitor Server...')
    print('Open http://localhost:5555 in your browser')
    app.run(host='0.0.0.0', port=5555, debug=False)

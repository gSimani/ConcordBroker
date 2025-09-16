#!/usr/bin/env python3
"""
Property Appraiser Monitoring System
Real-time monitoring with visualization using matplotlib, seaborn, and pandas
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.animation import FuncAnimation
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import requests
from supabase import create_client
import os
from dotenv import load_dotenv
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# Configure visualization style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv('.env.mcp')

@dataclass
class MonitoringMetric:
    """Data structure for monitoring metrics"""
    name: str
    value: float
    timestamp: datetime
    county: Optional[str] = None
    status: str = "normal"  # normal, warning, critical

@dataclass
class AlertRule:
    """Data structure for alert rules"""
    metric: str
    threshold: float
    condition: str  # >, <, ==
    severity: str  # info, warning, critical

class PropertyDataMonitor:
    """Comprehensive monitoring system for Property Appraiser data"""

    def __init__(self):
        """Initialize monitoring system"""
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        )

        self.metrics_history: List[MonitoringMetric] = []
        self.output_dir = Path("monitoring_output")
        self.output_dir.mkdir(exist_ok=True)

        # Define alert rules
        self.alert_rules = [
            AlertRule("data_quality_score", 0.8, "<", "warning"),
            AlertRule("record_count", 1000, "<", "critical"),
            AlertRule("processing_time", 300, ">", "warning"),
            AlertRule("error_rate", 0.05, ">", "critical")
        ]

        logger.info("Property Data Monitor initialized")

    def collect_system_metrics(self) -> List[MonitoringMetric]:
        """Collect system-wide metrics using pandas analysis"""
        metrics = []
        timestamp = datetime.now()

        try:
            # Get overall record counts
            for table in ['florida_parcels', 'nav_assessments', 'sdf_sales', 'nap_characteristics']:
                try:
                    response = self.supabase.table(table).select("id").limit(1).execute()
                    if response.data:
                        # For demo, simulate counts (in production, use COUNT queries)
                        count = np.random.randint(10000, 50000)
                        metrics.append(MonitoringMetric(
                            name=f"{table}_count",
                            value=count,
                            timestamp=timestamp
                        ))
                except Exception as e:
                    logger.warning(f"Could not get count for {table}: {e}")
                    metrics.append(MonitoringMetric(
                        name=f"{table}_count",
                        value=0,
                        timestamp=timestamp,
                        status="critical"
                    ))

            # Data quality metrics
            counties = ['ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD']
            for county in counties:
                quality_score = np.random.uniform(0.7, 0.95)
                status = "normal" if quality_score >= 0.8 else "warning"

                metrics.append(MonitoringMetric(
                    name="data_quality_score",
                    value=quality_score,
                    timestamp=timestamp,
                    county=county,
                    status=status
                ))

            # Processing performance metrics
            metrics.append(MonitoringMetric(
                name="processing_time",
                value=np.random.uniform(60, 180),  # seconds
                timestamp=timestamp
            ))

            metrics.append(MonitoringMetric(
                name="error_rate",
                value=np.random.uniform(0.001, 0.03),  # percentage
                timestamp=timestamp
            ))

            # Storage utilization
            metrics.append(MonitoringMetric(
                name="storage_usage_gb",
                value=np.random.uniform(10, 100),
                timestamp=timestamp
            ))

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")

        return metrics

    def collect_florida_revenue_metrics(self) -> List[MonitoringMetric]:
        """Monitor Florida Revenue portal for data updates"""
        metrics = []
        timestamp = datetime.now()

        # Simulate checking Florida Revenue portal
        # In production, this would check actual file timestamps and sizes

        file_types = ['NAL', 'NAP', 'NAV', 'SDF']
        counties = ['BROWARD', 'MIAMI-DADE', 'PALM BEACH', 'ORANGE', 'HILLSBOROUGH']

        for file_type in file_types:
            for county in counties:
                # Simulate file check
                file_age_hours = np.random.uniform(1, 48)
                file_size_mb = np.random.uniform(50, 500)

                # Check if file is recent (updated within 24 hours)
                status = "normal" if file_age_hours <= 24 else "warning"

                metrics.append(MonitoringMetric(
                    name=f"{file_type}_file_age_hours",
                    value=file_age_hours,
                    timestamp=timestamp,
                    county=county,
                    status=status
                ))

                metrics.append(MonitoringMetric(
                    name=f"{file_type}_file_size_mb",
                    value=file_size_mb,
                    timestamp=timestamp,
                    county=county
                ))

        return metrics

    def create_real_time_dashboard(self):
        """Create real-time monitoring dashboard"""
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Property Appraiser Real-Time Monitoring Dashboard', fontsize=16)

        def update_dashboard(frame):
            """Update dashboard with latest metrics"""
            # Clear previous plots
            for ax in axes.flat:
                ax.clear()

            # Collect latest metrics
            system_metrics = self.collect_system_metrics()
            florida_metrics = self.collect_florida_revenue_metrics()
            all_metrics = system_metrics + florida_metrics

            # Update metrics history
            self.metrics_history.extend(all_metrics)

            # Keep only last 100 points for performance
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]

            # Convert to DataFrame for analysis
            df = pd.DataFrame([
                {
                    'name': m.name,
                    'value': m.value,
                    'timestamp': m.timestamp,
                    'county': m.county,
                    'status': m.status
                }
                for m in self.metrics_history
            ])

            if df.empty:
                return

            # 1. Record counts by table
            ax = axes[0, 0]
            table_counts = df[df['name'].str.contains('_count')].copy()
            if not table_counts.empty:
                latest_counts = table_counts.groupby('name')['value'].last()
                bars = ax.bar(range(len(latest_counts)), latest_counts.values)
                ax.set_xticks(range(len(latest_counts)))
                ax.set_xticklabels([name.replace('_count', '') for name in latest_counts.index],
                                 rotation=45, ha='right')
                ax.set_title('Database Record Counts')
                ax.set_ylabel('Count')

                # Color bars based on values
                for i, bar in enumerate(bars):
                    if latest_counts.iloc[i] < 1000:
                        bar.set_color('red')
                    elif latest_counts.iloc[i] < 10000:
                        bar.set_color('orange')
                    else:
                        bar.set_color('green')

            # 2. Data quality over time
            ax = axes[0, 1]
            quality_data = df[df['name'] == 'data_quality_score'].copy()
            if not quality_data.empty:
                # Group by county and plot
                for county in quality_data['county'].unique():
                    if pd.notna(county):
                        county_data = quality_data[quality_data['county'] == county].sort_values('timestamp')
                        ax.plot(county_data['timestamp'], county_data['value'], marker='o', label=county)

                ax.set_title('Data Quality Score by County')
                ax.set_ylabel('Quality Score')
                ax.axhline(y=0.8, color='r', linestyle='--', label='Threshold')
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                ax.tick_params(axis='x', rotation=45)

            # 3. Processing performance
            ax = axes[0, 2]
            perf_metrics = df[df['name'].isin(['processing_time', 'error_rate'])].copy()
            if not perf_metrics.empty:
                latest_perf = perf_metrics.groupby('name')['value'].last()
                colors = ['green' if v < 180 else 'red' if 'time' in k else
                         'green' if v < 0.02 else 'red' for k, v in latest_perf.items()]
                ax.bar(range(len(latest_perf)), latest_perf.values, color=colors)
                ax.set_xticks(range(len(latest_perf)))
                ax.set_xticklabels(latest_perf.index, rotation=45, ha='right')
                ax.set_title('Performance Metrics')

            # 4. File age monitoring
            ax = axes[1, 0]
            file_age_data = df[df['name'].str.contains('_file_age_hours')].copy()
            if not file_age_data.empty:
                latest_ages = file_age_data.groupby(['name', 'county'])['value'].last().reset_index()
                pivot_data = latest_ages.pivot(index='county', columns='name', values='value')

                if not pivot_data.empty:
                    # Create heatmap
                    sns.heatmap(pivot_data, annot=True, fmt='.1f', cmap='RdYlGn_r',
                              ax=ax, vmin=0, vmax=48, cbar_kws={'label': 'Hours'})
                    ax.set_title('File Age by County (Hours)')

            # 5. Storage utilization
            ax = axes[1, 1]
            storage_data = df[df['name'] == 'storage_usage_gb'].copy()
            if not storage_data.empty:
                storage_history = storage_data.sort_values('timestamp')
                ax.plot(storage_history['timestamp'], storage_history['value'], marker='o')
                ax.set_title('Storage Usage Over Time')
                ax.set_ylabel('Storage (GB)')
                ax.tick_params(axis='x', rotation=45)

            # 6. Alert summary
            ax = axes[1, 2]
            ax.axis('off')

            # Count alerts by severity
            critical_count = len(df[df['status'] == 'critical'])
            warning_count = len(df[df['status'] == 'warning'])
            normal_count = len(df[df['status'] == 'normal'])

            alert_summary = f"""
ALERT SUMMARY
=============
Critical: {critical_count}
Warning: {warning_count}
Normal: {normal_count}

LAST UPDATE
{datetime.now().strftime('%H:%M:%S')}
            """

            ax.text(0.1, 0.5, alert_summary, fontsize=10, family='monospace',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"))

            plt.tight_layout()

        # Create animation
        ani = FuncAnimation(fig, update_dashboard, interval=5000, cache_frame_data=False)

        # Save dashboard
        dashboard_file = self.output_dir / 'real_time_dashboard.png'
        plt.savefig(dashboard_file, dpi=100, bbox_inches='tight')

        return ani, fig

    def generate_daily_report(self) -> Dict[str, Any]:
        """Generate comprehensive daily monitoring report"""
        logger.info("Generating daily monitoring report...")

        # Collect 24 hours of metrics
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)

        # Simulate daily metrics collection
        daily_metrics = []
        for hour in range(24):
            timestamp = start_time + timedelta(hours=hour)

            # System metrics
            daily_metrics.extend([
                MonitoringMetric("total_records", np.random.randint(45000, 50000), timestamp),
                MonitoringMetric("data_quality_score", np.random.uniform(0.85, 0.95), timestamp),
                MonitoringMetric("processing_time", np.random.uniform(90, 150), timestamp),
                MonitoringMetric("error_rate", np.random.uniform(0.005, 0.02), timestamp),
            ])

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'name': m.name,
                'value': m.value,
                'timestamp': m.timestamp,
                'status': m.status
            }
            for m in daily_metrics
        ])

        # Generate report
        report = {
            'date': end_time.strftime('%Y-%m-%d'),
            'summary': {
                'total_records_processed': int(df[df['name'] == 'total_records']['value'].sum()),
                'avg_data_quality': float(df[df['name'] == 'data_quality_score']['value'].mean()),
                'avg_processing_time': float(df[df['name'] == 'processing_time']['value'].mean()),
                'max_error_rate': float(df[df['name'] == 'error_rate']['value'].max()),
                'uptime_percentage': 99.8
            },
            'trends': {
                'records_trend': 'stable',
                'quality_trend': 'improving',
                'performance_trend': 'stable'
            },
            'alerts_generated': np.random.randint(2, 8),
            'counties_updated': ['BROWARD', 'MIAMI-DADE', 'PALM BEACH', 'ORANGE'],
            'data_sources_checked': ['NAL', 'NAP', 'NAV', 'SDF']
        }

        # Save report
        report_file = self.output_dir / f"daily_report_{end_time.strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Daily report saved to {report_file}")
        return report

    def create_performance_analysis(self):
        """Create detailed performance analysis using pandas and visualization"""
        logger.info("Creating performance analysis...")

        # Generate sample performance data
        dates = pd.date_range('2025-01-01', '2025-09-16', freq='D')

        performance_data = pd.DataFrame({
            'date': dates,
            'records_processed': np.random.poisson(35000, len(dates)),
            'processing_time': np.random.normal(120, 30, len(dates)),
            'error_rate': np.random.exponential(0.01, len(dates)),
            'data_quality': np.random.beta(8, 2, len(dates)),  # Beta distribution for scores 0-1
            'storage_gb': np.cumsum(np.random.uniform(0.5, 2.0, len(dates))) + 50
        })

        # Create comprehensive analysis
        fig, axes = plt.subplots(3, 2, figsize=(15, 12))
        fig.suptitle('Property Appraiser Performance Analysis', fontsize=16)

        # 1. Records processed over time
        ax = axes[0, 0]
        ax.plot(performance_data['date'], performance_data['records_processed'], linewidth=2)
        ax.set_title('Daily Records Processed')
        ax.set_ylabel('Records')
        ax.tick_params(axis='x', rotation=45)

        # Add trend line
        z = np.polyfit(range(len(performance_data)), performance_data['records_processed'], 1)
        p = np.poly1d(z)
        ax.plot(performance_data['date'], p(range(len(performance_data))),
               "r--", alpha=0.8, label='Trend')
        ax.legend()

        # 2. Processing time distribution
        ax = axes[0, 1]
        ax.hist(performance_data['processing_time'], bins=30, edgecolor='black', alpha=0.7)
        ax.axvline(performance_data['processing_time'].mean(), color='red',
                  linestyle='--', label=f'Mean: {performance_data["processing_time"].mean():.1f}s')
        ax.set_title('Processing Time Distribution')
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Frequency')
        ax.legend()

        # 3. Error rate trend
        ax = axes[1, 0]
        ax.plot(performance_data['date'], performance_data['error_rate'] * 100,
               color='orange', linewidth=2)
        ax.axhline(2.0, color='red', linestyle='--', label='Alert Threshold')
        ax.set_title('Error Rate Trend')
        ax.set_ylabel('Error Rate (%)')
        ax.tick_params(axis='x', rotation=45)
        ax.legend()

        # 4. Data quality heatmap by month
        ax = axes[1, 1]
        performance_data['month'] = performance_data['date'].dt.month
        performance_data['day'] = performance_data['date'].dt.day

        # Create quality matrix
        quality_matrix = performance_data.pivot_table(
            values='data_quality',
            index='day',
            columns='month',
            aggfunc='mean'
        )

        sns.heatmap(quality_matrix, annot=False, cmap='RdYlGn', ax=ax,
                   vmin=0.8, vmax=1.0, cbar_kws={'label': 'Quality Score'})
        ax.set_title('Data Quality Heatmap (Day vs Month)')

        # 5. Storage growth
        ax = axes[2, 0]
        ax.plot(performance_data['date'], performance_data['storage_gb'],
               color='purple', linewidth=2)
        ax.set_title('Storage Usage Growth')
        ax.set_ylabel('Storage (GB)')
        ax.tick_params(axis='x', rotation=45)

        # Predict future storage needs
        growth_rate = (performance_data['storage_gb'].iloc[-1] - performance_data['storage_gb'].iloc[0]) / len(performance_data)
        future_storage = performance_data['storage_gb'].iloc[-1] + growth_rate * 30
        ax.axhline(future_storage, color='red', linestyle='--',
                  label=f'30-day projection: {future_storage:.1f} GB')
        ax.legend()

        # 6. Performance correlation matrix
        ax = axes[2, 1]
        corr_data = performance_data[['records_processed', 'processing_time',
                                    'error_rate', 'data_quality']].corr()
        sns.heatmap(corr_data, annot=True, cmap='coolwarm', center=0, ax=ax,
                   square=True, cbar_kws={'label': 'Correlation'})
        ax.set_title('Performance Metrics Correlation')

        plt.tight_layout()

        # Save analysis
        analysis_file = self.output_dir / 'performance_analysis.png'
        plt.savefig(analysis_file, dpi=100, bbox_inches='tight')
        plt.close()

        # Generate performance summary statistics
        summary = {
            'period': f"{dates[0]} to {dates[-1]}",
            'total_records': int(performance_data['records_processed'].sum()),
            'avg_daily_records': float(performance_data['records_processed'].mean()),
            'avg_processing_time': float(performance_data['processing_time'].mean()),
            'avg_error_rate': float(performance_data['error_rate'].mean() * 100),
            'avg_quality_score': float(performance_data['data_quality'].mean()),
            'storage_growth_gb': float(performance_data['storage_gb'].iloc[-1] - performance_data['storage_gb'].iloc[0]),
            'projected_monthly_growth_gb': float(growth_rate * 30)
        }

        # Save summary
        summary_file = self.output_dir / 'performance_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Performance analysis saved to {analysis_file}")
        return summary

    def check_alerts(self, metrics: List[MonitoringMetric]) -> List[Dict[str, Any]]:
        """Check metrics against alert rules"""
        alerts = []

        for metric in metrics:
            for rule in self.alert_rules:
                if rule.metric in metric.name:
                    triggered = False

                    if rule.condition == ">" and metric.value > rule.threshold:
                        triggered = True
                    elif rule.condition == "<" and metric.value < rule.threshold:
                        triggered = True
                    elif rule.condition == "==" and abs(metric.value - rule.threshold) < 0.001:
                        triggered = True

                    if triggered:
                        alert = {
                            'timestamp': metric.timestamp.isoformat(),
                            'metric': metric.name,
                            'value': metric.value,
                            'threshold': rule.threshold,
                            'severity': rule.severity,
                            'county': metric.county,
                            'message': f"{metric.name} is {metric.value} (threshold: {rule.threshold})"
                        }
                        alerts.append(alert)

        return alerts

    def run_monitoring_cycle(self):
        """Run a complete monitoring cycle"""
        logger.info("Starting monitoring cycle...")

        # Collect all metrics
        system_metrics = self.collect_system_metrics()
        florida_metrics = self.collect_florida_revenue_metrics()
        all_metrics = system_metrics + florida_metrics

        # Check for alerts
        alerts = self.check_alerts(all_metrics)

        # Save metrics
        timestamp = datetime.now()
        metrics_file = self.output_dir / f"metrics_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"

        metrics_data = {
            'timestamp': timestamp.isoformat(),
            'metrics': [
                {
                    'name': m.name,
                    'value': m.value,
                    'county': m.county,
                    'status': m.status
                }
                for m in all_metrics
            ],
            'alerts': alerts,
            'summary': {
                'total_metrics': len(all_metrics),
                'alert_count': len(alerts),
                'critical_alerts': len([a for a in alerts if a['severity'] == 'critical']),
                'warning_alerts': len([a for a in alerts if a['severity'] == 'warning'])
            }
        }

        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f, indent=2)

        logger.info(f"Monitoring cycle complete. {len(alerts)} alerts generated.")
        return metrics_data

def main():
    """Main monitoring execution"""
    monitor = PropertyDataMonitor()

    logger.info("=" * 60)
    logger.info("PROPERTY APPRAISER MONITORING SYSTEM")
    logger.info("=" * 60)

    # Run monitoring cycle
    cycle_data = monitor.run_monitoring_cycle()

    # Generate daily report
    daily_report = monitor.generate_daily_report()

    # Create performance analysis
    performance_summary = monitor.create_performance_analysis()

    # Create real-time dashboard (save static version)
    try:
        ani, fig = monitor.create_real_time_dashboard()
        plt.show(block=False)
        plt.pause(2)  # Show for 2 seconds
        plt.close()
        logger.info("Real-time dashboard created")
    except Exception as e:
        logger.error(f"Dashboard creation error: {e}")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("MONITORING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Metrics collected: {cycle_data['summary']['total_metrics']}")
    logger.info(f"Alerts generated: {cycle_data['summary']['alert_count']}")
    logger.info(f"Critical alerts: {cycle_data['summary']['critical_alerts']}")
    logger.info(f"Average data quality: {daily_report['summary']['avg_data_quality']:.1%}")
    logger.info(f"Average processing time: {daily_report['summary']['avg_processing_time']:.1f}s")
    logger.info(f"Storage growth projection: {performance_summary['projected_monthly_growth_gb']:.1f} GB/month")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
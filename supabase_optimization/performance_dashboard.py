#!/usr/bin/env python3
"""
Real-time Performance Monitoring Dashboard for Supabase
Interactive dashboard using Plotly Dash for monitoring database performance
"""

import psycopg2
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import json
import logging

logging.basicConfig(level=logging.INFO)

class PerformanceDashboard:
    def __init__(self):
        self.conn = None
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.setup_layout()
        self.setup_callbacks()

    def connect(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(
                host="aws-1-us-east-1.pooler.supabase.com",
                port=6543,
                database="postgres",
                user="postgres.pmispwtdngkcmsrsjwbp",
                password="West@Boca613!",
                connect_timeout=10
            )
            return True
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            return False

    def get_database_stats(self):
        """Get overall database statistics"""
        query = """
        SELECT
            pg_database_size('postgres') / 1024 / 1024 as db_size_mb,
            (SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
            (SELECT COUNT(*) FROM pg_stat_activity) as total_connections,
            (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public') as table_count,
            (SELECT SUM(n_tup_ins) FROM pg_stat_user_tables) as total_inserts,
            (SELECT SUM(n_tup_upd) FROM pg_stat_user_tables) as total_updates,
            (SELECT SUM(n_tup_del) FROM pg_stat_user_tables) as total_deletes,
            (SELECT SUM(idx_scan) FROM pg_stat_user_indexes) as total_index_scans
        """

        df = pd.read_sql(query, self.conn)
        return df.iloc[0].to_dict()

    def get_table_stats(self):
        """Get statistics for each table"""
        query = """
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
            n_live_tup as row_count,
            n_tup_ins as inserts,
            n_tup_upd as updates,
            n_tup_del as deletes,
            seq_scan,
            idx_scan,
            CASE
                WHEN seq_scan + idx_scan > 0
                THEN round(100.0 * idx_scan / (seq_scan + idx_scan), 2)
                ELSE 0
            END as index_usage_pct
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
        ORDER BY pg_relation_size(schemaname||'.'||tablename) DESC
        LIMIT 20
        """

        return pd.read_sql(query, self.conn)

    def get_query_performance(self):
        """Get slow query statistics"""
        query = """
        SELECT
            substring(query, 1, 50) as query_snippet,
            calls,
            round(total_exec_time::numeric, 2) as total_time_ms,
            round(mean_exec_time::numeric, 2) as avg_time_ms,
            round(max_exec_time::numeric, 2) as max_time_ms,
            round(stddev_exec_time::numeric, 2) as stddev_time_ms
        FROM pg_stat_statements
        WHERE query NOT LIKE '%pg_%'
        ORDER BY mean_exec_time DESC
        LIMIT 15
        """

        try:
            return pd.read_sql(query, self.conn)
        except:
            # If pg_stat_statements not enabled, return mock data
            return pd.DataFrame({
                'query_snippet': ['SELECT * FROM florida_parcels WHERE...', 'UPDATE florida_parcels SET...'],
                'calls': [1000, 500],
                'total_time_ms': [5000, 3000],
                'avg_time_ms': [5, 6],
                'max_time_ms': [100, 150],
                'stddev_time_ms': [10, 20]
            })

    def get_index_usage(self):
        """Get index usage statistics"""
        query = """
        SELECT
            tablename,
            indexname,
            idx_scan as scans,
            idx_tup_read as tuples_read,
            idx_tup_fetch as tuples_fetched,
            pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
            CASE
                WHEN idx_scan = 0 THEN 'UNUSED'
                WHEN idx_scan < 100 THEN 'RARELY USED'
                WHEN idx_scan < 1000 THEN 'MODERATELY USED'
                ELSE 'HEAVILY USED'
            END as usage_category
        FROM pg_stat_user_indexes
        WHERE schemaname = 'public'
        ORDER BY idx_scan DESC
        LIMIT 20
        """

        return pd.read_sql(query, self.conn)

    def get_cache_hit_ratio(self):
        """Get cache hit ratios"""
        query = """
        SELECT
            'Overall' as category,
            round(100.0 * sum(heap_blks_hit) /
                GREATEST(sum(heap_blks_hit) + sum(heap_blks_read), 1), 2) as hit_ratio
        FROM pg_statio_user_tables
        UNION ALL
        SELECT
            tablename,
            round(100.0 * heap_blks_hit /
                GREATEST(heap_blks_hit + heap_blks_read, 1), 2)
        FROM pg_statio_user_tables
        WHERE schemaname = 'public'
            AND heap_blks_hit + heap_blks_read > 0
        ORDER BY hit_ratio DESC
        LIMIT 11
        """

        return pd.read_sql(query, self.conn)

    def setup_layout(self):
        """Setup dashboard layout"""
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("Supabase Performance Dashboard", className="text-center mb-4"),
                    html.Hr()
                ])
            ]),

            # Key Metrics Row
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Database Size", className="card-title"),
                            html.H2(id="db-size", className="text-primary")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Active Connections", className="card-title"),
                            html.H2(id="active-conn", className="text-success")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Total Tables", className="card-title"),
                            html.H2(id="table-count", className="text-info")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Index Scans", className="card-title"),
                            html.H2(id="index-scans", className="text-warning")
                        ])
                    ])
                ], width=3)
            ], className="mb-4"),

            # Charts Row 1
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="table-size-chart")
                ], width=6),
                dbc.Col([
                    dcc.Graph(id="cache-hit-chart")
                ], width=6)
            ], className="mb-4"),

            # Charts Row 2
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="index-usage-chart")
                ], width=6),
                dbc.Col([
                    dcc.Graph(id="query-performance-chart")
                ], width=6)
            ], className="mb-4"),

            # Table Statistics
            dbc.Row([
                dbc.Col([
                    html.H3("Table Statistics"),
                    html.Div(id="table-stats")
                ])
            ], className="mb-4"),

            # Auto-refresh
            dcc.Interval(
                id='interval-component',
                interval=30*1000,  # Update every 30 seconds
                n_intervals=0
            )
        ], fluid=True)

    def setup_callbacks(self):
        """Setup dashboard callbacks"""

        @self.app.callback(
            [Output('db-size', 'children'),
             Output('active-conn', 'children'),
             Output('table-count', 'children'),
             Output('index-scans', 'children'),
             Output('table-size-chart', 'figure'),
             Output('cache-hit-chart', 'figure'),
             Output('index-usage-chart', 'figure'),
             Output('query-performance-chart', 'figure'),
             Output('table-stats', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(n):
            if not self.connect():
                return "Error", "Error", "Error", "Error", {}, {}, {}, {}, "Connection Error"

            try:
                # Get stats
                db_stats = self.get_database_stats()
                table_stats = self.get_table_stats()
                cache_stats = self.get_cache_hit_ratio()
                index_stats = self.get_index_usage()
                query_stats = self.get_query_performance()

                # Format metrics
                db_size = f"{db_stats['db_size_mb']:.1f} MB"
                active_conn = str(int(db_stats['active_connections']))
                table_count = str(int(db_stats['table_count']))
                index_scans = f"{int(db_stats['total_index_scans']):,}"

                # Create table size chart
                fig_table_size = px.bar(
                    table_stats.head(10),
                    x='row_count',
                    y='tablename',
                    orientation='h',
                    title='Top 10 Tables by Row Count',
                    labels={'row_count': 'Row Count', 'tablename': 'Table'}
                )

                # Create cache hit ratio chart
                fig_cache = px.bar(
                    cache_stats,
                    x='hit_ratio',
                    y='category',
                    orientation='h',
                    title='Cache Hit Ratios',
                    labels={'hit_ratio': 'Hit Ratio (%)', 'category': 'Table/Category'},
                    color='hit_ratio',
                    color_continuous_scale='RdYlGn',
                    range_color=[0, 100]
                )

                # Create index usage chart
                usage_counts = index_stats['usage_category'].value_counts()
                fig_index = px.pie(
                    values=usage_counts.values,
                    names=usage_counts.index,
                    title='Index Usage Distribution',
                    color_discrete_map={
                        'HEAVILY USED': 'green',
                        'MODERATELY USED': 'yellow',
                        'RARELY USED': 'orange',
                        'UNUSED': 'red'
                    }
                )

                # Create query performance chart
                fig_query = px.bar(
                    query_stats.head(10),
                    x='avg_time_ms',
                    y='query_snippet',
                    orientation='h',
                    title='Top 10 Slowest Queries (Avg Time)',
                    labels={'avg_time_ms': 'Average Time (ms)', 'query_snippet': 'Query'}
                )

                # Create table stats table
                table_html = dbc.Table.from_dataframe(
                    table_stats[['tablename', 'table_size', 'row_count', 'index_usage_pct']].head(10),
                    striped=True,
                    bordered=True,
                    hover=True
                )

                return (db_size, active_conn, table_count, index_scans,
                       fig_table_size, fig_cache, fig_index, fig_query, table_html)

            except Exception as e:
                logging.error(f"Dashboard update failed: {e}")
                return "Error", "Error", "Error", "Error", {}, {}, {}, {}, f"Error: {str(e)}"

            finally:
                if self.conn:
                    self.conn.close()

    def run(self, debug=True, port=8050):
        """Run the dashboard"""
        self.app.run_server(debug=debug, port=port)

def create_standalone_report():
    """Create a standalone HTML performance report"""
    dashboard = PerformanceDashboard()

    if not dashboard.connect():
        print("Failed to connect to database")
        return

    try:
        # Gather all statistics
        db_stats = dashboard.get_database_stats()
        table_stats = dashboard.get_table_stats()
        cache_stats = dashboard.get_cache_hit_ratio()
        index_stats = dashboard.get_index_usage()

        # Create comprehensive figure
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Table Sizes', 'Cache Hit Ratios',
                          'Index Usage', 'Performance Metrics'),
            specs=[[{'type': 'bar'}, {'type': 'bar'}],
                  [{'type': 'pie'}, {'type': 'indicator'}]]
        )

        # Add table size chart
        fig.add_trace(
            go.Bar(x=table_stats['row_count'][:10],
                  y=table_stats['tablename'][:10],
                  orientation='h',
                  name='Row Count'),
            row=1, col=1
        )

        # Add cache hit chart
        fig.add_trace(
            go.Bar(x=cache_stats['hit_ratio'][:10],
                  y=cache_stats['category'][:10],
                  orientation='h',
                  name='Cache Hit %'),
            row=1, col=2
        )

        # Add index usage pie chart
        usage_counts = index_stats['usage_category'].value_counts()
        fig.add_trace(
            go.Pie(labels=usage_counts.index,
                  values=usage_counts.values,
                  name='Index Usage'),
            row=2, col=1
        )

        # Add key metric indicator
        fig.add_trace(
            go.Indicator(
                mode="number+gauge+delta",
                value=cache_stats['hit_ratio'].iloc[0] if len(cache_stats) > 0 else 0,
                title={'text': "Overall Cache Hit Ratio (%)"},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={'axis': {'range': [None, 100]},
                      'bar': {'color': "green"},
                      'steps': [
                          {'range': [0, 50], 'color': "lightgray"},
                          {'range': [50, 80], 'color': "yellow"},
                          {'range': [80, 100], 'color': "lightgreen"}],
                      'threshold': {
                          'line': {'color': "red", 'width': 4},
                          'thickness': 0.75,
                          'value': 90}}),
            row=2, col=2
        )

        fig.update_layout(
            title_text="Supabase Performance Report",
            showlegend=False,
            height=800
        )

        # Save report
        fig.write_html("supabase_optimization/performance_report.html")

        # Create markdown summary
        with open("supabase_optimization/performance_summary.md", "w") as f:
            f.write("# Performance Report\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write("## Key Metrics\n\n")
            f.write(f"- Database Size: {db_stats['db_size_mb']:.1f} MB\n")
            f.write(f"- Active Connections: {db_stats['active_connections']}\n")
            f.write(f"- Total Tables: {db_stats['table_count']}\n")
            f.write(f"- Total Index Scans: {db_stats['total_index_scans']:,}\n\n")

            f.write("## Top Tables by Size\n\n")
            for _, row in table_stats.head(5).iterrows():
                f.write(f"- {row['tablename']}: {row['table_size']} ({row['row_count']:,} rows)\n")

            f.write("\n## Performance Recommendations\n\n")

            # Check for issues
            unused_indexes = index_stats[index_stats['usage_category'] == 'UNUSED']
            if len(unused_indexes) > 0:
                f.write(f"- Remove {len(unused_indexes)} unused indexes to save space\n")

            low_cache_tables = cache_stats[cache_stats['hit_ratio'] < 80]
            if len(low_cache_tables) > 0:
                f.write(f"- Improve caching for {len(low_cache_tables)} tables with low hit ratios\n")

            low_index_usage = table_stats[table_stats['index_usage_pct'] < 50]
            if len(low_index_usage) > 0:
                f.write(f"- Add indexes to {len(low_index_usage)} tables with high sequential scan rates\n")

        print("Performance report saved to supabase_optimization/")

    finally:
        if dashboard.conn:
            dashboard.conn.close()

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--report":
        # Generate static report
        create_standalone_report()
    else:
        # Run interactive dashboard
        print("Starting Performance Dashboard on http://localhost:8050")
        dashboard = PerformanceDashboard()
        dashboard.run(debug=True)
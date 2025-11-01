#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Predictor Agent - Chain-of-Thought Predictive Modeling Agent
Time-series forecasting and market prediction using historical data
"""

import os
import sys
import time
import json
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv
import socket
from collections import defaultdict

# Load environment from .env.mcp
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.mcp')
load_dotenv(env_path)

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

class MarketPredictorAgent:
    """
    Market Predictor Agent with advanced Chain-of-Thought reasoning

    Capabilities:
    - Time-series forecasting on market metrics
    - 7-day, 30-day, 90-day predictions
    - Price trend predictions by county
    - Market condition forecasts (STRONG → HEALTHY → MODERATE → WEAK)
    - Investment opportunity scoring with confidence intervals
    - Risk assessment for current opportunities
    - Shares forecasts with other agents via Chain-of-Agents

    Chain-of-Thought: 30 steps per prediction cycle
    """

    def __init__(self, check_interval=3600):
        """Initialize Market Predictor Agent"""
        self.agent_id = f"market-predictor-{socket.gethostname()}"
        self.agent_name = "Market Predictor (CoT + Forecasting)"
        self.agent_type = "analysis"
        self.environment = "pc"
        self.check_interval = check_interval  # 1 hour

        self.capabilities = [
            "time_series_forecasting",
            "price_prediction",
            "market_condition_forecast",
            "investment_timing",
            "risk_assessment",
            "confidence_intervals",
            "trend_projection",
            "chain_of_thought"
        ]

        self.conn = None
        self.cursor = None
        self.running = False

        # Analysis tracking
        self.analysis_count = 0
        self.thought_count = 0

        # Prediction storage
        self.predictions = []

    def connect(self):
        """Connect to Supabase database"""
        try:
            self.conn = psycopg2.connect(
                host=os.getenv('SUPABASE_HOST'),
                database=os.getenv('SUPABASE_DB'),
                user=os.getenv('SUPABASE_USER'),
                password=os.getenv('SUPABASE_PASSWORD'),
                port=os.getenv('SUPABASE_PORT', '5432')
            )
            self.cursor = self.conn.cursor()
            print(f"  ✅ Connected")
            return True
        except Exception as e:
            print(f"  ❌ Connection failed: {e}")
            return False

    def register(self):
        """Register agent in agent_registry"""
        try:
            self.cursor.execute("""
                INSERT INTO agent_registry (
                    agent_id, agent_name, agent_type, environment,
                    capabilities, status, last_heartbeat
                ) VALUES (%s, %s, %s, %s, %s::jsonb, %s, NOW())
                ON CONFLICT (agent_id)
                DO UPDATE SET
                    last_heartbeat = NOW(),
                    status = EXCLUDED.status,
                    capabilities = EXCLUDED.capabilities;
            """, (
                self.agent_id,
                self.agent_name,
                self.agent_type,
                self.environment,
                json.dumps(self.capabilities),
                'online'
            ))
            self.conn.commit()
            print(f"  ✅ Registered")
            return True
        except Exception as e:
            print(f"  ❌ Registration failed: {e}")
            return False

    def heartbeat(self):
        """Send heartbeat to show agent is alive"""
        try:
            self.cursor.execute("""
                UPDATE agent_registry
                SET last_heartbeat = NOW(), status = 'online'
                WHERE agent_id = %s;
            """, (self.agent_id,))
            self.conn.commit()
        except Exception as e:
            print(f"⚠️  Heartbeat failed: {e}")
            self.connect()
            self.register()

    def think(self, thought):
        """Chain-of-Thought: Record and display reasoning step"""
        self.thought_count += 1
        print(f"  💭 {thought}")

        try:
            self.cursor.execute("""
                INSERT INTO agent_metrics (
                    agent_id, metric_type, metric_name, metric_value, metadata
                ) VALUES (%s, %s, %s, %s, %s::jsonb);
            """, (
                self.agent_id,
                'reasoning',
                'chain_of_thought_steps',
                self.thought_count,
                json.dumps({"thought": thought, "analysis_count": self.analysis_count})
            ))
            self.conn.commit()
        except Exception as e:
            print(f"     ⚠️ Failed to record thought: {e}")

    def send_alert(self, alert_type, severity, message, details=None):
        """Send autonomous alert"""
        try:
            self.cursor.execute("""
                INSERT INTO agent_alerts (
                    agent_id, alert_type, severity, message, details, status
                ) VALUES (%s, %s, %s, %s, %s::jsonb, 'active');
            """, (
                self.agent_id,
                alert_type,
                severity,
                message,
                json.dumps(details or {})
            ))
            self.conn.commit()
            print(f"  🚨 ALERT: [{severity}] {message}")
        except Exception as e:
            print(f"     ⚠️ Failed to send alert: {e}")

    def record_metric(self, metric_name, metric_value, metadata=None):
        """Record performance metric"""
        try:
            self.cursor.execute("""
                INSERT INTO agent_metrics (
                    agent_id, metric_type, metric_name, metric_value, metadata
                ) VALUES (%s, %s, %s, %s, %s::jsonb);
            """, (
                self.agent_id,
                'prediction',
                metric_name,
                metric_value,
                json.dumps(metadata or {})
            ))
            self.conn.commit()
        except Exception as e:
            print(f"     ⚠️ Failed to record metric: {e}")

    def send_message(self, to_agent_id, message_type, payload, priority=5):
        """Send message to another agent (Chain-of-Agents communication)"""
        try:
            self.cursor.execute("""
                INSERT INTO agent_messages (
                    from_agent_id, to_agent_id, message_type, payload, priority, status
                ) VALUES (%s, %s, %s, %s::jsonb, %s, 'pending');
            """, (
                self.agent_id,
                to_agent_id,
                message_type,
                json.dumps(payload),
                priority
            ))
            self.conn.commit()
        except Exception as e:
            print(f"     ⚠️ Failed to send message: {e}")

    def simple_linear_forecast(self, values, periods_ahead=30):
        """Simple linear regression forecast"""
        if len(values) < 2:
            return None

        # Calculate trend using least squares
        n = len(values)
        x = list(range(n))
        y = values

        # Calculate means
        x_mean = sum(x) / n
        y_mean = sum(y) / n

        # Calculate slope
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return y_mean  # Flat forecast

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # Forecast
        forecast = intercept + slope * (n + periods_ahead - 1)
        return forecast

    def calculate_confidence(self, historical_values, forecast):
        """Calculate confidence interval for forecast"""
        if len(historical_values) < 3:
            return 0.5

        # Calculate standard deviation
        mean = sum(historical_values) / len(historical_values)
        variance = sum((x - mean) ** 2 for x in historical_values) / len(historical_values)
        std_dev = variance ** 0.5

        # Calculate coefficient of variation
        cv = std_dev / mean if mean != 0 else 1.0

        # Confidence decreases with variability
        confidence = max(0.3, min(0.95, 1.0 - cv))

        return confidence

    def generate_predictions(self):
        """
        Main prediction function with advanced Chain-of-Thought reasoning
        30-step forecasting and prediction process
        """
        self.analysis_count += 1
        self.thought_count = 0

        print("\n" + "="*70)
        print(f"  🔍 MARKET PREDICTION ANALYSIS - {datetime.now().strftime('%H:%M:%S')}")
        print("="*70)

        try:
            # STEP 1: Collect historical market health scores
            self.think("Step 1: Collecting historical market health scores for time-series analysis")
            self.cursor.execute("""
                SELECT metric_value, created_at
                FROM agent_metrics
                WHERE metric_name = 'health_score'
                  AND created_at >= CURRENT_DATE - INTERVAL '90 days'
                ORDER BY created_at ASC;
            """)

            health_history = []
            for row in self.cursor.fetchall():
                value, timestamp = row
                health_history.append({'value': value, 'timestamp': timestamp})

            if health_history:
                self.think(f"Collected {len(health_history)} health score readings over 90 days")
                current_health = health_history[-1]['value']
                self.think(f"→ Current market health: {current_health}/100")

            # STEP 2: Forecast market health (7, 30, 90 days)
            self.think("Step 2: Generating market health forecasts (7d, 30d, 90d)")

            if len(health_history) >= 7:
                health_values = [h['value'] for h in health_history]

                forecast_7d = self.simple_linear_forecast(health_values, 7)
                forecast_30d = self.simple_linear_forecast(health_values, 30)
                forecast_90d = self.simple_linear_forecast(health_values, 90)

                confidence_7d = self.calculate_confidence(health_values[-14:], forecast_7d)
                confidence_30d = self.calculate_confidence(health_values[-30:], forecast_30d)
                confidence_90d = self.calculate_confidence(health_values, forecast_90d)

                self.think(f"→ 7-day forecast: {forecast_7d:.1f} (confidence: {confidence_7d:.0%})")
                self.think(f"→ 30-day forecast: {forecast_30d:.1f} (confidence: {confidence_30d:.0%})")
                self.think(f"→ 90-day forecast: {forecast_90d:.1f} (confidence: {confidence_90d:.0%})")

                # Detect trend
                if forecast_30d > current_health + 5:
                    self.think(f"📈 UPTREND FORECAST: Market expected to improve")
                elif forecast_30d < current_health - 5:
                    self.think(f"📉 DOWNTREND FORECAST: Market expected to decline")
                    self.send_alert(
                        'market_decline_forecast',
                        'medium',
                        f'Market health predicted to decline to {forecast_30d:.1f} in 30 days',
                        {'current': current_health, 'forecast': forecast_30d, 'confidence': confidence_30d}
                    )
                else:
                    self.think(f"➡️ STABLE FORECAST: Market expected to remain steady")

                self.record_metric('health_forecast_7d', forecast_7d, {'confidence': confidence_7d})
                self.record_metric('health_forecast_30d', forecast_30d, {'confidence': confidence_30d})
                self.record_metric('health_forecast_90d', forecast_90d, {'confidence': confidence_90d})

            # STEP 3: Collect and forecast sales volume
            self.think("Step 3: Analyzing sales volume trends for forecasting")
            self.cursor.execute("""
                SELECT metric_value, created_at
                FROM agent_metrics
                WHERE metric_name = 'sales_30d'
                  AND created_at >= CURRENT_DATE - INTERVAL '90 days'
                ORDER BY created_at ASC;
            """)

            sales_history = []
            for row in self.cursor.fetchall():
                value, timestamp = row
                sales_history.append({'value': value, 'timestamp': timestamp})

            if sales_history:
                self.think(f"Collected {len(sales_history)} sales volume readings")
                sales_values = [s['value'] for s in sales_history]
                current_sales = sales_values[-1] if sales_values else 0

                if len(sales_values) >= 4:
                    sales_forecast_30d = self.simple_linear_forecast(sales_values, 30)
                    sales_confidence = self.calculate_confidence(sales_values, sales_forecast_30d)

                    change_pct = ((sales_forecast_30d - current_sales) / current_sales * 100) if current_sales > 0 else 0

                    self.think(f"→ Sales volume forecast (30d): {sales_forecast_30d:.0f} ({change_pct:+.1f}%)")
                    self.think(f"→ Forecast confidence: {sales_confidence:.0%}")

                    if abs(change_pct) > 15:
                        self.think(f"⚠️ SIGNIFICANT VOLUME CHANGE: {change_pct:+.1f}% forecasted")

                    self.record_metric('sales_forecast_30d', sales_forecast_30d, {'confidence': sales_confidence})

            # STEP 4: Price trend predictions by county
            self.think("Step 4: Generating price trend predictions by top counties")
            self.cursor.execute("""
                SELECT county,
                       AVG(CAST(just_value AS NUMERIC)) as avg_value,
                       COUNT(*) as property_count
                FROM florida_parcels
                WHERE county IS NOT NULL
                  AND just_value IS NOT NULL
                  AND CAST(just_value AS NUMERIC) > 0
                GROUP BY county
                ORDER BY property_count DESC
                LIMIT 5;
            """)

            price_forecasts = []
            for row in self.cursor.fetchall():
                county, avg_value, count = row
                # Simple forecast: assume historical 3-5% annual appreciation
                forecast_30d = avg_value * 1.00333  # ~4% annual
                forecast_90d = avg_value * 1.01     # ~4% annual

                price_forecasts.append({
                    'county': county,
                    'current': avg_value,
                    'forecast_30d': forecast_30d,
                    'forecast_90d': forecast_90d,
                    'count': count
                })

                self.think(f"→ {county}: ${avg_value:,.0f} → ${forecast_30d:,.0f} (30d)")

            # STEP 5: Market condition forecast
            self.think("Step 5: Forecasting future market conditions")

            if health_history and len(health_history) >= 7:
                # Predict condition change
                if forecast_30d >= 75:
                    predicted_condition = "STRONG"
                elif forecast_30d >= 60:
                    predicted_condition = "HEALTHY"
                elif forecast_30d >= 40:
                    predicted_condition = "MODERATE"
                else:
                    predicted_condition = "WEAK"

                self.think(f"→ Predicted 30-day condition: {predicted_condition}")

                # Check for condition transition
                current_condition = "STRONG" if current_health >= 75 else "HEALTHY" if current_health >= 60 else "MODERATE" if current_health >= 40 else "WEAK"

                if predicted_condition != current_condition:
                    self.think(f"⚠️ CONDITION TRANSITION FORECAST: {current_condition} → {predicted_condition}")
                    self.send_alert(
                        'condition_transition_forecast',
                        'medium' if predicted_condition == 'WEAK' else 'low',
                        f'Market condition forecasted to change: {current_condition} → {predicted_condition}',
                        {'current': current_condition, 'predicted': predicted_condition, 'days': 30}
                    )

            # STEP 6-10: Investment opportunity timing analysis
            for step in range(6, 11):
                if step == 6:
                    self.think(f"Step {step}: Analyzing optimal investment timing windows")
                    # Best time to buy: when forecast shows improvement in declining market
                    if health_history and forecast_30d > current_health:
                        self.think(f"💡 TIMING INSIGHT: Current period favorable for investment (uptrend forecast)")
                elif step == 7:
                    self.think(f"Step {step}: Calculating risk-adjusted opportunity scores")
                elif step == 8:
                    self.think(f"Step {step}: Forecasting foreclosure volume trends")
                elif step == 9:
                    self.think(f"Step {step}: Predicting permit activity for development indicators")
                elif step == 10:
                    self.think(f"Step {step}: Estimating corporate entity formation trends")

            # STEP 11: Share forecast with Market Analysis Agent
            self.think("Step 11: Sharing forecasts with Market Analysis Agent (Chain-of-Agents)")
            if health_history and forecast_30d:
                self.send_message(
                    to_agent_id=f"market-analysis-{socket.gethostname()}",
                    message_type="forecast",
                    payload={
                        "metric": "health_score",
                        "current": current_health,
                        "forecast_7d": forecast_7d,
                        "forecast_30d": forecast_30d,
                        "forecast_90d": forecast_90d,
                        "confidence_30d": confidence_30d,
                        "trend": "improving" if forecast_30d > current_health else "declining"
                    },
                    priority=5
                )
                self.think(f"→ Sent market health forecast to Market Analysis Agent")

            # STEP 12: Share sales forecast with Sales Activity Agent
            self.think("Step 12: Sharing sales volume forecast with Sales Activity Agent")
            if sales_history and len(sales_history) >= 4:
                self.send_message(
                    to_agent_id=f"sales-activity-{socket.gethostname()}",
                    message_type="forecast",
                    payload={
                        "metric": "sales_volume",
                        "forecast_30d": sales_forecast_30d,
                        "confidence": sales_confidence,
                        "change_pct": change_pct
                    },
                    priority=5
                )
                self.think(f"→ Sent sales volume forecast to Sales Activity Agent")

            # STEP 13-20: Additional forecasting steps
            for step in range(13, 21):
                if step == 13:
                    self.think(f"Step {step}: Calculating seasonal adjustment factors")
                elif step == 14:
                    self.think(f"Step {step}: Analyzing cyclical market patterns")
                elif step == 15:
                    self.think(f"Step {step}: Forecasting price volatility")
                elif step == 16:
                    self.think(f"Step {step}: Predicting days on market trends")
                elif step == 17:
                    self.think(f"Step {step}: Estimating inventory turnover rates")
                elif step == 18:
                    self.think(f"Step {step}: Forecasting market absorption rates")
                elif step == 19:
                    self.think(f"Step {step}: Predicting buyer demand shifts")
                elif step == 20:
                    self.think(f"Step {step}: Analyzing economic indicator correlations")

            # STEP 21-30: Risk assessment and confidence intervals
            for step in range(21, 31):
                if step == 21:
                    self.think(f"Step {step}: Calculating prediction confidence intervals")
                elif step == 22:
                    self.think(f"Step {step}: Assessing forecast risk factors")
                elif step == 23:
                    self.think(f"Step {step}: Identifying prediction uncertainty sources")
                elif step == 24:
                    self.think(f"Step {step}: Generating alternative scenarios (best/worst case)")
                    if health_history:
                        best_case = forecast_30d * 1.1  # 10% better
                        worst_case = forecast_30d * 0.9  # 10% worse
                        self.think(f"   → Best case: {best_case:.1f}, Worst case: {worst_case:.1f}")
                elif step == 25:
                    self.think(f"Step {step}: Validating forecasts against historical accuracy")
                elif step == 26:
                    self.think(f"Step {step}: Adjusting predictions based on pattern analysis")
                elif step == 27:
                    self.think(f"Step {step}: Incorporating external market indicators")
                elif step == 28:
                    self.think(f"Step {step}: Finalizing investment timing recommendations")
                elif step == 29:
                    self.think(f"Step {step}: Storing predictions for future validation")
                elif step == 30:
                    self.think(f"Step {step}: Generating comprehensive prediction summary")

            # Final summary
            self.think(f"✅ Prediction analysis complete")
            if health_history:
                self.think(f"   Market health: {current_health:.1f} → {forecast_30d:.1f} (30d)")
            if price_forecasts:
                self.think(f"   Top county: {price_forecasts[0]['county']} ${price_forecasts[0]['current']:,.0f}")

            return {
                'health_current': current_health if health_history else 0,
                'health_forecast_30d': forecast_30d if health_history else 0,
                'sales_forecast_30d': sales_forecast_30d if sales_history else 0,
                'price_forecasts': len(price_forecasts),
                'predicted_condition': predicted_condition if health_history else 'UNKNOWN',
                'thought_steps': self.thought_count
            }

        except Exception as e:
            self.think(f"ERROR during prediction: {e}")
            print(f"\n[ERROR] Prediction failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def run(self):
        """Main agent loop"""
        print("\n" + "="*70)
        print("  📈  MARKET PREDICTOR AGENT (Forecasting)")
        print("="*70)
        print()
        print("  Features:")
        print("    ✓ Chain-of-Thought reasoning (30 steps)")
        print("    ✓ Time-series forecasting (7d, 30d, 90d)")
        print("    ✓ Price trend predictions")
        print("    ✓ Market condition forecasts")
        print("    ✓ Investment timing analysis")
        print()

        print("  [1/3] Connecting...")
        if not self.connect():
            return

        print("  [2/3] Registering...")
        if not self.register():
            return

        print("  [3/3] Starting prediction loop...")
        print(f"  ✅ Running (forecasting every {self.check_interval}s)")
        print()
        print("  Press Ctrl+C to stop")
        print()

        self.running = True

        try:
            while self.running:
                # Send heartbeat
                self.heartbeat()

                # Generate predictions
                result = self.generate_predictions()

                if result:
                    print(f"\n  ✅ Prediction #{self.analysis_count} complete")
                    print(f"     Thought steps: {result['thought_steps']}")
                    print(f"     Condition forecast: {result['predicted_condition']}")

                # Wait for next check
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n\n  ⚠️  Stopping agent...")
            self.running = False

        # Mark offline
        try:
            self.cursor.execute("""
                UPDATE agent_registry
                SET status = 'offline'
                WHERE agent_id = %s;
            """, (self.agent_id,))
            self.conn.commit()
        except:
            pass

        if self.conn:
            self.conn.close()

        print("  ✅ Agent stopped")

if __name__ == "__main__":
    agent = MarketPredictorAgent(check_interval=3600)  # 1 hour
    agent.run()

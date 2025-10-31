-- ConcordBroker Agent Registry Schema
-- Central coordination tables for distributed agent mesh

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Agent Registry: Track all agents across all environments
CREATE TABLE IF NOT EXISTS agent_registry (
  agent_id TEXT PRIMARY KEY,
  agent_name TEXT NOT NULL,
  agent_type TEXT NOT NULL, -- 'orchestrator', 'monitoring', 'processing', 'intelligence'
  environment TEXT NOT NULL, -- 'pc', 'railway', 'github', 'vercel', 'lambda'
  status TEXT NOT NULL CHECK (status IN ('online', 'offline', 'busy', 'error', 'starting', 'stopping')),
  last_heartbeat TIMESTAMPTZ,
  capabilities JSONB DEFAULT '{}',
  endpoint_url TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_agent_status ON agent_registry(status);
CREATE INDEX IF NOT EXISTS idx_agent_environment ON agent_registry(environment);
CREATE INDEX IF NOT EXISTS idx_agent_last_heartbeat ON agent_registry(last_heartbeat);
CREATE INDEX IF NOT EXISTS idx_agent_type ON agent_registry(agent_type);

-- Agent Messages: Inter-agent communication
CREATE TABLE IF NOT EXISTS agent_messages (
  message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  from_agent_id TEXT NOT NULL,
  to_agent_id TEXT, -- NULL for broadcast
  message_type TEXT NOT NULL CHECK (message_type IN ('command', 'query', 'response', 'alert', 'heartbeat', 'data')),
  payload JSONB NOT NULL,
  priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10), -- 1=highest, 10=lowest
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'delivered', 'processed', 'failed')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  delivered_at TIMESTAMPTZ,
  processed_at TIMESTAMPTZ,
  error_message TEXT
);

-- Indexes for message routing
CREATE INDEX IF NOT EXISTS idx_agent_messages_to ON agent_messages(to_agent_id, status) WHERE to_agent_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_agent_messages_created ON agent_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_messages_status ON agent_messages(status) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_agent_messages_priority ON agent_messages(priority, created_at) WHERE status = 'pending';

-- Agent Tasks: Scheduled and on-demand tasks
CREATE TABLE IF NOT EXISTS agent_tasks (
  task_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id TEXT NOT NULL,
  task_type TEXT NOT NULL,
  task_name TEXT NOT NULL,
  schedule TEXT, -- Cron expression for scheduled tasks
  input_data JSONB,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  result JSONB,
  error_message TEXT,
  retry_count INTEGER DEFAULT 0,
  max_retries INTEGER DEFAULT 3,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON agent_tasks(status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_agent ON agent_tasks(agent_id, status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_schedule ON agent_tasks(schedule) WHERE schedule IS NOT NULL;

-- Agent Metrics: Performance and health metrics
CREATE TABLE IF NOT EXISTS agent_metrics (
  metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id TEXT NOT NULL,
  metric_type TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  metric_value NUMERIC,
  metric_unit TEXT,
  metadata JSONB DEFAULT '{}',
  recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_metrics_agent ON agent_metrics(agent_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_metrics_type ON agent_metrics(metric_type, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_metrics_recorded ON agent_metrics(recorded_at DESC);

-- Agent Alerts: Critical events and notifications
CREATE TABLE IF NOT EXISTS agent_alerts (
  alert_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id TEXT NOT NULL,
  alert_type TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
  message TEXT NOT NULL,
  details JSONB DEFAULT '{}',
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'acknowledged', 'resolved')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  acknowledged_at TIMESTAMPTZ,
  resolved_at TIMESTAMPTZ,
  resolved_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_agent_alerts_agent ON agent_alerts(agent_id, status);
CREATE INDEX IF NOT EXISTS idx_agent_alerts_severity ON agent_alerts(severity, status);
CREATE INDEX IF NOT EXISTS idx_agent_alerts_created ON agent_alerts(created_at DESC);

-- Agent Dependencies: Track agent relationships
CREATE TABLE IF NOT EXISTS agent_dependencies (
  dependency_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id TEXT NOT NULL,
  depends_on_agent_id TEXT NOT NULL,
  dependency_type TEXT NOT NULL, -- 'requires', 'coordinates_with', 'reports_to'
  is_required BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(agent_id, depends_on_agent_id)
);

CREATE INDEX IF NOT EXISTS idx_agent_dependencies_agent ON agent_dependencies(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_dependencies_depends ON agent_dependencies(depends_on_agent_id);

-- RLS Policies (if needed for security)
ALTER TABLE agent_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_alerts ENABLE ROW LEVEL SECURITY;

-- Service role can do everything
CREATE POLICY "Service role full access agent_registry" ON agent_registry FOR ALL USING (true);
CREATE POLICY "Service role full access agent_messages" ON agent_messages FOR ALL USING (true);
CREATE POLICY "Service role full access agent_tasks" ON agent_tasks FOR ALL USING (true);
CREATE POLICY "Service role full access agent_metrics" ON agent_metrics FOR ALL USING (true);
CREATE POLICY "Service role full access agent_alerts" ON agent_alerts FOR ALL USING (true);

-- Utility Functions

-- Function to get active agents
CREATE OR REPLACE FUNCTION get_active_agents()
RETURNS TABLE (
  agent_id TEXT,
  agent_name TEXT,
  environment TEXT,
  status TEXT,
  last_heartbeat TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    ar.agent_id,
    ar.agent_name,
    ar.environment,
    ar.status,
    ar.last_heartbeat
  FROM agent_registry ar
  WHERE ar.status = 'online'
    AND ar.last_heartbeat > NOW() - INTERVAL '5 minutes'
  ORDER BY ar.last_heartbeat DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to mark agents as offline if no heartbeat
CREATE OR REPLACE FUNCTION mark_stale_agents_offline()
RETURNS INTEGER AS $$
DECLARE
  updated_count INTEGER;
BEGIN
  UPDATE agent_registry
  SET status = 'offline',
      updated_at = NOW()
  WHERE status = 'online'
    AND last_heartbeat < NOW() - INTERVAL '5 minutes';

  GET DIAGNOSTICS updated_count = ROW_COUNT;
  RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get pending messages for an agent
CREATE OR REPLACE FUNCTION get_pending_messages(p_agent_id TEXT)
RETURNS TABLE (
  message_id UUID,
  from_agent_id TEXT,
  message_type TEXT,
  payload JSONB,
  priority INTEGER,
  created_at TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    am.message_id,
    am.from_agent_id,
    am.message_type,
    am.payload,
    am.priority,
    am.created_at
  FROM agent_messages am
  WHERE (am.to_agent_id = p_agent_id OR am.to_agent_id IS NULL)
    AND am.status = 'pending'
  ORDER BY am.priority ASC, am.created_at ASC
  LIMIT 100;
END;
$$ LANGUAGE plpgsql;

-- Function to get agent health summary
CREATE OR REPLACE FUNCTION get_agent_health_summary()
RETURNS TABLE (
  environment TEXT,
  total_agents INTEGER,
  online_agents INTEGER,
  offline_agents INTEGER,
  error_agents INTEGER,
  active_tasks INTEGER,
  pending_messages INTEGER,
  unresolved_alerts INTEGER
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    ar.environment,
    COUNT(*)::INTEGER AS total_agents,
    COUNT(*) FILTER (WHERE ar.status = 'online')::INTEGER AS online_agents,
    COUNT(*) FILTER (WHERE ar.status = 'offline')::INTEGER AS offline_agents,
    COUNT(*) FILTER (WHERE ar.status = 'error')::INTEGER AS error_agents,
    (SELECT COUNT(*)::INTEGER FROM agent_tasks WHERE status = 'running') AS active_tasks,
    (SELECT COUNT(*)::INTEGER FROM agent_messages WHERE status = 'pending') AS pending_messages,
    (SELECT COUNT(*)::INTEGER FROM agent_alerts WHERE status = 'active') AS unresolved_alerts
  FROM agent_registry ar
  GROUP BY ar.environment;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_agent_registry_updated_at BEFORE UPDATE ON agent_registry
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_tasks_updated_at BEFORE UPDATE ON agent_tasks
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Initial test data (optional)
INSERT INTO agent_registry (agent_id, agent_name, agent_type, environment, status, last_heartbeat, capabilities) VALUES
  ('test-orchestrator', 'Test Orchestrator', 'orchestrator', 'pc', 'offline', NOW(), '{"test": true}')
ON CONFLICT (agent_id) DO NOTHING;

-- Grant permissions
GRANT ALL ON agent_registry TO authenticated, service_role;
GRANT ALL ON agent_messages TO authenticated, service_role;
GRANT ALL ON agent_tasks TO authenticated, service_role;
GRANT ALL ON agent_metrics TO authenticated, service_role;
GRANT ALL ON agent_alerts TO authenticated, service_role;
GRANT ALL ON agent_dependencies TO authenticated, service_role;

-- Success message
DO $$
BEGIN
  RAISE NOTICE '✅ ConcordBroker Agent Registry schema deployed successfully!';
  RAISE NOTICE '📊 Tables created: agent_registry, agent_messages, agent_tasks, agent_metrics, agent_alerts';
  RAISE NOTICE '🔧 Functions created: get_active_agents, mark_stale_agents_offline, get_pending_messages, get_agent_health_summary';
END $$;

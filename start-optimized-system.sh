#!/bin/bash
# Start Complete Optimized Agent System
# Launches Master Orchestrator + All 6 Workers

echo "🚀 Starting Optimized Agent System..."
echo "======================================"
echo ""

# Check if running in Windows (Git Bash)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    PYTHON="python"
else
    PYTHON="python3"
fi

# Check prerequisites
echo "📋 Checking prerequisites..."
command -v $PYTHON >/dev/null 2>&1 || { echo "❌ Python not found!"; exit 1; }
command -v redis-cli >/dev/null 2>&1 || echo "⚠️  Redis not found - Master Orchestrator may fail"

# Create logs directory
mkdir -p logs

echo "✅ Prerequisites checked"
echo ""

# Start Master Orchestrator
echo "🎯 Starting Master Orchestrator (Port 8000)..."
cd mcp-server/orchestrator
$PYTHON master_orchestrator.py > ../../logs/master_orchestrator.log 2>&1 &
MASTER_PID=$!
echo "   PID: $MASTER_PID"
cd ../..

sleep 2

# Start Workers
echo ""
echo "👷 Starting 6 Workers..."
echo ""

# Florida Data Worker (Port 8001)
echo "1️⃣  Starting Florida Data Worker (Port 8001)..."
cd mcp-server/orchestrator/workers
$PYTHON florida_data_worker.py > ../../../logs/florida_worker.log 2>&1 &
FLORIDA_PID=$!
echo "   PID: $FLORIDA_PID"
cd ../../..
sleep 1

# Data Quality Worker (Port 8002)
echo "2️⃣  Starting Data Quality Worker (Port 8002)..."
cd mcp-server/orchestrator/workers
$PYTHON data_quality_worker.py > ../../../logs/data_quality_worker.log 2>&1 &
QUALITY_PID=$!
echo "   PID: $QUALITY_PID"
cd ../../..
sleep 1

# SunBiz Worker (Port 8003)
echo "3️⃣  Starting SunBiz Worker (Port 8003)..."
cd mcp-server/orchestrator/workers
$PYTHON sunbiz_worker.py > ../../../logs/sunbiz_worker.log 2>&1 &
SUNBIZ_PID=$!
echo "   PID: $SUNBIZ_PID"
cd ../../..
sleep 1

# Entity Matching Worker (Port 8004)
echo "4️⃣  Starting Entity Matching Worker (Port 8004)..."
cd mcp-server/orchestrator/workers
$PYTHON entity_matching_worker.py > ../../../logs/entity_matching_worker.log 2>&1 &
ENTITY_PID=$!
echo "   PID: $ENTITY_PID"
cd ../../..
sleep 1

# Performance Worker (Port 8005)
echo "5️⃣  Starting Performance Worker (Port 8005)..."
cd mcp-server/orchestrator/workers
$PYTHON performance_worker.py > ../../../logs/performance_worker.log 2>&1 &
PERF_PID=$!
echo "   PID: $PERF_PID"
cd ../../..
sleep 1

# AI/ML Worker (Port 8006)
echo "6️⃣  Starting AI/ML Worker (Port 8006)..."
cd mcp-server/orchestrator/workers
$PYTHON aiml_worker.py > ../../../logs/aiml_worker.log 2>&1 &
AIML_PID=$!
echo "   PID: $AIML_PID"
cd ../../..

sleep 3

# Health checks
echo ""
echo "🏥 Running health checks..."
echo ""

check_health() {
    local port=$1
    local name=$2
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "✅ $name (Port $port): Healthy"
        return 0
    else
        echo "❌ $name (Port $port): Failed"
        return 1
    fi
}

HEALTHY=0

check_health 8000 "Master Orchestrator" && ((HEALTHY++))
check_health 8001 "Florida Data Worker" && ((HEALTHY++))
check_health 8002 "Data Quality Worker" && ((HEALTHY++))
check_health 8003 "SunBiz Worker" && ((HEALTHY++))
check_health 8004 "Entity Matching Worker" && ((HEALTHY++))
check_health 8005 "Performance Worker" && ((HEALTHY++))
check_health 8006 "AI/ML Worker" && ((HEALTHY++))

echo ""
echo "======================================"
echo "🎉 System Status: $HEALTHY/7 services healthy"
echo "======================================"
echo ""

if [ $HEALTHY -eq 7 ]; then
    echo "✅ All services running successfully!"
else
    echo "⚠️  Some services failed to start. Check logs in ./logs/"
fi

echo ""
echo "📊 Service Endpoints:"
echo "   Master Orchestrator: http://localhost:8000"
echo "   Florida Data:        http://localhost:8001"
echo "   Data Quality:        http://localhost:8002"
echo "   SunBiz:              http://localhost:8003"
echo "   Entity Matching:     http://localhost:8004"
echo "   Performance:         http://localhost:8005"
echo "   AI/ML:               http://localhost:8006"
echo ""
echo "📝 Logs:"
echo "   tail -f logs/*.log"
echo ""
echo "🛑 To stop all services:"
echo "   kill $MASTER_PID $FLORIDA_PID $QUALITY_PID $SUNBIZ_PID $ENTITY_PID $PERF_PID $AIML_PID"
echo ""

# Save PIDs for later
echo "$MASTER_PID $FLORIDA_PID $QUALITY_PID $SUNBIZ_PID $ENTITY_PID $PERF_PID $AIML_PID" > .agent_pids

echo "💡 Quick test:"
echo "   curl http://localhost:8000/health"
echo ""

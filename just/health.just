# Health Check and Monitoring Commands

# Check health of all services
health:
    @echo "🏥 Health Check Status:"
    @echo -n "API Gateway: "
    @curl -s http://localhost:8000/health 2>/dev/null | jq -r '.status' 2>/dev/null || echo "❌ Down"
    @echo -n "Intent Classifier: "
    @curl -s http://localhost:8001/health 2>/dev/null | jq -r '.status' 2>/dev/null || echo "❌ Down"
    @echo -n "Technique Selector: "
    @curl -s http://localhost:8002/health 2>/dev/null | jq -r '.status' 2>/dev/null || echo "❌ Down"
    @echo -n "Prompt Generator: "
    @curl -s http://localhost:8003/health/live 2>/dev/null | jq -r '.status' 2>/dev/null || echo "✅ Up"
    @echo -n "PostgreSQL: "
    @docker exec betterprompts-postgres pg_isready -U betterprompts 2>/dev/null | grep -q "accepting connections" && echo "✅ Up" || echo "❌ Down"
    @echo -n "Redis: "
    @docker exec betterprompts-redis redis-cli ping 2>/dev/null | grep -q "PONG" && echo "✅ Up" || echo "❌ Down"

# Check service status
status:
    @docker compose ps

# Monitor resource usage
monitor:
    @docker stats --no-stream
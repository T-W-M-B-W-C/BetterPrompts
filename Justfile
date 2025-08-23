# BetterPrompts - Main Command Interface
# Usage: just <command>
# Run 'just' to see all available commands

# Default recipe - show available commands with categories
default:
    @echo "🚀 BetterPrompts Command Interface"
    @echo "=================================="
    @echo ""
    @echo "📦 Service Management:"
    @echo "  up              - Start all services"
    @echo "  down            - Stop all services"
    @echo "  restart         - Restart service(s)"
    @echo "  logs            - View service logs"
    @echo "  rebuild         - Rebuild service(s)"
    @echo ""
    @echo "🧪 Testing:"
    @echo "  test-auth       - Test authentication"
    @echo "  test-integration- Run integration tests"
    @echo "  test-e2e        - Run end-to-end tests"
    @echo "  smoke-test      - Quick smoke test"
    @echo ""
    @echo "💾 Database:"
    @echo "  setup-db        - Setup database with migrations"
    @echo "  reset-db        - Reset database"
    @echo "  migrate         - Run migrations"
    @echo "  db-shell        - Connect to database"
    @echo ""
    @echo "🏥 Monitoring:"
    @echo "  health          - Check service health"
    @echo "  status          - Show service status"
    @echo "  monitor         - Monitor resources"
    @echo ""
    @echo "⚡ Performance:"
    @echo "  bench-selector  - Benchmark selector"
    @echo "  bench-generator - Benchmark generator"
    @echo "  bench-auth      - Benchmark auth"
    @echo ""
    @echo "Run 'just --list' for complete command list"

# Import all modular just files
import 'just/database.just'
import 'just/docker.just'
import 'just/test.just'
import 'just/services.just'
import 'just/health.just'
import 'just/performance.just'

# Quick start - bring up system and check health
start:
    @just up
    @sleep 5
    @just health
    @echo "\n✨ System ready! Run 'just test-auth' to verify authentication."

# Quick stop - bring down system cleanly
stop:
    @just down
    @echo "👋 System stopped. Run 'just start' to bring it back up."

# Full system test
test-all:
    @echo "🧪 Running All Tests..."
    @just health
    @just test-auth
    @just test-integration
    @echo "\n✅ All tests complete!"
# First-time setup

first-time:
    @echo "🚀 Setting up BetterPrompts..."
    @echo "Installing Python dependencies..."
    @python3 -m venv venv || true
    @. venv/bin/activate && pip install -r requirements.txt
    @echo "Building Docker images..."
    @docker compose build
    @echo "Starting database..."
    @docker compose up -d postgres
    @sleep 5
    @echo "Setting up database..."
    @docker compose exec -T postgres psql -U betterprompts -d betterprompts < backend/infrastructure/database/migrations/001_initial_schema.sql
    @docker compose exec -T postgres psql -U betterprompts -d betterprompts < backend/services/api-gateway/internal/migrations/sql/002_fix_user_schema.sql
    @echo "Starting all services..."
    @docker compose up -d
    @sleep 10
    @echo "Running smoke test..."
    @curl -sf http://localhost:8000/api/v1/health && echo "✅ API Gateway working" || echo "❌ API Gateway not responding"
    @echo "✅ Setup complete! Use 'just up' to start and 'just down' to stop."
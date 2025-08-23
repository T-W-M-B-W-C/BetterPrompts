# Start the application

up:
    @docker compose up -d
    @docker compose ps
    @echo "✅ BetterPrompts is running at http://localhost:8000"

# Start with logs
up-logs:
    @docker compose up
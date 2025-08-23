# Stop the application

down:
    @docker compose down
    @echo "✅ BetterPrompts stopped"

# Stop and remove volumes (deletes data)
down-clean:
    @docker compose down -v
    @echo "✅ All data removed"
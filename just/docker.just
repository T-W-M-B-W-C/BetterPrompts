# Docker Service Management Commands

# Restart specific service(s)
restart service="all":
    #!/bin/bash
    if [ "{{service}}" = "all" ]; then
        docker compose restart
    else
        docker compose restart {{service}}
    fi
    @echo "🔄 Restarted {{service}}"

# View logs for a service
logs service="all" lines="50":
    #!/bin/bash
    if [ "{{service}}" = "all" ]; then
        docker compose logs --tail={{lines}}
    else
        docker compose logs {{service}} --tail={{lines}}
    fi

# Watch logs for errors
watch-errors:
    docker compose logs -f | grep -E "error|ERROR|Error|fail|FAIL|Fail"

# Clear all logs
clear-logs:
    docker compose logs --tail=0 -f > /dev/null &
    @echo "📝 Logs cleared"

# Rebuild services
rebuild service="all":
    #!/bin/bash
    if [ "{{service}}" = "all" ]; then
        docker compose build --no-cache
    else
        docker compose build --no-cache {{service}}
    fi
    @echo "🔨 Rebuilt {{service}}"

# Show service configuration
show-config service="technique-selector":
    @echo "⚙️ Configuration for {{service}}:"
    @docker exec betterprompts-{{service}} cat /app/configs/*.yaml | head -50
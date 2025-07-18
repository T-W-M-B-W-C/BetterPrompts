#!/bin/sh

# Health check script for nginx
if [ -f /var/run/nginx.pid ]; then
    if ps -p $(cat /var/run/nginx.pid) > /dev/null 2>&1; then
        # Check if nginx is responding
        curl -f http://localhost/health > /dev/null 2>&1
        exit $?
    fi
fi

exit 1
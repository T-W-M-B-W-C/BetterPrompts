# Nginx API Gateway
FROM nginx:1.25-alpine

# Install dependencies
RUN apk add --no-cache curl

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/

# Create cache directory and fix permissions
RUN mkdir -p /var/cache/nginx/api_cache /var/run /var/log/nginx && \
    chown -R nginx:nginx /var/cache/nginx /var/run /var/log/nginx && \
    chmod -R 755 /var/run

# Add health check script
COPY healthcheck.sh /usr/local/bin/healthcheck
RUN chmod +x /usr/local/bin/healthcheck

# Note: Running as root to avoid permission issues
# USER nginx

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD /usr/local/bin/healthcheck || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
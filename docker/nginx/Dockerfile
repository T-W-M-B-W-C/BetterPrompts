# Nginx API Gateway
FROM nginx:1.25-alpine

# Install dependencies
RUN apk add --no-cache curl

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/

# Create cache directory
RUN mkdir -p /var/cache/nginx/api_cache && \
    chown -R nginx:nginx /var/cache/nginx

# Add health check script
COPY healthcheck.sh /usr/local/bin/healthcheck
RUN chmod +x /usr/local/bin/healthcheck

# Switch to nginx user (already exists in nginx:alpine)
USER nginx

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD /usr/local/bin/healthcheck || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
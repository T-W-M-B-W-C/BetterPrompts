# Frontend - Next.js Application
# Build stage
FROM node:20-alpine AS builder

# Add build arguments for environment variables
ARG NEXT_PUBLIC_API_URL

# Set environment variables for build
ENV NODE_ENV=production
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Set working directory
WORKDIR /app

# Install dependencies first (better layer caching)
COPY package*.json ./
RUN npm ci --legacy-peer-deps --production=false && \
    npm install tailwindcss postcss autoprefixer --save-dev --legacy-peer-deps && \
    npm cache clean --force

# Copy source code
COPY . .

# Replace globals.css with Docker-compatible version and remove PostCSS configs
RUN cp src/app/globals-docker.css src/app/globals.css && \
    rm -f postcss.config.js postcss.config.mjs tailwind.config.js tailwind.config.ts

# Install swc dependencies explicitly for Next.js
RUN npm install @next/swc-linux-x64-musl --legacy-peer-deps && \
    npm cache clean --force

# Ensure all dependencies are installed
RUN npm list

# Build the application
ENV NEXT_TELEMETRY_DISABLED=1
ENV NPM_CONFIG_LEGACY_PEER_DEPS=true
RUN npm run build

# Production stage
FROM node:20-alpine AS runner

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

WORKDIR /app

# Copy built application from builder
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

# Set environment variables
ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node healthcheck.js || exit 1

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Start the application
CMD ["node", "/app/server.js"]
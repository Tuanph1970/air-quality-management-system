# =============================================================================
# Frontend - serve pre-built React app with Nginx
# Build the frontend locally (outside Docker) before running docker compose build.
# deploy.sh handles: npm install + npm run build → dist/
# =============================================================================
FROM nginx:1.25-alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy pre-built assets (built by deploy.sh before docker compose build)
COPY dist /usr/share/nginx/html

# Permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:80/health || exit 1

CMD ["nginx", "-g", "daemon off;"]

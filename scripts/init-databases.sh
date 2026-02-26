#!/bin/bash
# Initialize all databases for the AQMS microservices

set -e

echo "Initializing databases..."

# Wait for databases to be ready
echo "Waiting for databases to be ready..."
sleep 5

# Run migrations for each service
services=("factory-service" "sensor-service" "alert-service" "user-service")

for service in "${services[@]}"; do
    echo "Running migrations for $service..."
    docker-compose exec "$service" alembic upgrade head || echo "Warning: $service migrations skipped"
done

echo "Database initialization complete."

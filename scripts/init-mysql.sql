-- =============================================================================
-- MySQL Initialization Script
-- Creates all databases for the Air Quality Management System
-- =============================================================================
-- This runs automatically on first MySQL container startup
-- (mounted into /docker-entrypoint-initdb.d/)
-- =============================================================================

CREATE DATABASE IF NOT EXISTS factory_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS sensor_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS alert_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS user_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS remote_sensing_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

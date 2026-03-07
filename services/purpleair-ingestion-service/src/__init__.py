"""PurpleAir Data Ingestion Service.

A lightweight service for receiving data from PurpleAir Flex-Air Quality Monitors.
Runs on port 8008 and accepts webhook data from PurpleAir devices.

Features:
- Webhook endpoint for PurpleAir device data push
- Cloud API polling for PurpleAir sensors
- Fake data generation for demonstration
- Publishes events to RabbitMQ for AQI recalculation
"""
from __future__ import annotations

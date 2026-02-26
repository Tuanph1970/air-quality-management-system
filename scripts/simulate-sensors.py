"""Simulate sensor data for development and testing."""
import asyncio
import random


async def generate_reading():
    """Generate a random sensor reading."""
    return {
        "pm25": round(random.uniform(5, 200), 2),
        "pm10": round(random.uniform(10, 300), 2),
        "co": round(random.uniform(0.1, 10), 2),
        "no2": round(random.uniform(5, 150), 2),
        "so2": round(random.uniform(2, 100), 2),
        "o3": round(random.uniform(10, 200), 2),
    }


async def simulate(interval_seconds: int = 30):
    """Simulate sensor readings at regular intervals."""
    print(f"Starting sensor simulation (interval: {interval_seconds}s)...")
    while True:
        reading = await generate_reading()
        print(f"Generated reading: {reading}")
        # TODO: Submit reading to sensor service API
        await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    asyncio.run(simulate())

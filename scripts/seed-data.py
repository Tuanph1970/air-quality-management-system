"""Seed sample data into the AQMS databases."""
import asyncio


async def seed_factories():
    """Seed sample factory data."""
    # TODO: Implement factory seeding
    print("Seeding factories...")


async def seed_sensors():
    """Seed sample sensor data."""
    # TODO: Implement sensor seeding
    print("Seeding sensors...")


async def seed_users():
    """Seed sample user data."""
    # TODO: Implement user seeding
    print("Seeding users...")


async def main():
    print("Starting data seeding...")
    await seed_users()
    await seed_factories()
    await seed_sensors()
    print("Data seeding complete.")


if __name__ == "__main__":
    asyncio.run(main())

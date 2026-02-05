"""Database connection management using Prisma."""

from prisma import Prisma

db = Prisma()


async def connect_db():
    """Connect to the database."""
    await db.connect()


async def get_db():
    """Get database connection, connecting if necessary."""
    if not db.is_connected():
        await connect_db()
    return db


async def disconnect_db():
    """Disconnect from the database."""
    await db.disconnect()

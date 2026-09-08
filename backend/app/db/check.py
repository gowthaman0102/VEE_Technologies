import asyncio

from sqlalchemy import text

from app.db.session import engine


async def check_database() -> None:
    async with engine.connect() as connection:
        result = await connection.execute(
            text(
                """
                SELECT
                    current_database() AS database_name,
                    current_user AS database_user,
                    version() AS postgres_version
                """
            )
        )

        row = result.mappings().one()

        print("Database connection: OK")
        print(f"Database: {row['database_name']}")
        print(f"User: {row['database_user']}")
        print(f"PostgreSQL: {row['postgres_version']}")

        vector_result = await connection.execute(
            text(
                """
                SELECT extversion
                FROM pg_extension
                WHERE extname = 'vector'
                """
            )
        )

        vector_version = vector_result.scalar_one_or_none()

        if vector_version:
            print(f"pgvector: {vector_version}")
        else:
            print("pgvector: NOT INSTALLED")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_database())

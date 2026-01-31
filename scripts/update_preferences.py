import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recommendation_service.infrastructure.database.connection import get_db_session
from recommendation_service.services.user_preference import UserPreferenceService


async def main():
    print("Updating user preference embeddings...")
    print("This aggregates user interactions into preference vectors for personalization.\n")

    async with get_db_session() as session:
        service = UserPreferenceService(session)

        result = await service.update_all_active_users(
            min_interactions=3,
            batch_size=100,
        )

        print("=== Results ===")
        print(f"Total users processed: {result.get('total_users', 0)}")
        print(f"Successfully updated: {result.get('updated', 0)}")
        print(f"Errors: {result.get('errors', 0)}")

        if result.get("updated", 0) > 0:
            print("\n✓ User preferences updated successfully!")
            print("\nUsers now have personalized embeddings based on their interactions.")
            print("The recommendation engine will use these for content-based personalization.")
        else:
            print("\n⚠ No users were updated.")
            print("Make sure users have at least 3 interactions in the last 90 days.")


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import json
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import asyncpg
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB", "reemio_db"),
}

PUBLIC_EVENT_TYPES = [
    "PRODUCT_VIEWED",
    "CART_ITEM_ADDED",
    "CART_ITEM_REMOVED",
    "CHECKOUT_STARTED",
    "PURCHASED",
]

RECOMMENDER_INTERACTION_TYPES = [
    "VIEW",
    "CART_ADD",
    "CART_REMOVE",
    "PURCHASE",
    "WISHLIST_ADD",
    "SEARCH",
    "RECOMMENDATION_CLICK",
    "RECOMMENDATION_VIEW",
]

RECOMMENDATION_CONTEXTS = ["homepage", "product_page", "cart", "email"]
DEVICES = ["desktop", "mobile", "tablet"]
SOURCES = ["home", "search", "pdp", "cart", "email", "direct"]

SEARCH_QUERIES = [
    {"query": "wireless headphones", "filters": {"category": "Electronics", "price_max": 5000}},
    {"query": "running shoes", "filters": {"category": "Sports", "size": "10"}},
    {"query": "office chair", "filters": {"category": "Furniture", "in_stock": True}},
    {"query": "laptop stand", "filters": {"price_min": 2000, "price_max": 10000}},
    {"query": "organic coffee", "filters": {"category": "Grocery"}},
    {"query": "kitchen knife set", "filters": {"category": "Home & Kitchen"}},
    {"query": "yoga mat", "filters": {"category": "Sports", "price_max": 3000}},
    {"query": "bluetooth speaker", "filters": {"category": "Electronics"}},
    {"query": "garden tools", "filters": {"category": "Garden"}},
    {"query": "notebook", "filters": {"category": "Office"}},
]

USER_PERSONAS = {
    "power_shopper": {
        "users": ["user_alice"],
        "view_count": (15, 25),
        "cart_add_rate": 0.4,
        "purchase_rate": 0.6,
        "reco_click_rate": 0.5,
        "search_count": (3, 6),
    },
    "browser": {
        "users": ["user_bob"],
        "view_count": (20, 35),
        "cart_add_rate": 0.15,
        "purchase_rate": 0.2,
        "reco_click_rate": 0.2,
        "search_count": (5, 10),
    },
    "cart_abandoner": {
        "users": ["user_carol"],
        "view_count": (10, 20),
        "cart_add_rate": 0.5,
        "purchase_rate": 0.1,
        "reco_click_rate": 0.3,
        "search_count": (2, 5),
    },
    "search_heavy": {
        "users": [],
        "view_count": (8, 15),
        "cart_add_rate": 0.25,
        "purchase_rate": 0.3,
        "reco_click_rate": 0.25,
        "search_count": (10, 20),
    },
    "recommendation_responder": {
        "users": [],
        "view_count": (12, 20),
        "cart_add_rate": 0.35,
        "purchase_rate": 0.4,
        "reco_click_rate": 0.7,
        "search_count": (2, 4),
    },
    "light_user": {
        "users": [],
        "view_count": (3, 8),
        "cart_add_rate": 0.2,
        "purchase_rate": 0.15,
        "reco_click_rate": 0.15,
        "search_count": (0, 2),
    },
}


def random_timestamp(days_ago_max: int = 30) -> datetime:
    now = datetime.now()
    days_ago = random.uniform(0, days_ago_max)
    hours = random.randint(6, 23)
    minutes = random.randint(0, 59)
    return now - timedelta(days=days_ago, hours=24 - hours, minutes=60 - minutes)


def generate_session_id() -> str:
    return f"sess_{uuid4().hex[:16]}"


def generate_time_on_page(interaction_type: str) -> int:
    if interaction_type in ["VIEW", "PRODUCT_VIEWED"]:
        return random.randint(15, 180)
    elif interaction_type in ["SEARCH"]:
        return random.randint(5, 60)
    elif interaction_type in ["CART_ADD", "CART_ITEM_ADDED", "WISHLIST_ADD"]:
        return random.randint(3, 30)
    elif interaction_type in ["RECOMMENDATION_VIEW"]:
        return random.randint(1, 10)
    elif interaction_type in ["RECOMMENDATION_CLICK"]:
        return random.randint(2, 15)
    else:
        return random.randint(5, 45)


def generate_scroll_depth(interaction_type: str) -> int:
    if interaction_type in ["VIEW", "PRODUCT_VIEWED"]:
        return random.randint(40, 100)
    elif interaction_type in ["SEARCH"]:
        return random.randint(20, 80)
    else:
        return random.randint(10, 60)


async def fetch_user_ids(conn) -> list[str]:
    rows = await conn.fetch("SELECT id FROM public.users LIMIT 15")
    return [row["id"] for row in rows]


async def fetch_product_ids(conn) -> list[dict]:
    rows = await conn.fetch("""
        SELECT external_product_id, name, category, price_cents
        FROM recommender.product_embeddings
        WHERE is_active = true
        ORDER BY random()
        LIMIT 150
    """)
    return [dict(row) for row in rows]


async def fetch_order_ids(conn) -> list[str]:
    rows = await conn.fetch("SELECT id FROM public.orders LIMIT 20")
    return [row["id"] for row in rows]


async def clear_seed_data(conn):
    await conn.execute("""
        DELETE FROM public.events WHERE metadata->>'seed_data' = 'true'
    """)
    await conn.execute("""
        DELETE FROM recommender.user_interactions WHERE extra_data->>'seed_data' = 'true'
    """)
    print("Cleared existing seed data")


def generate_user_session_interactions(
    user_id: str,
    products: list[dict],
    persona_config: dict,
    session_id: str,
    session_start: datetime,
) -> tuple[list[dict], list[dict]]:
    public_events = []
    recommender_interactions = []

    session_duration = random.randint(60, 1800)
    current_time = session_start
    device = random.choice(DEVICES)
    source = random.choice(SOURCES)

    session_products = random.sample(products, min(len(products), random.randint(3, 10)))

    for i, product in enumerate(session_products):
        if random.random() > 0.8:
            continue

        time_offset = random.randint(10, 120)
        current_time = current_time + timedelta(seconds=time_offset)

        time_on_page = generate_time_on_page("VIEW")
        scroll_depth = generate_scroll_depth("VIEW")

        base_metadata = {
            "seed_data": True,
            "sessionId": session_id,
            "source": source,
            "device": device,
            "timeOnPageSeconds": time_on_page,
            "sessionDurationSeconds": session_duration,
            "scrollDepthPercent": scroll_depth,
        }

        public_events.append({
            "id": str(uuid4()),
            "type": "PRODUCT_VIEWED",
            "userId": user_id,
            "productId": product["external_product_id"],
            "orderId": None,
            "metadata": json.dumps(base_metadata),
            "createdAt": current_time,
        })

        recommender_interactions.append({
            "external_user_id": user_id,
            "external_product_id": product["external_product_id"],
            "interaction_type": "VIEW",
            "search_query": None,
            "recommendation_context": None,
            "recommendation_position": None,
            "recommendation_request_id": None,
            "session_id": session_id,
            "extra_data": json.dumps({
                "seed_data": True,
                "timeOnPageSeconds": time_on_page,
                "scrollDepthPercent": scroll_depth,
                "device": device,
            }),
            "created_at": current_time,
        })

        if random.random() < persona_config["reco_click_rate"]:
            reco_context = random.choice(RECOMMENDATION_CONTEXTS)
            reco_position = random.randint(1, 8)
            reco_request_id = str(uuid4())

            recommender_interactions.append({
                "external_user_id": user_id,
                "external_product_id": product["external_product_id"],
                "interaction_type": "RECOMMENDATION_VIEW",
                "search_query": None,
                "recommendation_context": reco_context,
                "recommendation_position": reco_position,
                "recommendation_request_id": reco_request_id,
                "session_id": session_id,
                "extra_data": json.dumps({
                    "seed_data": True,
                    "timeOnPageSeconds": generate_time_on_page("RECOMMENDATION_VIEW"),
                    "device": device,
                }),
                "created_at": current_time + timedelta(seconds=random.randint(1, 10)),
            })

            if random.random() < 0.6:
                recommender_interactions.append({
                    "external_user_id": user_id,
                    "external_product_id": product["external_product_id"],
                    "interaction_type": "RECOMMENDATION_CLICK",
                    "search_query": None,
                    "recommendation_context": reco_context,
                    "recommendation_position": reco_position,
                    "recommendation_request_id": reco_request_id,
                    "session_id": session_id,
                    "extra_data": json.dumps({
                        "seed_data": True,
                        "timeOnPageSeconds": generate_time_on_page("RECOMMENDATION_CLICK"),
                        "device": device,
                    }),
                    "created_at": current_time + timedelta(seconds=random.randint(5, 20)),
                })

        if random.random() < persona_config["cart_add_rate"]:
            cart_time = current_time + timedelta(seconds=random.randint(20, 60))

            public_events.append({
                "id": str(uuid4()),
                "type": "CART_ITEM_ADDED",
                "userId": user_id,
                "productId": product["external_product_id"],
                "orderId": None,
                "metadata": json.dumps({
                    **base_metadata,
                    "quantity": random.randint(1, 3),
                    "timeOnPageSeconds": generate_time_on_page("CART_ADD"),
                }),
                "createdAt": cart_time,
            })

            recommender_interactions.append({
                "external_user_id": user_id,
                "external_product_id": product["external_product_id"],
                "interaction_type": "CART_ADD",
                "search_query": None,
                "recommendation_context": None,
                "recommendation_position": None,
                "recommendation_request_id": None,
                "session_id": session_id,
                "extra_data": json.dumps({
                    "seed_data": True,
                    "quantity": random.randint(1, 3),
                    "timeOnPageSeconds": generate_time_on_page("CART_ADD"),
                    "device": device,
                }),
                "created_at": cart_time,
            })

            if random.random() < 0.3:
                remove_time = cart_time + timedelta(seconds=random.randint(60, 300))

                public_events.append({
                    "id": str(uuid4()),
                    "type": "CART_ITEM_REMOVED",
                    "userId": user_id,
                    "productId": product["external_product_id"],
                    "orderId": None,
                    "metadata": json.dumps({
                        **base_metadata,
                        "timeOnPageSeconds": generate_time_on_page("CART_REMOVE"),
                    }),
                    "createdAt": remove_time,
                })

                recommender_interactions.append({
                    "external_user_id": user_id,
                    "external_product_id": product["external_product_id"],
                    "interaction_type": "CART_REMOVE",
                    "search_query": None,
                    "recommendation_context": None,
                    "recommendation_position": None,
                    "recommendation_request_id": None,
                    "session_id": session_id,
                    "extra_data": json.dumps({
                        "seed_data": True,
                        "timeOnPageSeconds": generate_time_on_page("CART_REMOVE"),
                        "device": device,
                    }),
                    "created_at": remove_time,
                })

        if random.random() < 0.15:
            recommender_interactions.append({
                "external_user_id": user_id,
                "external_product_id": product["external_product_id"],
                "interaction_type": "WISHLIST_ADD",
                "search_query": None,
                "recommendation_context": None,
                "recommendation_position": None,
                "recommendation_request_id": None,
                "session_id": session_id,
                "extra_data": json.dumps({
                    "seed_data": True,
                    "device": device,
                }),
                "created_at": current_time + timedelta(seconds=random.randint(30, 90)),
            })

    return public_events, recommender_interactions


def generate_search_interactions(
    user_id: str,
    search_count: int,
    session_id: str,
    session_start: datetime,
    device: str,
) -> list[dict]:
    interactions = []

    for _ in range(search_count):
        search_data = random.choice(SEARCH_QUERIES)
        search_time = session_start + timedelta(seconds=random.randint(10, 600))

        interactions.append({
            "external_user_id": user_id,
            "external_product_id": None,
            "interaction_type": "SEARCH",
            "search_query": search_data["query"],
            "recommendation_context": None,
            "recommendation_position": None,
            "recommendation_request_id": None,
            "session_id": session_id,
            "extra_data": json.dumps({
                "seed_data": True,
                "filters": search_data["filters"],
                "resultsCount": random.randint(5, 150),
                "timeOnPageSeconds": generate_time_on_page("SEARCH"),
                "device": device,
            }),
            "created_at": search_time,
        })

    return interactions


def generate_purchase_events(
    user_id: str,
    products: list[dict],
    order_ids: list[str],
    purchase_count: int,
    base_time: datetime,
    session_id: str,
    device: str,
) -> tuple[list[dict], list[dict]]:
    public_events = []
    recommender_interactions = []

    purchase_products = random.sample(products, min(len(products), purchase_count))

    for product in purchase_products:
        order_id = random.choice(order_ids) if order_ids else None
        purchase_time = base_time + timedelta(seconds=random.randint(300, 1800))

        public_events.append({
            "id": str(uuid4()),
            "type": "CHECKOUT_STARTED",
            "userId": user_id,
            "productId": product["external_product_id"],
            "orderId": order_id,
            "metadata": json.dumps({
                "seed_data": True,
                "sessionId": session_id,
                "device": device,
                "cartValue": product["price_cents"],
                "timeOnPageSeconds": generate_time_on_page("CHECKOUT"),
            }),
            "createdAt": purchase_time - timedelta(seconds=random.randint(60, 300)),
        })

        public_events.append({
            "id": str(uuid4()),
            "type": "PURCHASED",
            "userId": user_id,
            "productId": product["external_product_id"],
            "orderId": order_id,
            "metadata": json.dumps({
                "seed_data": True,
                "sessionId": session_id,
                "device": device,
                "quantity": random.randint(1, 2),
                "totalCents": product["price_cents"],
                "timeOnPageSeconds": generate_time_on_page("PURCHASE"),
            }),
            "createdAt": purchase_time,
        })

        recommender_interactions.append({
            "external_user_id": user_id,
            "external_product_id": product["external_product_id"],
            "interaction_type": "PURCHASE",
            "search_query": None,
            "recommendation_context": None,
            "recommendation_position": None,
            "recommendation_request_id": None,
            "session_id": session_id,
            "extra_data": json.dumps({
                "seed_data": True,
                "orderId": order_id,
                "quantity": random.randint(1, 2),
                "priceCents": product["price_cents"],
                "device": device,
            }),
            "created_at": purchase_time,
        })

    return public_events, recommender_interactions


async def insert_public_events(conn, events: list[dict]):
    if not events:
        return

    await conn.executemany("""
        INSERT INTO public.events (id, type, "userId", "productId", "orderId", metadata, "createdAt")
        VALUES ($1, $2::public."EventType", $3, $4, $5, $6::jsonb, $7)
        ON CONFLICT (id) DO NOTHING
    """, [
        (e["id"], e["type"], e["userId"], e["productId"], e["orderId"], e["metadata"], e["createdAt"])
        for e in events
    ])


async def insert_recommender_interactions(conn, interactions: list[dict]):
    if not interactions:
        return

    await conn.executemany("""
        INSERT INTO recommender.user_interactions
        (external_user_id, external_product_id, interaction_type, search_query,
         recommendation_context, recommendation_position, recommendation_request_id,
         session_id, extra_data, created_at)
        VALUES ($1, $2, $3::recommender.interactiontype, $4, $5, $6, $7, $8, $9::json, $10)
    """, [
        (
            i["external_user_id"], i["external_product_id"], i["interaction_type"],
            i["search_query"], i["recommendation_context"], i["recommendation_position"],
            i["recommendation_request_id"], i["session_id"], i["extra_data"], i["created_at"]
        )
        for i in interactions
    ])


async def main():
    print("Connecting to database...")
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        print("Clearing existing seed data...")
        await clear_seed_data(conn)

        print("Fetching existing IDs...")
        user_ids = await fetch_user_ids(conn)
        products = await fetch_product_ids(conn)
        order_ids = await fetch_order_ids(conn)

        print(f"Found {len(user_ids)} users, {len(products)} products, {len(order_ids)} orders")

        if len(user_ids) < 3:
            print("Warning: Not enough users found, using demo user IDs")
            user_ids = ["user_alice", "user_bob", "user_carol"]

        demo_user_mapping = {
            "user_alice": user_ids[0] if user_ids else "user_alice",
            "user_bob": user_ids[1] if len(user_ids) > 1 else "user_bob",
            "user_carol": user_ids[2] if len(user_ids) > 2 else "user_carol",
        }

        additional_users = user_ids[3:] if len(user_ids) > 3 else []

        USER_PERSONAS["search_heavy"]["users"] = additional_users[:2] if len(additional_users) >= 2 else ["user_dave", "user_eve"]
        USER_PERSONAS["recommendation_responder"]["users"] = additional_users[2:4] if len(additional_users) >= 4 else ["user_frank", "user_grace"]
        USER_PERSONAS["light_user"]["users"] = additional_users[4:7] if len(additional_users) >= 7 else ["user_henry", "user_ivy", "user_jack"]

        all_public_events = []
        all_recommender_interactions = []

        print("Generating interactions for each persona...")

        for persona_name, config in USER_PERSONAS.items():
            for user_id in config["users"]:
                actual_user_id = demo_user_mapping.get(user_id, user_id)

                num_sessions = random.randint(3, 8)

                for _ in range(num_sessions):
                    session_id = generate_session_id()
                    session_start = random_timestamp(30)
                    device = random.choice(DEVICES)

                    pub_events, reco_interactions = generate_user_session_interactions(
                        actual_user_id, products, config, session_id, session_start
                    )
                    all_public_events.extend(pub_events)
                    all_recommender_interactions.extend(reco_interactions)

                    search_min, search_max = config["search_count"]
                    search_count = random.randint(search_min, search_max) // num_sessions
                    if search_count > 0:
                        search_interactions = generate_search_interactions(
                            actual_user_id, search_count, session_id, session_start, device
                        )
                        all_recommender_interactions.extend(search_interactions)

                    if random.random() < config["purchase_rate"]:
                        purchase_count = random.randint(1, 3)
                        pub_purchases, reco_purchases = generate_purchase_events(
                            actual_user_id, products, order_ids, purchase_count,
                            session_start, session_id, device
                        )
                        all_public_events.extend(pub_purchases)
                        all_recommender_interactions.extend(reco_purchases)

                print(f"  {persona_name}: {user_id} -> {actual_user_id}")

        print(f"\nInserting {len(all_public_events)} public events...")
        await insert_public_events(conn, all_public_events)

        print(f"Inserting {len(all_recommender_interactions)} recommender interactions...")
        await insert_recommender_interactions(conn, all_recommender_interactions)

        print("\n=== Summary ===")

        event_counts = await conn.fetch("""
            SELECT type, COUNT(*) as count
            FROM public.events
            WHERE metadata->>'seed_data' = 'true'
            GROUP BY type
            ORDER BY count DESC
        """)
        print("\nPublic Events by Type:")
        for row in event_counts:
            print(f"  {row['type']}: {row['count']}")

        interaction_counts = await conn.fetch("""
            SELECT interaction_type, COUNT(*) as count
            FROM recommender.user_interactions
            WHERE extra_data->>'seed_data' = 'true'
            GROUP BY interaction_type
            ORDER BY count DESC
        """)
        print("\nRecommender Interactions by Type:")
        for row in interaction_counts:
            print(f"  {row['interaction_type']}: {row['count']}")

        user_counts = await conn.fetch("""
            SELECT external_user_id, COUNT(*) as count
            FROM recommender.user_interactions
            WHERE extra_data->>'seed_data' = 'true'
            GROUP BY external_user_id
            ORDER BY count DESC
            LIMIT 10
        """)
        print("\nTop 10 Users by Interaction Count:")
        for row in user_counts:
            print(f"  {row['external_user_id']}: {row['count']}")

        print("\n✓ Seed data inserted successfully!")
        print("\nNext step: Run 'python scripts/update_preferences.py' to build user embeddings")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

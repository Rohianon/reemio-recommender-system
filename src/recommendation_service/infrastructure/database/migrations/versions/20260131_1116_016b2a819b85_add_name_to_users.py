"""add_name_to_users

Revision ID: 016b2a819b85
Revises: 0bcb764abf3d
Create Date: 2026-01-31 11:16:09.291485+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '016b2a819b85'
down_revision: Union[str, None] = '0bcb764abf3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

KENYAN_NAMES = [
    ("805b5c8c-ac76-4422-803b-80151c911fd3", "Wanjiku Muthoni"),
    ("b8355b11-784f-467b-b611-216fdb6dcd91", "Otieno Ochieng"),
    ("69b2bf41-1e9f-4753-95c8-43788297e692", "Akinyi Adhiambo"),
    ("f2de971c-12dd-4394-8557-87160be804d4", "Kipchoge Korir"),
    ("ea4b669f-04f5-493b-94ba-f0a9dcb4ce43", "Nyambura Wangari"),
    ("c36fa92e-61f7-4e92-ab2a-7636f87dfa65", "Omondi Onyango"),
    ("c08b7035-502d-47f9-9237-80e1aadac147", "Chebet Jepkosgei"),
    ("ba75f8fb-12ed-48a5-af36-f9a8d3ee5e6d", "Mutua Kioko"),
    ("e6eb8dc7-7b3e-4bab-b7dd-ec08576e5732", "Nafula Wekesa"),
    ("3c19ab6b-7e34-4f91-9435-3282fa8a18aa", "Kimani Njoroge"),
    ("79013234-1bf5-4a1c-a25b-0e2e347e6ecc", "Awino Auma"),
    ("2a54e089-f6e8-40b8-94d1-27237ba82506", "Rotich Kiprono"),
    ("43844712-33d8-45df-a5a6-81a6c926dd83", "Wairimu Njeri"),
    ("4012deee-abff-4524-82bc-c7f39a322499", "Barasa Wanjala"),
    ("a9472af0-f52c-4505-8352-c7d383b44bb1", "Moraa Kemunto"),
    ("5da08cf5-78d1-4a73-ad8b-1352781283ee", "Nzioka Mutuku"),
    ("d0ec6736-892d-466f-9e64-9ae2a66127a7", "Nekesa Simiyu"),
    ("9b1f35e4-8ce3-44bc-81fb-b0653ff9c391", "Karanja Mwangi"),
    ("36a38635-e8e7-4f7d-82f6-207bb50a0cbe", "Anyango Akoth"),
    ("5ca48fe4-2c99-4e84-be4d-eb9459165c1b", "Chepkemoi Sang"),
    ("e2870a70-c59d-402c-9bbc-cc5d1c155782", "Mwende Kavuu"),
]


def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(255), nullable=True), schema="public")

    connection = op.get_bind()
    for user_id, name in KENYAN_NAMES:
        connection.execute(
            sa.text('UPDATE public.users SET name = :name WHERE id = :id'),
            {"name": name, "id": user_id}
        )


def downgrade() -> None:
    op.drop_column("users", "name", schema="public")

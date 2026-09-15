"""migrate active company to vee technologies

Revision ID: c5a6738cf250
Revises: 4fcdf143b86b
Create Date: 2026-09-15 21:30:20.531617
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c5a6738cf250"
down_revision: Union[
    str,
    Sequence[str],
    None,
] = "4fcdf143b86b"

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


VEE_ALIASES = (
    "VEE Technologies",
    "Vee Technologies",
    "Vee Technologies Pvt Ltd",
    "Vee Technologies Private Limited",
)


VEE_TOPICS = (
    ("Artificial Intelligence", "high"),
    ("Technology", "high"),
    ("Cybersecurity", "high"),
    ("Partnership", "medium"),
    ("Acquisition", "high"),
    ("Expansion", "medium"),
    ("Leadership Change", "medium"),
    ("Product or Service Launch", "medium"),
    ("Financial Development", "high"),
    ("Reputation", "high"),
)


def upgrade() -> None:
    """Switch active monitoring from PayU to VEE Technologies."""

    bind = op.get_bind()

    payu = bind.execute(
        sa.text(
            """
            SELECT id, client_id
            FROM companies
            WHERE name = :name
            ORDER BY id
            LIMIT 1
            """
        ),
        {
            "name": "PayU",
        },
    ).mappings().first()

    vee = bind.execute(
        sa.text(
            """
            SELECT id, client_id
            FROM companies
            WHERE name = :name
            ORDER BY id
            LIMIT 1
            """
        ),
        {
            "name": "VEE Technologies",
        },
    ).mappings().first()

    # Preserve PayU as historical data,
    # but stop actively monitoring it.
    if payu is not None:
        bind.execute(
            sa.text(
                """
                UPDATE companies
                SET is_active = FALSE
                WHERE id = :company_id
                """
            ),
            {
                "company_id": payu["id"],
            },
        )

    # If VEE does not exist yet, reuse the same
    # client that previously owned PayU.
    if vee is None:
        if payu is None:
            # Nothing to migrate on an empty/unseeded
            # database. The normal client/company setup
            # process can create the company later.
            return

        vee = bind.execute(
            sa.text(
                """
                INSERT INTO companies (
                    client_id,
                    name,
                    industry,
                    website,
                    is_active
                )
                VALUES (
                    :client_id,
                    :name,
                    :industry,
                    :website,
                    TRUE
                )
                RETURNING id, client_id
                """
            ),
            {
                "client_id": payu["client_id"],
                "name": "VEE Technologies",
                "industry": (
                    "Technology and Professional Services"
                ),
                "website": (
                    "https://www.veetechnologies.com"
                ),
            },
        ).mappings().one()

    else:
        # Make an existing manually-created VEE record
        # match the canonical configuration.
        bind.execute(
            sa.text(
                """
                UPDATE companies
                SET
                    industry = :industry,
                    website = :website,
                    is_active = TRUE
                WHERE id = :company_id
                """
            ),
            {
                "company_id": vee["id"],
                "industry": (
                    "Technology and Professional Services"
                ),
                "website": (
                    "https://www.veetechnologies.com"
                ),
            },
        )

    vee_id = vee["id"]

    for alias in VEE_ALIASES:
        exists = bind.execute(
            sa.text(
                """
                SELECT 1
                FROM company_aliases
                WHERE
                    company_id = :company_id
                    AND lower(alias) = lower(:alias)
                LIMIT 1
                """
            ),
            {
                "company_id": vee_id,
                "alias": alias,
            },
        ).first()

        if exists is None:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO company_aliases (
                        company_id,
                        alias
                    )
                    VALUES (
                        :company_id,
                        :alias
                    )
                    """
                ),
                {
                    "company_id": vee_id,
                    "alias": alias,
                },
            )

    for topic, priority in VEE_TOPICS:
        existing_topic = bind.execute(
            sa.text(
                """
                SELECT id
                FROM monitoring_topics
                WHERE
                    company_id = :company_id
                    AND lower(topic) = lower(:topic)
                LIMIT 1
                """
            ),
            {
                "company_id": vee_id,
                "topic": topic,
            },
        ).mappings().first()

        if existing_topic is None:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO monitoring_topics (
                        company_id,
                        topic,
                        priority,
                        is_active
                    )
                    VALUES (
                        :company_id,
                        :topic,
                        :priority,
                        TRUE
                    )
                    """
                ),
                {
                    "company_id": vee_id,
                    "topic": topic,
                    "priority": priority,
                },
            )

        else:
            bind.execute(
                sa.text(
                    """
                    UPDATE monitoring_topics
                    SET
                        priority = :priority,
                        is_active = TRUE
                    WHERE id = :topic_id
                    """
                ),
                {
                    "topic_id": (
                        existing_topic["id"]
                    ),
                    "priority": priority,
                },
            )


def downgrade() -> None:
    """Return active monitoring to PayU without deleting history."""

    bind = op.get_bind()

    # Reactivate the original PayU configuration.
    bind.execute(
        sa.text(
            """
            UPDATE companies
            SET is_active = TRUE
            WHERE name = :name
            """
        ),
        {
            "name": "PayU",
        },
    )

    # Keep VEE instead of deleting it because future
    # articles, triage, risks or reports may reference it.
    # A downgrade therefore makes it inactive while
    # preserving referential and historical integrity.
    bind.execute(
        sa.text(
            """
            UPDATE companies
            SET is_active = FALSE
            WHERE name = :name
            """
        ),
        {
            "name": "VEE Technologies",
        },
    )

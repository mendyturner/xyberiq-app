"""${message}"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

${imports if imports else ""}


revision = ${revision!r}
down_revision = ${down_revision!r}
branch_labels = ${branch_labels!r}
depends_on = ${depends_on!r}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}

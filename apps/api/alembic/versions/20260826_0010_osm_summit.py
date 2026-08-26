"""Allow the OSM summit peak as a distinct feature kind.

The South Col snapshot could hold only ``camp`` and ``route`` rows, so the
8848.86 m summit - the one point every Summit Window decision is about - had no
place to live and the 3D scene had no summit marker. OSM publishes it as
``natural=peak`` node 164979149 with ``ele=8848.86``; it is a peak, not a camp,
so it gets its own kind rather than being mislabelled.

Revision ID: 20260826_0010
Revises: 20260826_0009
Create Date: 2026-08-26 00:00:00 UTC
"""

# pylint: disable=invalid-name,no-member,wrong-import-order,implicit-str-concat
# Alembic requires these revision variable names and operation proxies.

from alembic import op

revision = "20260826_0010"
down_revision = "20260826_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Extend the feature-kind constraint to admit the summit peak."""
    op.drop_constraint("ck_osm_feature_kind", "osm_feature", type_="check")
    op.create_check_constraint(
        "ck_osm_feature_kind",
        "osm_feature",
        "feature_kind IN ('camp', 'route', 'summit')",
    )


def downgrade() -> None:
    """Restore the camp/route-only constraint, dropping any summit rows first."""
    op.execute("DELETE FROM osm_feature WHERE feature_kind = 'summit'")
    op.drop_constraint("ck_osm_feature_kind", "osm_feature", type_="check")
    op.create_check_constraint(
        "ck_osm_feature_kind",
        "osm_feature",
        "feature_kind IN ('camp', 'route')",
    )

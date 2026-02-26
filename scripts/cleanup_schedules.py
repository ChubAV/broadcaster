"""Remove stale group IDs from schedules.

Finds schedules that reference groups which no longer exist in the DB
and cleans up the group_ids JSON arrays.

Usage:
    uv run python scripts/cleanup_schedules.py          # dry-run (default)
    uv run python scripts/cleanup_schedules.py --apply   # apply changes
"""

import argparse
import asyncio

from sqlalchemy import select

from app.config import get_settings
from app.database import Base, get_engine, get_session_factory
from app.models.group import Group
from app.models.schedule import Schedule


async def main(apply: bool) -> None:
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        # Load all existing group IDs into a set
        result = await session.execute(select(Group.id))
        existing_group_ids = set(result.scalars().all())

        # Scan all schedules
        result = await session.execute(select(Schedule))
        schedules = list(result.scalars().all())

        updated = 0
        for schedule in schedules:
            if not schedule.group_ids:
                continue

            clean_ids = [gid for gid in schedule.group_ids if gid in existing_group_ids]
            removed = len(schedule.group_ids) - len(clean_ids)

            if removed == 0:
                continue

            stale = [gid for gid in schedule.group_ids if gid not in existing_group_ids]
            print(f"  Schedule #{schedule.id}: removing {stale} ({removed} stale IDs)")
            schedule.group_ids = clean_ids
            updated += 1

        if updated == 0:
            print("Nothing to clean up — all schedules are consistent.")
        elif apply:
            await session.commit()
            print(f"\nDone. Updated {updated} schedule(s).")
        else:
            print(f"\nDry run. {updated} schedule(s) would be updated. Run with --apply to commit.")

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean stale group IDs from schedules")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")
    args = parser.parse_args()
    asyncio.run(main(apply=args.apply))

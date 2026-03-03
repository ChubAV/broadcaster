"""Collect group metadata from messengers into group_info reference table.

Iterates over all messenger accounts, connects to each, and fetches
detailed group info (members, admins, metadata) for every group.

Usage:
    uv run python scripts/collect_group_info.py                    # dry-run (default)
    uv run python scripts/collect_group_info.py --apply            # write to DB
    uv run python scripts/collect_group_info.py --apply --force    # update existing
    uv run python scripts/collect_group_info.py --user-id 5        # only for user 5
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, distinct

from app.config import get_settings
from app.database import get_engine, get_session_factory
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.repositories.group_info import GroupInfoRepository
from app.services.messenger_factory import create_messenger


async def main(apply: bool, force: bool, user_id: int | None = None) -> None:
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        repo = GroupInfoRepository(session)

        # 1. Load existing keys
        existing_keys = await repo.list_all_keys()
        print(f"Existing group_info records: {len(existing_keys)}")

        # 2. Load distinct (account_id, messenger_type, external_id) from groups
        query = select(
            Group.account_id,
            Group.messenger_type,
            Group.group_external_id,
        ).distinct()
        if user_id:
            query = query.where(Group.user_id == user_id)
            print(f"Filtering by user_id={user_id}")
        result = await session.execute(query)
        group_rows = list(result.all())
        print(f"Distinct groups in DB: {len(group_rows)}")

        # Group by account_id
        account_groups: dict[int, list[tuple[str, str]]] = {}
        for account_id, messenger_type, external_id in group_rows:
            account_groups.setdefault(account_id, []).append(
                (messenger_type, external_id)
            )

        collected = 0
        skipped = 0
        errors = 0

        for account_id, groups in account_groups.items():
            # Filter groups before connecting — avoid spinning up containers for nothing
            if not force:
                pending = [(mt, eid) for mt, eid in groups if (mt, eid) not in existing_keys]
                skipped += len(groups) - len(pending)
            else:
                pending = groups

            if not pending:
                print(f"  Account #{account_id}: all {len(groups)} groups already collected, skipping")
                continue

            # Load account
            account = await session.get(MessengerAccount, account_id)
            if not account:
                print(f"  Account #{account_id}: not found, skipping {len(pending)} groups")
                skipped += len(pending)
                continue

            # Create messenger
            try:
                messenger = create_messenger(account, settings)
            except Exception as e:
                print(f"  Account #{account_id} ({account.type}): cannot create messenger: {e}")
                skipped += len(pending)
                continue

            # Check connection
            try:
                connected = await messenger.check_connection()
            except Exception as e:
                print(f"  Account #{account_id} ({account.type}): connection check failed: {e}")
                skipped += len(pending)
                continue

            if not connected:
                print(f"  Account #{account_id} ({account.type}): offline, skipping {len(pending)} groups")
                skipped += len(pending)
                continue

            print(f"  Account #{account_id} ({account.type}): online, processing {len(pending)} groups...")

            for messenger_type, external_id in pending:

                try:
                    details = await messenger.get_group_details(external_id)
                except Exception as e:
                    print(f"    [{messenger_type}] {external_id}: error - {e}")
                    errors += 1
                    continue

                if details is None:
                    print(f"    [{messenger_type}] {external_id}: no details returned")
                    skipped += 1
                    continue

                key = (messenger_type, external_id)
                action = "update" if key in existing_keys else "create"
                print(f"    [{messenger_type}] {external_id}: {details.get('name', '?')} "
                      f"({details.get('member_count', '?')} members, "
                      f"{len(details.get('admins', []))} admins) [{action}]")

                if apply:
                    await repo.upsert(
                        messenger_type=messenger_type,
                        external_id=external_id,
                        name=details.get("name", external_id),
                        member_count=details.get("member_count"),
                        admin_contacts=details.get("admins"),
                        raw_metadata=details.get("raw"),
                    )
                    existing_keys.add(key)

                collected += 1

                # Rate limit delay
                await asyncio.sleep(0.5)

    print(f"\nSummary: collected={collected}, skipped={skipped}, errors={errors}")
    if not apply and collected > 0:
        print("Dry run. Run with --apply to write to DB.")

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect group metadata into group_info")
    parser.add_argument("--apply", action="store_true", help="Write to DB (default is dry-run)")
    parser.add_argument("--force", action="store_true", help="Update existing records")
    parser.add_argument("--user-id", type=int, default=None, help="Collect only for specific user")
    args = parser.parse_args()
    asyncio.run(main(apply=args.apply, force=args.force, user_id=args.user_id))

"""Move existing achievement videos from the private task bucket to the public bucket."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from minio.commonconfig import CopySource
from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.minio_client import BUCKET_NAMES, minio_client
from models.domains.achievements import Achievement

logger = logging.getLogger("alanko.migrate_achievement_videos")


def migrate(*, dry_run: bool) -> int:
    old_bucket = BUCKET_NAMES["videos"]
    new_bucket = BUCKET_NAMES["achievement_videos"]
    moved = 0

    if not minio_client.bucket_exists(new_bucket):
        if dry_run:
            logger.info("Would create bucket %s", new_bucket)
        else:
            minio_client.make_bucket(new_bucket)

    with SessionLocal() as db:
        achievements = (
            db.query(Achievement)
            .filter(Achievement.video_url.is_not(None))
            .order_by(Achievement.id.asc())
            .all()
        )
        for achievement in achievements:
            key = achievement.video_url
            try:
                minio_client.stat_object(old_bucket, key)
            except Exception:
                logger.warning("Source object is missing: %s/%s", old_bucket, key)
                continue

            if dry_run:
                logger.info("Would copy %s/%s to %s/%s", old_bucket, key, new_bucket, key)
                moved += 1
                continue

            minio_client.copy_object(new_bucket, key, CopySource(old_bucket, key))
            achievement.is_public = True
            moved += 1

        if not dry_run:
            db.commit()

    logger.info("Achievement videos migrated: %s", moved)
    return moved


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    migrate(dry_run=args.dry_run)


if __name__ == "__main__":
    main()

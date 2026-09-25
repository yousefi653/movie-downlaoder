import argparse
import json
import logging
import shutil
import tarfile
from datetime import datetime
from pathlib import Path

from bson import json_util
from pymongo import MongoClient, errors

from logger_config import setup_logging
from storage_db import DB_NAME, MONGO_URI

logger = logging.getLogger(__name__)

DEFAULT_BACKUP_DIR = Path("backups")
DEFAULT_COLLECTIONS = ("movies", "series")
METADATA_FILE = "metadata.json"


def get_client():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")
        logger.debug("Connected to MongoDB at %s", MONGO_URI)
        return client
    except errors.ConnectionFailure as exc:
        logger.error("MongoDB connection failed: %s", exc)
        raise


def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def backup_collections(
    client,
    collections,
    output_dir,
    fmt="json",
    compress=False,
    batch_size=1000,
):
    db = client[DB_NAME]
    timestamp = get_timestamp()
    backup_name = f"{DB_NAME}_{timestamp}"
    backup_path = Path(output_dir) / backup_name
    backup_path.mkdir(parents=True, exist_ok=True)

    metadata = {
        "database": DB_NAME,
        "timestamp": timestamp,
        "format": fmt,
        "collections": {},
        "mongodb_version": None,
        "total_documents": 0,
    }

    try:
        server_info = client.server_info()
        metadata["mongodb_version"] = server_info.get("version")
    except Exception:
        pass

    for coll_name in collections:
        logger.info("Backing up collection: %s", coll_name)
        coll = db[coll_name]
        count = 0
        coll_file = backup_path / f"{coll_name}.{fmt}"

        if fmt == "json":
            with open(coll_file, "w", encoding="utf-8") as f:
                f.write("[\n")
                first = True
                cursor = coll.find({}, batch_size=batch_size)
                for doc in cursor:
                    if not first:
                        f.write(",\n")
                    f.write(json_util.dumps(doc, ensure_ascii=False))
                    first = False
                    count += 1
                f.write("\n]")
        elif fmt == "bson":
            with open(coll_file, "wb") as f:
                cursor = coll.find({}, batch_size=batch_size)
                for doc in cursor:
                    f.write(json_util.dumps(doc).encode("utf-8") + b"\n")
                    count += 1
        else:
            raise ValueError(f"Unknown format: {fmt}")

        metadata["collections"][coll_name] = {
            "document_count": count,
            "file": f"{coll_name}.{fmt}",
        }
        metadata["total_documents"] += count
        logger.info("  %s: %d documents", coll_name, count)

    meta_file = backup_path / METADATA_FILE
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    archive_path = None
    if compress:
        archive_path = Path(output_dir) / f"{backup_name}.tar.gz"
        logger.info("Compressing backup to %s", archive_path)
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(backup_path, arcname=backup_name)
        shutil.rmtree(backup_path)
        logger.info("Backup compressed, removed uncompressed directory")

    logger.info(
        "Backup completed: %s (%d total documents)",
        backup_name,
        metadata["total_documents"],
    )
    return backup_path if not compress else archive_path


def restore_collections(client, backup_dir, collections=None, drop_first=False):
    """Restore collections from a backup directory."""
    backup_path = Path(backup_dir)
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup directory not found: {backup_path}")

    meta_file = backup_path / METADATA_FILE
    if not meta_file.exists():
        raise FileNotFoundError(f"Metadata file not found in {backup_path}")

    with open(meta_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    if metadata.get("database") != DB_NAME:
        logger.warning(
            "Backup database (%s) differs from target (%s)",
            metadata.get("database"),
            DB_NAME,
        )

    fmt = metadata.get("format", "json")
    db = client[DB_NAME]

    colls_to_restore = collections or list(metadata.get("collections", {}).keys())
    for coll_name in colls_to_restore:
        coll_info = metadata["collections"].get(coll_name)
        if not coll_info:
            logger.warning(
                "Collection %s not found in backup metadata, skipping", coll_name
            )
            continue

        coll_file = backup_path / coll_info["file"]
        if not coll_file.exists():
            logger.error("Backup file not found: %s", coll_file)
            continue

        coll = db[coll_name]
        if drop_first:
            logger.info("Dropping collection %s before restore", coll_name)
            coll.drop()
            coll.create_index([("imdb_code", 1), ("type", 1)], unique=True)

        logger.info("Restoring collection: %s from %s", coll_name, coll_file)
        count = 0
        if fmt == "json":
            with open(coll_file, "r", encoding="utf-8") as f:
                data = json_util.loads(f.read())
            if data:
                coll.insert_many(data, ordered=False)
                count = len(data)
        elif fmt == "bson":
            with open(coll_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    doc = json_util.loads(line)
                    coll.insert_one(doc)
                    count += 1
        else:
            raise ValueError(f"Unknown format: {fmt}")

        logger.info("  %s: restored %d documents", coll_name, count)

    logger.info("Restore completed")


def list_backups(backup_dir):
    backup_path = Path(backup_dir)
    if not backup_path.exists():
        logger.info("No backup directory found at %s", backup_dir)
        return []

    backups = []
    for item in sorted(backup_path.iterdir()):
        if item.is_dir():
            meta_file = item / METADATA_FILE
            if meta_file.exists():
                with open(meta_file) as f:
                    meta = json.load(f)
                backups.append(
                    {
                        "name": item.name,
                        "path": str(item),
                        "timestamp": meta.get("timestamp"),
                        "total_documents": meta.get("total_documents"),
                        "format": meta.get("format"),
                        "collections": list(meta.get("collections", {}).keys()),
                    }
                )
        elif item.suffix == ".gz" and item.name.endswith(".tar.gz"):
            backups.append(
                {
                    "name": item.name.replace(".tar.gz", ""),
                    "path": str(item),
                    "compressed": True,
                }
            )
    return backups


def clean_backups(backup_dir, keep=5):
    backups = list_backups(backup_dir)
    if len(backups) <= keep:
        logger.info(
            "Only %d backups found, nothing to clean (keep=%d)", len(backups), keep
        )
        return

    to_delete = backups[:-keep]
    logger.info("Cleaning %d old backups (keeping %d)", len(to_delete), keep)
    for b in to_delete:
        p = Path(b["path"])
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        logger.info("  Deleted: %s", p.name)


def extract_if_compressed(backup_arg):
    p = Path(backup_arg)
    if p.suffix == ".gz" and p.name.endswith(".tar.gz"):
        extract_dir = p.parent / p.name.replace(".tar.gz", "")
        logger.info("Extracting compressed backup %s to %s", p, extract_dir)
        with tarfile.open(p, "r:gz") as tar:
            tar.extractall(p.parent)
        return extract_dir
    return p


def cmd_backup(args):
    client = get_client()
    try:
        backup_collections(
            client,
            collections=args.collections,
            output_dir=args.output_dir,
            fmt=args.format,
            compress=args.compress,
        )
    finally:
        client.close()


def cmd_restore(args):
    backup_path = extract_if_compressed(args.backup_dir)
    client = get_client()
    try:
        restore_collections(
            client,
            backup_path,
            collections=args.collections,
            drop_first=args.drop,
        )
    finally:
        client.close()


def cmd_list(args):
    backups = list_backups(args.output_dir)
    if not backups:
        print("No backups found.")
        return
    print(f"{'Name':<40} {'Timestamp':<20} {'Format':<6} {'Docs':>8} Collections")
    print("-" * 100)
    for b in backups:
        ts = b.get("timestamp", "?")
        fmt = b.get("format", "?")
        docs = b.get("total_documents", 0)
        colls = ", ".join(b.get("collections", []))
        comp = " (compressed)" if b.get("compressed") else ""
        print(f"{b['name']:<40} {ts:<20} {fmt:<6} {docs:>8} {colls}{comp}")


def cmd_clean(args):
    clean_backups(args.output_dir, keep=args.keep)


def main():
    parser = argparse.ArgumentParser(
        description="MongoDB backup/restore for movie_db",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # backup
    p_backup = subparsers.add_parser("backup", help="Create a new backup")
    p_backup.add_argument(
        "--format", choices=["json", "bson"], default="json", help="Backup format"
    )
    p_backup.add_argument(
        "--output-dir",
        default=DEFAULT_BACKUP_DIR,
        help="Directory to store backups",
    )
    p_backup.add_argument(
        "--collections",
        nargs="+",
        default=DEFAULT_COLLECTIONS,
        help="Collections to backup",
    )
    p_backup.add_argument(
        "--compress",
        action="store_true",
        help="Compress backup to .tar.gz",
    )
    p_backup.add_argument(
        "-q", "--quiet", action="store_true", help="Minimal output (for cron)"
    )
    p_backup.set_defaults(func=cmd_backup)

    # restore
    p_restore = subparsers.add_parser("restore", help="Restore from backup")
    p_restore.add_argument("backup_dir", help="Backup directory or .tar.gz file")
    p_restore.add_argument(
        "--collections",
        nargs="+",
        default=None,
        help="Collections to restore (default: all)",
    )
    p_restore.add_argument(
        "--drop",
        action="store_true",
        help="Drop collections before restore",
    )
    p_restore.set_defaults(func=cmd_restore)

    # list
    p_list = subparsers.add_parser("list", help="List available backups")
    p_list.add_argument(
        "--output-dir", default=DEFAULT_BACKUP_DIR, help="Backup directory"
    )
    p_list.set_defaults(func=cmd_list)

    # clean
    p_clean = subparsers.add_parser("clean", help="Remove old backups")
    p_clean.add_argument(
        "--output-dir", default=DEFAULT_BACKUP_DIR, help="Backup directory"
    )
    p_clean.add_argument(
        "--keep", type=int, default=5, help="Number of recent backups to keep"
    )
    p_clean.set_defaults(func=cmd_clean)

    args = parser.parse_args()

    args.func(args)


if __name__ == "__main__":
    setup_logging()
    main()

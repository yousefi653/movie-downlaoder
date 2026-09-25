import logging
import re

from pymongo import MongoClient, UpdateOne, errors

logger = logging.getLogger(__name__)

MONGO_URI = "mongodb://127.0.0.1:27017"
DB_NAME = "movie_db"


def db_connection():
    try:
        logger.debug("Connecting to MongoDB uri=%s", MONGO_URI)
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
    except errors.ConnectionFailure as exc:
        logger.error("MongoDB ping failed (connection failure): %s", exc)
        return None
    except Exception as exc:
        logger.error("Unexpected MongoDB connection error: %r", exc)
        return None
    else:
        logger.debug("MongoDB connection established (db=%s)", DB_NAME)
        return client[DB_NAME]


def insert_movies_data(data, count):
    if not data:
        logger.warning("insert_movies_data called with empty data; nothing to do")
        return
    db = db_connection()
    if db is None:
        logger.error("Cannot insert %d movies: no DB connection", len(data))
        return
    movie_col = db["movies"]
    movie_col.create_index([("imdb_code", 1), ("type", 1)], unique=True)
    update_list = []

    logger.info("Inserting/upserting %d movies ...", len(data))
    for item in data:
        try:
            imdb_code = item["imdb_code"]
        except KeyError:
            logger.warning("Skipping movie record without imdb_code: %r", item)
            continue
        update_list.append(
            UpdateOne(
                {"imdb_code": imdb_code},
                {
                    "$set": {
                        "name": item.get("name"),
                        "type": item.get("type"),
                        "SoftSub": item.get("SoftSub"),
                        "Dubbed": item.get("Dubbed"),
                        "NoSub": item.get("NoSub"),
                    }
                },
                upsert=True,
            )
        )
    if not update_list:
        logger.warning("No valid movie records to write after validation")
        return
    try:
        result = movie_col.bulk_write(update_list, ordered=False)
        logger.info(
            "Movies bulk_write done: matched=%d modified=%d upserted=%d",
            result.matched_count,
            result.modified_count,
            len(result.upserted_ids or {}),
        )
    except Exception as exc:
        logger.error("Movies bulk_write failed for %d records: %r", len(update_list), exc)
        return

    try:
        total = movie_col.count_documents({})
        logger.debug("Movies collection now holds %d documents", total)
    except Exception as exc:
        logger.warning("Could not count movies collection: %s", exc)


def insert_series_data(data):
    if not data:
        logger.warning("insert_series_data called with empty data; nothing to do")
        return
    db = db_connection()
    if db is None:
        logger.error("Cannot insert %d series: no DB connection", len(data))
        return
    serie_col = db["series"]
    serie_col.create_index([("imdb_code", 1), ("type", 1)], unique=True)
    update_list = []

    logger.info("Inserting/upserting %d series ...", len(data))
    for item in data:
        try:
            imdb_code = item["imdb_code"]
        except KeyError:
            logger.warning("Skipping serie record without imdb_code: %r", item)
            continue
        update_list.append(
            UpdateOne(
                {"imdb_code": imdb_code},
                {
                    "$set": {
                        "name": item.get("name"),
                        "type": item.get("type"),
                        "SoftSub": item.get("SoftSub"),
                        "NoSub": item.get("NoSub"),
                        "Dubbed": item.get("Dubbed"),
                    }
                },
                upsert=True,
            )
        )
    if not update_list:
        logger.warning("No valid serie records to write after validation")
        return
    try:
        result = serie_col.bulk_write(update_list, ordered=False)
        logger.info(
            "Series bulk_write done: matched=%d modified=%d upserted=%d",
            result.matched_count,
            result.modified_count,
            len(result.upserted_ids or {}),
        )
    except Exception as exc:
        logger.error("Series bulk_write failed for %d records: %r", len(update_list), exc)


def is_item_in_db(imdb_or_name):
    """Return True if a serie with this imdb_code (tt...) or name exists.

    Always returns a real bool (old code implicitly returned None).
    """
    db = db_connection()
    if db is None:
        logger.warning(
            "is_item_in_db(%r): no DB connection, assuming absent", imdb_or_name
        )
        return False
    col = db["series"]
    try:
        if str(imdb_or_name).startswith("tt"):
            found = col.find_one({"imdb_code": imdb_or_name}, {"_id": 1}) is not None
        else:
            found = col.find_one({"name": imdb_or_name}, {"_id": 1}) is not None
    except Exception as exc:
        logger.warning("is_item_in_db(%r) query failed: %s", imdb_or_name, exc)
        return False
    logger.debug("is_item_in_db(%r) -> %s", imdb_or_name, found)
    return found


def find_movie_or_serie(name, type_name):
    """Search movies/series by name words. Logs query and hit count."""
    if type_name not in ("s", "m"):
        logger.warning("find_movie_or_serie called with invalid type=%r", type_name)
        return []
    db = db_connection()
    if db is None:
        logger.error(
            "Search failed for query=%r type=%s: no DB connection", name, type_name
        )
        return []
    col = db["series"] if type_name == "s" else db["movies"]

    # Escape user words so regex metacharacters can't break/redirect the query.
    words = [re.escape(w) for w in str(name).split() if w]
    if not words:
        logger.warning("Empty search query (type=%s); returning []", type_name)
        return []
    pattern = ".*".join(f".*{w}.*" for w in words).replace(".*.*", ".*")
    logger.info(
        "Searching %s for query=%r (%d hits expected at most: pattern logged at debug)",
        "series" if type_name == "s" else "movies",
        name,
        len(words),
    )
    logger.debug("Search regex pattern: %s", pattern)
    try:
        data = list(
            col.find(
                {"name": {"$regex": pattern, "$options": "i"}},
                {"name": 1, "_id": 0, "SoftSub": 1, "NoSub": 1, "Dubbed": 1},
            )
        )
    except Exception as exc:
        logger.error("Search query failed for query=%r type=%s: %r", name, type_name, exc)
        return []
    logger.info(
        "Search done: query=%r type=%s -> %d result(s)",
        name,
        type_name,
        len(data),
    )
    return data

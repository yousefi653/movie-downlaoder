from pymongo import MongoClient, errors, UpdateOne
import datetime


def get_time():
    now = datetime.datetime.now().time()
    return datetime.time.strftime(now, "%H:%M:%S")


def db_connection():
    try:
        print(f"[ {get_time()} ] Connect to the db")
        client = MongoClient("mongodb://127.0.0.1:27017")
        client.admin.command("ping")
    except errors.ConnectionFailure:
        print(f"[ {get_time()} ] Timeoute")
        return None
    else:
        db = client["movie_db"]
        return db


def insert_movies_data(data, count):
    db = db_connection()
    movie_col = db["movies"]
    movie_col.create_index([("imdb_code", 1), ("type", 1)], unique=True)
    update_list = []

    print(f"[ {get_time()} ] Start inserting movies data ....")
    for item in data:
        update_list.append(
            UpdateOne(
                {"imdb_code": item["imdb_code"]},
                {
                    "$set": {
                        "name": item["name"],
                        "type": item["type"],
                        "SoftSub": item["SoftSub"],
                        "Dubbed": item["Dubbed"],
                        "NoSub": item["NoSub"],
                    }
                },
                upsert=True,
            )
        )
    movie_col.bulk_write(update_list, ordered=False)
    if movie_col.count_documents({}) != count:
        print(f"[ {get_time()} ] Inserting data failed :(")
    print(f"[ {get_time()} ] movies data inserted")


def insert_series_data(data):
    db = db_connection()
    serie_col = db["series"]
    serie_col.create_index([("imdb_code", 1), ("type", 1)], unique=True)
    update_list = []

    print(f"[ {get_time()} ] Start inserting series data ....")
    for item in data:
        update_list.append(
            UpdateOne(
                {"imdb_code": item["imdb_code"]},
                {
                    "$set": {
                        "name": item["name"],
                        "type": item["type"],
                        "SoftSub": item["SoftSub"],
                        "NoSub": item["NoSub"],
                        "Dubbed": item["Dubbed"],
                    }
                },
                upsert=True,
            )
        )
    serie_col.bulk_write(update_list, ordered=False)
    print(f"[ {get_time()} ] series data inserted")


def is_item_in_db(name):
    db = db_connection()
    col = db["series"]
    if not name.startswith("tt"):
        result = col.find({"name": name})
    else:
        result = col.find({"imdb_code": name})
    if list(result):
        return True


def find_movie_or_serie(name, type_name):
    db = db_connection()
    if type_name == "s":
        col = db["series"]
    else:
        col = db["movies"]

    tmp = ""
    for item in name.split():
        tmp += f".*{item}.*"
    tmp = tmp.replace(".*.*", ".*")
    data = list(
        col.find(
            {"name": {"$regex": tmp, "$options": "i"}},
            {"name": 1, "_id": 0, "SoftSub": 1, "NoSub": 1, "Dubbed": 1},
        )
    )
    return data

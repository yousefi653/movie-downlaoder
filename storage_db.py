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

def insert_movies_data(data):
    db = db_connection()
    movie_col = db["movies"]
    movie_col.create_index("imdb_code", unique=True)
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
    movie_col.bulk_write(update_list)
    print(f"[ {get_time()} ] movies data inserted")

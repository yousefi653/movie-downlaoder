import requests
from bs4 import BeautifulSoup
import pickle
import datetime
import re
import os
import json
from storage_db import insert_movies_data

MOVIE_NAME_PATT = re.compile(r"(?P<movie_name>^\d.*\. .*\n)")
TITLE_TYPE_PATT = re.compile(r"(?P<title_type>^Title Type:.*\n)")
IMDB_CODE_PATT = re.compile(r"(?P<imdb_code>^IMDb Code:.*\n)")
URL = "https://dls2.iran-gamecenter-host.com/DonyayeSerial/donyaye_serial_all_archive.html"


def get_time():
    now = datetime.datetime.now().time()
    return datetime.time.strftime(now, "%H:%M:%S")

def get_request():
    response = requests.get(URL)
    return response

def creation_soup():
    print(f"[ {get_time()} ] Starting program")
    print(f"[ {get_time()} ] Get request to the site")
    response = get_request()
    if response.status_code == 200:
        print(f"[ {get_time()} ] Response was successfuly received")
    print(f"[ {get_time()} ] Parsing response ......")
    soup = BeautifulSoup(response.text, "html.parser")
    return soup

def writing_html_code_in_file():
    soup = creation_soup()
    with open("html_code_with_a.txt", "w", encoding="UTF-8") as file:
        print(f"[ {get_time()} ] Writing the html code in file")
        file.write(str(soup.prettify()))
    with open("html_code.txt", "w", encoding="UTF-8") as file:
        file.write(str(soup.text))
    today = datetime.date.today()
    pickl_file = open("info", "wb")
    pickle.dump({"last_modified": today}, file=pickl_file)
    pickl_file.close()

def link_gen(soup):
    bad_links = [
        "http://dls6.iran-gamecenter-host.com/DonyayeSerial/10_thous.html",
        "https://daramet.com/donyayeserial",
    ]
    for a in soup.find_all("a"):
        if any(a.get("href") == item for item in bad_links):
            continue
        yield a

def movie_gen(movies):
    for movie in movies:
        yield movie.values()

def movies_links(movies):
    print(f"[ {get_time()} ] Getting movies info")

    file_a_tags = open("html_code_with_a.txt", "r", encoding="UTF-8")
    soup = BeautifulSoup(file_a_tags.read(), "html.parser")
    links = link_gen(soup)
    data = []
    movie = {
        "SoftSub": [],
        "Dubbed": [],
        "NoSub": [],
    }

    movies_lenght = len(movies)
    names = movie_gen(movies)
    name, imdb_code, title_type = next(names)

    counter = 1
    for link in links:
        href = link.get("href")

        if re.match(r".*/series.*/.*", href):
            print(f"[ {get_time()} ] This is Series then pass")
            continue

        if not (imdb_code in href) or movies_lenght == counter:
            try:
                print(f"[ {get_time()} ] {name} movie append")
                counter += 1
                data.append(
                    {
                        "name": name,
                        "type": title_type,
                        "imdb_code": imdb_code,
                        "SoftSub": movie["SoftSub"],
                        "Dubbed": movie["Dubbed"],
                        "NoSub": movie["NoSub"],
                    }
                )
                name, imdb_code, title_type = next(names)
                movie = {
                    "SoftSub": [],
                    "Dubbed": [],
                    "NoSub": [],
                }
            except StopIteration:
                print(f"[ {get_time()} ] We have data from all movie in site ;)")
                print(f"[ {get_time()} ] Now we will have {counter-1} movie in DB")
                break

        if any(item in href for item in ["SoftSub", "Soft.Sub", "Softub"]):
            movie["SoftSub"].append(
                {"title": link.text.replace("\n", "").strip(), "link": href}
            )
        elif "Dubbed" in href:
            movie["Dubbed"].append(
                {"title": link.text.replace("\n", "").strip(), "link": href}
            )
        elif "NoSub" in href:
            movie["NoSub"].append(
                {"title": link.text.replace("\n", "").strip(), "link": href}
            )

    # with open("data.json", "w") as file:
    #     json.dump(data, file, indent=3)
    # insert_movies_data(data)
    insert_movies_data(data=data, count=counter-1)

def movies_info():
    movies = []
    movie = {}
    with open("html_code.txt", "r", encoding="UTF-8") as file:
        for line in file:
            name = re.match(MOVIE_NAME_PATT, line)
            imdb_code = re.match(IMDB_CODE_PATT, line)
            title_type = re.match(TITLE_TYPE_PATT, line)

            if name:
                name = name.group().split()[1:]
                name = ".".join(name)
                movie["name"] = name

            if imdb_code:
                movie["imdb_code"] = (
                    imdb_code.group().split()[2].replace("\n", "").strip()
                )

            if title_type:
                if "series" in title_type.group().lower():
                    movie = {}
                    continue
                movie["type"] = title_type.group().split()[2].replace("\n", "").strip()
                movies.append(movie)
                movie = {}
    movies_links(movies=movies)


# main program

if not "info" in os.listdir():
    writing_html_code_in_file()

file = open("info", "rb")
today = datetime.date.today()
last_modified = pickle.load(file)["last_modified"]
file.close()
if (today - last_modified).days > 1:
    writing_html_code_in_file()

movies_info()

import requests
from bs4 import BeautifulSoup
# from scrapper.utils import get_usr_agnts
import pickle
import datetime
import re
import os
import json
import simple_header
import random
import time
import difflib
import urllib3
from storage_db import insert_movies_data, insert_series_data, is_item_in_db

urllib3.disable_warnings()

# --- Patterns ---
NAME_PATT = re.compile(r"(?P<movie_name>^\d.*\. .*\n)")
TITLE_TYPE_PATT = re.compile(r"(?P<title_type>^Title Type:.*\n)")
IMDB_CODE_PATT = re.compile(r"(?P<imdb_code>^IMDb Code:.*\n)")

# --- Request URL ---
# URL = "https://dls2.iran-gamecenter-host.com/DonyayeSerial/donyaye_serial_all_archive.html"
URL = "https://dls2.iran-onemovies-dcenter.com/DonyayeSerial/donyaye_serial_all_archive.html"
USER_AGENTS = simple_header.sua.get_list(shuffle=True, force_cached=True)
USER_AGENTS2 = USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.112 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.185 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.217 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.60 Safari/537.36",

    # Chrome macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36",

    # Chrome Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36",
    "Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36",

    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",

    # Firefox macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13.6; rv:125.0) Gecko/20100101 Firefox/125.0",

    # Firefox Linux
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",

    # Safari macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",

    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36 Edg/124.0.2478.97",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36 Edg/123.0.2420.97",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.112 Safari/537.36 Edg/122.0.2365.92",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36 Edg/124.0.2478.97",

    # Edge macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36 Edg/124.0.2478.97",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36 Edg/124.0.2478.97",

    # Opera
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36 OPR/109.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36 OPR/108.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36 OPR/109.0.0.0",

    # Chrome Android
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; OnePlus 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Xiaomi 13 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",

    # Safari iOS
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 16_7_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",

    # Firefox Android
    "Mozilla/5.0 (Android 14; Mobile; rv:125.0) Gecko/125.0 Firefox/125.0",
    "Mozilla/5.0 (Android 13; Mobile; rv:124.0) Gecko/124.0 Firefox/124.0",
    "Mozilla/5.0 (Android 14; Tablet; rv:125.0) Gecko/125.0 Firefox/125.0",

    # Samsung Browser
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/24.0 Chrome/117.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/24.0 Chrome/117.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.36",

    # Brave (همون Chrome engine)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36 Brave/1.65",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36 Brave/1.65",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36 Brave/1.65",
]

def get_time():
    now = datetime.datetime.now().time()
    return datetime.time.strftime(now, "%H:%M:%S")

def similarity(name, name_in_link, imdb_code):
    if name_in_link.startswith("tt"):
        return difflib.SequenceMatcher(None, imdb_code, name_in_link).ratio()
    else:
        return difflib.SequenceMatcher(None, name.lower(), name_in_link.lower()).ratio()

def get_request(url=URL):
    # ua = simple_header.sua.get_list(force_cached=True)[0]
    # headers = simple_header.get_dict(url=url, user_agent=random.choice(USER_AGENTS))
    try:
        headers = simple_header.get_dict(url=url, user_agent=random.choice(USER_AGENTS2))
    except:
        headers = simple_header.get_dict(url=url, user_agent=random.choice(USER_AGENTS))

    try:
        # time.sleep(random.randint(3, 10))
        if "dls8" not in url:
            response = requests.get(url=url, headers=headers, timeout=45, allow_redirects=True, verify=False)
        else:
            response = requests.get(url=url)
    except requests.ConnectionError as Error:
        print(f"[ {get_time()} ] Error: {str(Error)}")
        return None
    except requests.Timeout as Error:
        print(f"[ {get_time()} ] Error: {str(Error)}")
        return None
    except OSError as Error:
        print(f"[ {get_time()} ] Error: {str(Error)}")
        return None
    except Exception as Error:
        print(f"[ {get_time()} ] Error: {str(Error)}")
        return None

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
        "http://dls6.iran-onemovies-dcenter.com/DonyayeSerial/10_thous.html",
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

def series_links(series):
    remains_data = open("remains_data.json", "a+")
    if not "parsed_links.txt" in os.listdir():
        with open("parsed_links.txt", "w"):
            pass
    parsed_links_file = open("parsed_links.txt", "a+", encoding="UTF-8")
    print(f"[ {get_time()} ] Getting series info")

    file_a_tags = open("html_code_with_a.txt", "r", encoding="UTF-8")
    soup = BeautifulSoup(file_a_tags.read(), "html.parser")
    links = link_gen(soup)
    data = []

    names = movie_gen(series)
    name, imdb_code, title_type = next(names)
    seasons_link = {}
    counter = 1
    movie_type = None
    
    parsed_links_file.seek(0)
    parsed_links = parsed_links_file.readlines()
    serie_link_parsed = []
    serie_pass_flag = False
    for link in links:
        href = link.get("href")
        name_in_link = href.split("/")[5]

        if not re.match(r".*/series.*/.*", href):
            print(f"[ {get_time()} ] This is Movie then pass")
            continue
        if any(item in href for item in ["SoftSub", "Soft.Sub", "Softub"]):
            movie_type = "SoftSub"
        elif "NoSub" in href or ("Sub" not in href and "Dubbed" not in href):
            movie_type = "NoSub"
        else:
            print(href, name_in_link)
            for item in data:
                if name_in_link == item["imdb_code"] or name_in_link == item["name"]:
                    print("omad in to")
                    if ("SoftSub" in item) or ("NoSub" in item):
                        continue
            if is_item_in_db(name_in_link):
                print("omad in to 2")
                continue
            movie_type = "Dubbed"

        if not re.match(r".*/720p.*", href) and not re.match(r".*/480p.*", href) and not re.match(r".*/1080p.*", href):
            continue

        sm = similarity(name, name_in_link, imdb_code)
        is_current_serie = (imdb_code.lower() in href.lower())  or (sm >= 0.7) #or (name.lower() in href.lower())

        if not is_current_serie:
            try:
                if not serie_pass_flag:
                    if "SoftSub" in seasons_link:
                        print(f"[ {get_time()} ] seasons(SoftSub) is {", ".join(list(seasons_link["SoftSub"].keys()))}")
                    if "NoSub" in seasons_link:
                        print(f"[ {get_time()} ] seasons(NoSub) is {", ".join(list(seasons_link["NoSub"].keys()))}")
                    data.append(
                        {
                            "name": name,
                            "type": title_type,
                            "imdb_code": imdb_code,
                            "SoftSub": seasons_link.get("SoftSub"),
                            "NoSub": seasons_link.get("NoSub"),
                            "Dubbed": seasons_link.get("Dubbed")
                        }
                    )
                    print(f"[ {get_time()} ] {name} serie append")
                    print(f"[ {get_time()} ] Unitl now {counter} series appended")
                    name, imdb_code, title_type = next(names)
                    if len(data) % 10 == 0:
                        insert_series_data(data)
                        for item in serie_link_parsed:
                            parsed_links_file.write(f"{item}\n")
                        serie_link_parsed = []
                        data = []
                    seasons_link = {}
                    counter += 1
                    parsed_links_file.seek(0, 2)
                    print(f"[ {get_time()} ] I'm Going to sleep 15 seconds😴😴")
                    time.sleep(15)
                else:
                    print(f"[ {get_time()} ] **{name.upper()}** parsed before the pass")
                    name, imdb_code, title_type = next(names)
                    serie_pass_flag = False
            except StopIteration:
                print(f"[ {get_time()} ] We have data from all series in site ;)")
                print(f"[ {get_time()} ] Now we will have {counter-1} serie in DB")
                break

        if f"{href}\n" in parsed_links:
            serie_pass_flag = True
            continue
        else:
            # parsed_links_file.seek(0, 2)
            # parsed_links_file.write(f"{href}\n")
            serie_link_parsed.append(href)

        ep_counter = 1
        season = re.findall(r"/S\d{1,2}/", href)[0].replace("/", "")
        quality = link.text.replace("\n", "").strip()

        if not season:
            season = "NULL"

        if movie_type not in seasons_link:
            seasons_link[movie_type] = {}

        if season not in seasons_link[movie_type]:
            seasons_link[movie_type][season] = {}

        if any("720" in key for key in seasons_link[movie_type][season].keys()):
            continue
        if any("480" in key for key in seasons_link[movie_type][season].keys()):
            continue
        # if any("1080" in key for key in seasons_link[movie_type][season].keys()):
        #     continue

        print(f"LINK FOR SERIE *** {name} *** WITH IMDB_CODE ### {imdb_code} ### IS => {href}")
        sm = similarity(name, name_in_link, imdb_code)
        if not (sm >= 0.7 or imdb_code in href):
            print("###\n BUG FOUNDED \n####")
            exit(1)
        if quality not in seasons_link[movie_type][season]:
            seasons_link[movie_type][season][quality] = {}

        count = 0
        while(count <= 5):
            print(f"[ {get_time()} ] Attempt {count+1} for {season}")
            response = get_request(url=href)
            print(f"[ {get_time()} ] Response code is: {response}")
            if not response:
                print(f"[ {get_time()} ] Url is {href}")
                print(f"[ {get_time()} ] Failed, count before: {count}")
                count += 1
                print(f"[ {get_time()} ] count after: {count}")
                time.sleep(10)
                continue
            break
        if not response:
            json.dump({"name": name, "imdb_code": imdb_code, "season": season, "quality": quality, "link": href}, remains_data)
            continue
        print(f"[ {get_time()} ] Response received successfuly from site for {season} of {name}")

        season_soup = BeautifulSoup(response.text, "html.parser")
        for item in season_soup.find_all("td", attrs={"class": "n"})[1:]:
            episode_link = item.find("a").text.replace("\n", "").strip()
            # if name in episode_link:
            episode = re.findall(r"E\d{1,2}", episode_link)
            if episode:
                episode = episode[0]
                seasons_link[movie_type][season][quality][episode] = {"link": f"{href}/{episode_link}", "size": season_soup.find_all("td", attrs={"class": "s"})[ep_counter].text.replace("\n", "")}
                ep_counter += 1
    with open("moviesssss.pkl", "wb") as file:
        pickle.dump(data, file)
    insert_series_data(data=data)

def movies_info():
    movies = []
    movie = {}
    with open("html_code.txt", "r", encoding="UTF-8") as file:
        for line in file:
            name = re.match(NAME_PATT, line)
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
                if any(item in title_type.group() for item in ["tvSeries", "tvMiniSeries"]):
                    movie = {}
                    continue
                movie["type"] = title_type.group().split()[2].replace("\n", "").strip()
                movies.append(movie)
                movie = {}
    movies_links(movies=movies)

def series_info():
    series = []
    serie = {}
    with open("html_code.txt", "r", encoding="UTF-8") as file:
        for line in file:
            name = re.match(NAME_PATT, line)
            imdb_code = re.match(IMDB_CODE_PATT, line)
            title_type = re.match(TITLE_TYPE_PATT, line)

            if name:
                name = name.group().split()[1:]
                name = ".".join(name).replace("..", ".").replace(":", "").replace("-", ".").replace("'", "")
                serie["name"] = name

            if imdb_code:
                serie["imdb_code"] = (
                    imdb_code.group().split()[2].replace("\n", "").strip()
                )

            if title_type:
                if any(item in title_type.group() for item in ["tvSeries", "tvMiniSeries"]):
                    serie["type"] = title_type.group().split()[2].replace("\n", "").strip()
                    series.append(serie)
                serie = {}
                continue
    series_links(series=series)

# main program

if not "info" in os.listdir():
    writing_html_code_in_file()

file = open("info", "rb")
today = datetime.date.today()
last_modified = pickle.load(file)["last_modified"]
file.close()
if (today - last_modified).days > 1:
    writing_html_code_in_file()

print(f"\n#### MOVIE STEP START ####\n")
movies_info()
print(f"\n#### MOVIE STEP END ####\n")
print(f"\n#### SERIE STEP START ####\n")
series_info()
print(f"\n#### SERIE STEP END ####\n")
print(f"[ {get_time()} ] Done :)")

import datetime
import difflib
import json
import logging
import os
import pickle
import random
import re
import time

import requests
import simple_header
import urllib3
from bs4 import BeautifulSoup

from logger_config import setup_logging
from storage_db import insert_movies_data, insert_series_data, is_item_in_db

setup_logging()
logger = logging.getLogger(__name__)

urllib3.disable_warnings()

# --- Patterns ---
NAME_PATT = re.compile(r"(?P<movie_name>^\d.*\. .*\n)")
TITLE_TYPE_PATT = re.compile(r"(?P<title_type>^Title Type:.*\n)")
IMDB_CODE_PATT = re.compile(r"(?P<imdb_code>^IMDb Code:.*\n)")

# --- Request URL ---
URL = (
    "https://dls2.aparatchi-dlcenter.top/DonyayeSerial/donyaye_serial_all_archive.html"
)

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
    # Brave (Chrome engine)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36 Brave/1.65",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36 Brave/1.65",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.202 Safari/537.36 Brave/1.65",
]


def similarity(name, name_in_link, imdb_code):
    if name_in_link.startswith("tt"):
        return 0
    else:
        if name.startswith("The."):
            name = name.replace("The.", "")
        if name_in_link.startswith("The."):
            name_in_link = name_in_link.replace("The.", "")

        return difflib.SequenceMatcher(None, name.lower(), name_in_link.lower()).ratio()


def get_request(url=URL):
    # ua = simple_header.sua.get_list(force_cached=True)[0]
    # headers = simple_header.get_dict(url=url, user_agent=random.choice(USER_AGENTS))
    try:
        headers = simple_header.get_dict(
            url=url, user_agent=random.choice(USER_AGENTS2)
        )
    except:
        headers = simple_header.get_dict(url=url, user_agent=random.choice(USER_AGENTS))

    try:
        # time.sleep(random.randint(3, 10))
        if "dls8" not in url:
            response = requests.get(
                url=url, headers=headers, timeout=45, allow_redirects=True, verify=False
            )
        else:
            response = requests.get(url=url, timeout=45, verify=False)
    except requests.ConnectionError as exc:
        logger.warning("Connection error for url=%s: %s", url, exc)
        return None
    except requests.Timeout as exc:
        logger.warning("Timeout after 45s for url=%s: %s", url, exc)
        return None
    except OSError as exc:
        logger.warning("OS/network error for url=%s: %s", url, exc)
        return None
    except Exception as exc:
        logger.warning("Unexpected request error for url=%s: %r", url, exc)
        return None

    try:
        if response.status_code != 200:
            logger.warning(
                "Bad HTTP status=%s for url=%s", response.status_code, url
            )
            return None
    except Exception as exc:
        logger.warning("Could not read status code for url=%s: %r", url, exc)
        return None

    logger.debug("GET %s -> 200 (%s bytes)", url, len(response.content))
    return response


def creation_soup():
    logger.info("Starting archive fetch")
    logger.info("Sending GET request to archive url=%s", URL)
    response = get_request()
    if response is None:
        logger.error("Archive request failed (no response); aborting")
        raise RuntimeError("Archive request failed: no response (see logs/app.log)")
    logger.info("Archive response received (status=200)")
    logger.debug("Parsing archive response ......")
    soup = BeautifulSoup(response.text, "html.parser")
    return soup


def writing_html_code_in_file():
    soup = creation_soup()
    with open("html_code_with_a.txt", "w", encoding="UTF-8") as file:
        logger.info("Writing prettified HTML to html_code_with_a.txt")
        content = str(soup.prettify())
        file.write(content)
    logger.debug("html_code_with_a.txt written (%d chars)", len(content))
    with open("html_code.txt", "w", encoding="UTF-8") as file:
        text = str(soup.text)
        file.write(text)
    logger.debug("html_code.txt written (%d chars)", len(text))
    today = datetime.date.today()
    with open("info", "wb") as pickl_file:
        pickle.dump({"last_modified": today}, file=pickl_file)
    logger.info("Archive cache refreshed (last_modified=%s)", today)


def link_gen(soup):
    bad_links = [
        "http://dls6.aparatchi-dlcenter.top/DonyayeSerial/10_thous.html",
        "https://daramet.com/donyayeserial",
    ]
    for a in soup.find_all("a"):
        if any(a.get("href") == item for item in bad_links):
            continue

        yield a


BAD_HREFS = {
    "http://dls6.aparatchi-dlcenter.top/DonyayeSerial/10_thous.html",
    "https://daramet.com/donyayeserial",
}

VERSION_HEADERS = ("SoftSub", "Dubbed", "NoSub")

SEASON_RE = re.compile(r"/S(\d{1,3})/", re.IGNORECASE)
EPISODE_RE = re.compile(r"E(\d{1,3})", re.IGNORECASE)
FILE_URL_RE = re.compile(
    r"https?://[^\s'\"<>]+?\.(?:mkv|mp4|avi)(?:\?[^\s'\"<>]*)?", re.IGNORECASE
)
EMBEDDED_SEASON_RE = re.compile(
    r"\{\s*['\"]version['\"]\s*:\s*['\"](?P<version>[^'\"]+)['\"]"
    r".*?['\"]quality['\"]\s*:\s*['\"](?P<quality>[^'\"]+)['\"]"
    r".*?['\"]file['\"]\s*:\s*['\"](?P<file>https?://[^'\"]+)['\"]"
    r".*?['\"]size['\"]\s*:\s*['\"](?P<size>[^'\"]+)['\"]",
    re.IGNORECASE | re.DOTALL,
)


def normalize_series_name(raw_title):
    name = ".".join(raw_title.split())
    name = name.replace("..", ".").replace(":", "").replace("-", ".").replace("'", "")
    return name


def normalize_movie_name(raw_title):
    name = ".".join(raw_title.split())
    name = name.replace(".start_year", "")
    return name


def extract_identifier(href):
    try:
        parts = href.split("/")
        idx = parts.index("DonyayeSerial")
        return parts[idx + 2]

    except (ValueError, IndexError):
        try:
            return href.split("/")[5]
        except IndexError:
            return ""


def extract_season(href):
    m = SEASON_RE.search(href or "")
    if not m:
        return None
    num = m.group(1).zfill(2)
    return f"S{num}"


def classify_version(href, header_version=None):
    if header_version in VERSION_HEADERS:
        return header_version
    href = href or ""
    if "SoftSub" in href or "Soft.Sub" in href or "Softub" in href:
        return "SoftSub"
    if "Dubbed" in href:
        return "Dubbed"
    if "NoSub" in href:
        return "NoSub"
    if "Sub" not in href and "Dubbed" not in href:
        return "NoSub"
    return "DVDRip"


def parse_archive_blocks(soup):
    blocks = []
    h3_list = soup.find_all("h3")
    for h3 in h3_list:
        raw = h3.get_text(strip=True)
        m = re.match(r"^\s*(\d+)\.\s*(.+?)\s*$", raw, re.DOTALL)
        if not m:
            continue
        raw_title = m.group(2).strip()
        imdb_code = None
        title_type = None
        links = []
        cur_header = None
        block_text_parts = []
        sib = h3.find_next_sibling()

        while sib is not None and sib.name != "h3":
            try:
                txt = sib.get_text(" ", strip=True)
            except Exception:
                txt = ""

            if txt:
                block_text_parts.append(txt)

            if imdb_code is None and "IMDb Code:" in txt:
                mm = re.search(r"tt\d+", txt)
                if mm:
                    imdb_code = mm.group(0).strip()

            if title_type is None and "Title Type:" in txt:
                t = txt.lower()
                if "series" in t:
                    title_type = "series"
                elif "movie" in t:
                    title_type = "movie"

            if sib.name == "p" and not sib.find("a"):
                s = sib.get_text(strip=True)
                if s in VERSION_HEADERS:
                    cur_header = s

            for a in sib.find_all("a"):
                href = a.get("href")
                if not href or href in BAD_HREFS:
                    continue
                try:
                    quality = a.get_text(" ", strip=True).replace("\n", "").strip()
                except Exception:
                    quality = ""
                if not quality:
                    quality = href.rstrip("/").rsplit("/", 1)[-1].replace(".", " ")
                links.append((href, quality, cur_header))
            sib = sib.find_next_sibling()

        if not imdb_code or not title_type:
            continue
        if title_type == "series":
            name = normalize_series_name(raw_title)
        else:
            name = normalize_movie_name(raw_title)
        block = {
            "name": name,
            "raw_title": raw_title,
            "imdb_code": imdb_code,
            "type": title_type,
            "links": links,
            "block_text": " | ".join(block_text_parts),
        }
        blocks.append(block)
    return blocks


def parse_embedded_file_links(block_text):
    out = []
    for m in EMBEDDED_SEASON_RE.finditer(block_text or ""):
        out.append(
            {
                "version": m.group("version").strip(),
                "quality": m.group("quality").strip(),
                "file": m.group("file").strip(),
                "size": m.group("size").strip(),
            }
        )
    return out


def fetch_season_episodes(season_url, max_retries=5):
    response = None
    count = 0
    while count < max_retries:
        logger.debug("Fetch attempt %d/%d for season_url=%s", count + 1, max_retries, season_url)
        response = get_request(url=season_url)
        if response is not None:
            break
        logger.warning(
            "Season fetch failed (attempt %d/%d) for season_url=%s; retrying in 10s",
            count + 1,
            max_retries,
            season_url,
        )
        count += 1
        time.sleep(10)
    if response is None:
        logger.error(
            "Season fetch gave up after %d attempts for season_url=%s",
            max_retries,
            season_url,
        )
        return None
    try:
        season_soup = BeautifulSoup(response.text, "html.parser")
    except Exception as exc:
        logger.error("HTML parse failed for season_url=%s: %r", season_url, exc)
        return None

    episodes = {}
    rows = season_soup.find_all("tr")
    if rows:
        for row in rows:
            td_n = row.find("td", attrs={"class": "n"})
            td_s = row.find("td", attrs={"class": "s"})
            if not td_n:
                continue
            a_tag = td_n.find("a")
            if not a_tag:
                continue
            a_href = (a_tag.get("href") or "").strip()
            a_text = a_tag.get_text(strip=True).replace("\n", "").strip()
            
            if a_text.lower() in ("parent directory", "..", "../", "parent directory/"):
                continue
            
            if a_href.endswith("/") and not re.search(
                r"\.(mkv|mp4|avi|srt)", a_href, re.I
            ):
                continue
            
            filename = a_href if a_href and not a_href.startswith("?") else a_text
            if not filename or filename in ("/", "../"):
                continue

            if not re.search(r"\.(mkv|mp4|avi)$", filename, re.I):

                if re.search(r"\.(srt|nfo|jpg|jpeg|png|txt|sfv|md5)$", filename, re.I):
                    continue
                if not EPISODE_RE.search(filename):
                    continue
            em = EPISODE_RE.search(filename)
            if not em:
                logger.debug("Skipping file without episode number: %s", filename)
                continue
    
            digits = em.group(1)
            ep_code = f"E{digits.zfill(2) if len(digits) <= 2 else digits}"
            size = td_s.get_text(" ", strip=True).replace("\n", "") if td_s else ""
            if a_href.startswith("http"):
                full_link = a_href
            else:
                rel = a_href if a_href and a_href not in ("../", "/") else filename
                full_link = season_url.rstrip("/") + "/" + rel.lstrip("/")
            if ep_code not in episodes:
                episodes[ep_code] = {"link": full_link, "size": size}
            else:
                logger.debug(
                    "Duplicate episode %s in season_url=%s; keeping first link",
                    ep_code,
                    season_url,
                )
        logger.info(
            "Parsed %d episodes from season_url=%s (rows mode)",
            len(episodes),
            season_url,
        )
        return episodes

    td_ns = season_soup.find_all("td", attrs={"class": "n"})
    td_ss = season_soup.find_all("td", attrs={"class": "s"})
    start = 1 if len(td_ns) > 1 else 0
    for idx in range(start, len(td_ns)):
        try:
            a_tag = td_ns[idx].find("a")
            if not a_tag:
                continue
            a_href = (a_tag.get("href") or "").strip()
            a_text = a_tag.get_text(strip=True)
            if a_text.lower().startswith("parent"):
                continue
            filename = a_href if a_href else a_text
            em = EPISODE_RE.search(filename)
            if not em:
                continue
            digits = em.group(1)
            ep_code = f"E{digits.zfill(2) if len(digits) <= 2 else digits}"
            size = td_ss[idx].get_text(" ", strip=True) if idx < len(td_ss) else ""
            full_link = (
                a_href
                if a_href.startswith("http")
                else season_url.rstrip("/") + "/" + filename.lstrip("/")
            )
            if ep_code not in episodes:
                episodes[ep_code] = {"link": full_link, "size": size}
        except Exception as exc:
            logger.debug("Skipping unparseable directory row idx=%d: %r", idx, exc)
            continue
    if not episodes:
        logger.warning("No episodes parsed from season_url=%s", season_url)
    else:
        logger.info(
            "Parsed %d episodes from season_url=%s (fallback mode)",
            len(episodes),
            season_url,
        )
    return episodes


def load_parsed_set(path="parsed_links.txt"):
    if not os.path.exists(path):
        logger.info("parsed_links file not found; creating empty %s", path)
        open(path, "w", encoding="UTF-8").close()
        return set()
    with open(path, "r", encoding="UTF-8") as f:
        items = {line.strip() for line in f if line.strip()}
    logger.debug("Loaded %d already-parsed links from %s", len(items), path)
    return items


def append_parsed_links(path, links):
    if not links:
        return
    try:
        with open(path, "a", encoding="UTF-8") as f:
            for h in links:
                f.write(f"{h}\n")
        logger.debug("Appended %d parsed links to %s", len(links), path)
    except OSError as exc:
        logger.error("Failed to append %d links to %s: %s", len(links), path, exc)


def log_remain(path, obj):
    try:
        with open(path, "a", encoding="UTF-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        logger.debug("Logged failed item to %s: %s", path, obj)
    except Exception as exc:
        logger.error("Failed to write remain entry to %s (%r): %r", path, obj, exc)


def movie_gen(movies):
    for movie in movies:
        yield movie.values()


def movies_links(movies=None, blocks=None):
    logger.info("Parsing movies (block-based)")
    if blocks is None:
        try:
            with open("html_code_with_a.txt", "r", encoding="UTF-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
        except OSError as exc:
            logger.error("Cannot read html_code_with_a.txt for movies: %s", exc)
            return
        blocks = parse_archive_blocks(soup)
    movie_blocks = [b for b in blocks if b["type"] == "movie"]
    logger.info("Found %d movie blocks", len(movie_blocks))
    data = []
    for b in movie_blocks:
        name = b["name"]
        imdb_code = b["imdb_code"]
        title_type = b["type"]
        movie = {"SoftSub": [], "Dubbed": [], "NoSub": []}
        for href, quality_text, header in b["links"]:
            if re.match(r".*/series.*/.*", href):
                logger.debug(
                    "Skipping series folder inside movie block name=%s imdb=%s href=%s",
                    name,
                    imdb_code,
                    href,
                )
                continue
            title = quality_text
            if "SoftSub" in href or "Soft.Sub" in href or "Softub" in href:
                movie["SoftSub"].append({"title": title, "link": href})
            elif "Dubbed" in href:
                movie["Dubbed"].append({"title": title, "link": href})
            elif "NoSub" in href:
                movie["NoSub"].append({"title": title, "link": href})
            else:
                movie["NoSub"].append({"title": title, "link": href})
        if not b["links"]:
            embedded = parse_embedded_file_links(b.get("block_text", ""))
            if embedded:
                logger.debug(
                    "Movie block name=%s imdb=%s has no <a> links; using %d embedded file(s)",
                    name,
                    imdb_code,
                    len(embedded),
                )
            for emb in embedded:
                ver = emb["version"]
                key = ver if ver in movie else "NoSub"
                movie[key].append({"title": emb["quality"], "link": emb["file"]})
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
    logger.info("Parsed %d movies, inserting ...", len(data))
    if data:
        insert_movies_data(data=data, count=len(data))
    else:
        logger.warning("No movie data parsed; nothing to insert")


def series_links(series=None, blocks=None, fetch_episodes=True, sleep_seconds=5):
    parsed_set = load_parsed_set("parsed_links.txt")
    logger.info("Parsing series (block-based)")
    if blocks is None:
        try:
            with open("html_code_with_a.txt", "r", encoding="UTF-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
        except OSError as exc:
            logger.error("Cannot read html_code_with_a.txt for series: %s", exc)
            return
        blocks = parse_archive_blocks(soup)
    serie_blocks = [b for b in blocks if b["type"] == "series"]
    logger.info("Found %d serie blocks", len(serie_blocks))

    data = []
    newly_parsed = []
    counter = 0
    skipped_cached = 0
    failed_blocks = 0

    for b in serie_blocks:
        name = b["name"]
        imdb_code = b["imdb_code"]
        title_type = b["type"]
        try:
            block_hrefs = [h for h, _, _ in b["links"]]
            if (
                block_hrefs
                and all(h in parsed_set for h in block_hrefs)
                and is_item_in_db(imdb_code)
            ):
                logger.debug(
                    "Skipping cached block name=%s imdb=%s (%d links already parsed)",
                    name,
                    imdb_code,
                    len(block_hrefs),
                )
                skipped_cached += 1
                continue
        except Exception as exc:
            logger.debug(
                "Cache check failed for block name=%s imdb=%s: %r", name, imdb_code, exc
            )
        seasons_link = {}


        grouped = {}
        direct_files = []
        for href, quality_text, header in b["links"]:
            if href in BAD_HREFS:
                continue

            if re.search(r"\.(mkv|mp4|avi)(\?|$)", href, re.I) and not SEASON_RE.search(
                href
            ):
                direct_files.append((href, quality_text, header))
                continue
            if not re.match(r".*/series.*/.*", href):
                continue
            season = extract_season(href)
            if not season:
                log_remain(
                    "remains_data.json",
                    {
                        "name": name,
                        "imdb_code": imdb_code,
                        "reason": "no-season",
                        "link": href,
                    },
                )
                logger.warning(
                    "Skipping link without season: name=%s imdb=%s href=%s",
                    name,
                    imdb_code,
                    href,
                )
                continue
            version = classify_version(href, header)
            if not quality_text:
                quality_text = href.rstrip("/").rsplit("/", 1)[-1]
            key = (version, season, quality_text)
            if key not in grouped:
                grouped[key] = {"quality_text": quality_text, "hrefs": []}
            if href not in grouped[key]["hrefs"]:
                grouped[key]["hrefs"].append(href)

        embedded = parse_embedded_file_links(b.get("block_text", ""))
        for emb in embedded:
            ver = (
                emb["version"]
                if emb["version"] in ("SoftSub", "Dubbed", "NoSub")
                else "Dubbed"
            )
            qual = emb["quality"] or "720p BluRay"
            if ver not in seasons_link:
                seasons_link[ver] = {}
            if "S01" not in seasons_link[ver]:
                seasons_link[ver]["S01"] = {}
            if qual not in seasons_link[ver]["S01"]:
                seasons_link[ver]["S01"][qual] = {}
            seasons_link[ver]["S01"][qual]["E01"] = {
                "link": emb["file"],
                "size": emb["size"],
            }

        for href, quality_text, header in direct_files:
            ver = classify_version(href, header)
            qual = quality_text or href.rsplit("/", 1)[-1]
            if ver not in seasons_link:
                seasons_link[ver] = {}
            if "S01" not in seasons_link[ver]:
                seasons_link[ver]["S01"] = {}
            if qual not in seasons_link[ver]["S01"]:
                seasons_link[ver]["S01"][qual] = {}
            if "E01" not in seasons_link[ver]["S01"][qual]:
                seasons_link[ver]["S01"][qual]["E01"] = {"link": href, "size": ""}
            newly_parsed.append(href)

        for (version, season, quality_text), g in grouped.items():
            hrefs = g["hrefs"]
            if version not in seasons_link:
                seasons_link[version] = {}
            if season not in seasons_link[version]:
                seasons_link[version][season] = {}
            if (
                quality_text in seasons_link[version][season]
                and seasons_link[version][season][quality_text]
            ):
                continue

            episodes = {}
            fetched_href = None
            if not fetch_episodes:
                episodes = {"_folder": {"link": hrefs[0], "size": ""}}
                fetched_href = hrefs[0]
            else:
                for href in hrefs:
                    if href in parsed_set and len(hrefs) > 1:
                        continue
                    logger.info(
                        "Fetching serie name=%s imdb=%s season=%s quality=%s url=%s",
                        name,
                        imdb_code,
                        season,
                        quality_text,
                        href,
                    )
                    eps = fetch_season_episodes(href)
                    if eps is None:
                        log_remain(
                            "remains_data.json",
                            {
                                "name": name,
                                "imdb_code": imdb_code,
                                "season": season,
                                "quality": quality_text,
                                "link": href,
                            },
                        )
                        continue
                    episodes = eps
                    fetched_href = href
                    break
                if not episodes:
                    for href in hrefs:
                        eps = fetch_season_episodes(href)
                        if eps is not None:
                            episodes = eps
                            fetched_href = href
                            break
                if fetched_href is None:
                    failed_blocks += 1
                    logger.warning(
                        "All %d mirror(s) failed: name=%s imdb=%s season=%s quality=%s",
                        len(hrefs),
                        name,
                        imdb_code,
                        season,
                        quality_text,
                    )
                    continue
            seasons_link[version][season][quality_text] = episodes
            if (
                fetched_href
                and fetched_href not in parsed_set
                and fetched_href not in newly_parsed
            ):
                newly_parsed.append(fetched_href)

        for version_key in ("SoftSub", "NoSub", "Dubbed"):
            seasons = seasons_link.get(version_key)
            if seasons:
                logger.debug(
                    "Seasons(%s) for name=%s imdb=%s: %s",
                    version_key,
                    name,
                    imdb_code,
                    ", ".join(sorted(seasons.keys())),
                )
        if not seasons_link:
            failed_blocks += 1
            logger.warning(
                "Block produced zero seasons (all fetches failed?): name=%s imdb=%s links=%d",
                name,
                imdb_code,
                len(b["links"]),
            )
        data.append(
            {
                "name": name,
                "type": title_type,
                "imdb_code": imdb_code,
                "SoftSub": seasons_link.get("SoftSub"),
                "NoSub": seasons_link.get("NoSub"),
                "Dubbed": seasons_link.get("Dubbed"),
            }
        )
        counter += 1
        logger.info("Serie appended: name=%s imdb=%s (%d/%d)", name, imdb_code, counter, len(serie_blocks))
        if len(data) % 5 == 0:
            if data:
                insert_series_data(data)
            append_parsed_links("parsed_links.txt", newly_parsed)
            parsed_set.update(newly_parsed)
            newly_parsed = []
            data = []
            if sleep_seconds:
                logger.info("Batch done; sleeping %ss ...", sleep_seconds)
                time.sleep(sleep_seconds)

    if data:
        with open("moviesssss.pkl", "wb") as f:
            try:
                pickle.dump(data, f)
            except Exception as exc:
                logger.warning("Could not write debug pickle moviesssss.pkl: %s", exc)
        insert_series_data(data)
    if newly_parsed:
        append_parsed_links("parsed_links.txt", newly_parsed)
    logger.info(
        "Series done: processed=%d skipped_cached=%d blocks_with_failures=%d",
        counter,
        skipped_cached,
        failed_blocks,
    )


def movies_info():
    logger.info("Movie step started")
    try:
        with open("html_code_with_a.txt", "r", encoding="UTF-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
    except OSError as exc:
        logger.error("Cannot read html_code_with_a.txt for movies_info: %s", exc)
        return
    blocks = parse_archive_blocks(soup)
    logger.debug("Parsed %d archive blocks for movies", len(blocks))
    movies_links(blocks=blocks)


def series_info(fetch_episodes=True):
    logger.info("Serie step started (fetch_episodes=%s)", fetch_episodes)
    try:
        with open("html_code_with_a.txt", "r", encoding="UTF-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
    except OSError as exc:
        logger.error("Cannot read html_code_with_a.txt for series_info: %s", exc)
        return
    blocks = parse_archive_blocks(soup)
    logger.debug("Parsed %d archive blocks for series", len(blocks))
    series_links(blocks=blocks, fetch_episodes=fetch_episodes)


# main program

if __name__ == "__main__":
    if "info" not in os.listdir():
        logger.info("No cache info found; fetching archive for the first time")
        writing_html_code_in_file()

    try:
        with open("info", "rb") as file:
            last_modified = pickle.load(file)["last_modified"]
    except (OSError, pickle.PickleError, KeyError) as exc:
        logger.warning("Could not read cache info (%s); refetching archive", exc)
        writing_html_code_in_file()
        with open("info", "rb") as file:
            last_modified = pickle.load(file)["last_modified"]
    today = datetime.date.today()
    if (today - last_modified).days > 1:
        logger.info("Archive cache is stale (>1 day); refetching")
        writing_html_code_in_file()

    logger.info("#### MOVIE STEP START ####")
    movies_info()
    logger.info("#### MOVIE STEP END ####")

    logger.info("#### SERIE STEP START ####")
    series_info()
    logger.info("#### SERIE STEP END ####")
    logger.info("Done :)")

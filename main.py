import logging
import os
import subprocess

import requests
from colorama import Fore, Style
from tqdm import tqdm

from logger_config import setup_logging
from storage_db import find_movie_or_serie

setup_logging(quiet=True)
logger = logging.getLogger(__name__)


# function to download file from url
def download_file(url, filename, save_dir="."):
    logger.info("Download requested: url=%s file=%s save_dir=%s", url, filename, save_dir)
    attempt = 0
    while attempt <= 3:
        try:
            download_path = os.path.join(save_dir, filename)
            os.makedirs(save_dir, exist_ok=True)
            downloaded_size = 0
            if os.path.exists(download_path):
                downloaded_size = os.path.getsize(download_path)
                logger.info(
                    "Resuming download: file=%s already=%d bytes (attempt %d)",
                    download_path,
                      downloaded_size,
                    attempt + 1,
                )
                print(
                    Fore.YELLOW,
                    f"{downloaded_size} of {download_path} downloaded",
                    Fore.RESET,
                )

            headers = {}
            if downloaded_size > 0:
                headers["Range"] = f"bytes={downloaded_size}-"

            response = requests.get(url, stream=True, headers=headers, timeout=30)
            logger.debug(
                "GET %s -> status=%s (resume_from=%d)",
                url,
                response.status_code,
                downloaded_size,
            )
            if response.status_code >= 400:
                raise requests.HTTPError(f"HTTP {response.status_code} for {url}")

            if downloaded_size > 0:
                total_size = (
                    int(response.headers.get("content-length", 0)) + downloaded_size
                )
            else:
                total_size = int(response.headers.get("content-length", 0))
            logger.info(
                "Downloading: file=%s total=%d bytes (attempt %d)",
                download_path,
                total_size,
                attempt + 1,
            )

            mode = "ab" if downloaded_size > 0 else "wb"
            block_size = 1024
            with tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                desc=filename,
                initial=downloaded_size,
            ) as progress_bar:
                print(Fore.GREEN)
                with open(download_path, mode) as file:
                    for data in response.iter_content(block_size):
                        file.write(data)
                        progress_bar.update(len(data))
            print(Fore.RESET)
        except requests.exceptions.ConnectionError as exc:
            attempt += 1
            logger.warning(
                "Download connection error (attempt %d/4): url=%s file=%s: %s",
                attempt,
                url,
                filename,
                exc,
            )
            print(Fore.RED, f"Connection error in attempt {attempt}", Fore.RESET)
        except requests.exceptions.ConnectTimeout as exc:
            attempt += 1
            logger.warning(
                "Download connect timeout (attempt %d/4): url=%s file=%s: %s",
                attempt,
                url,
                filename,
                exc,
            )
            print(Fore.RED, f"Connection timeoute in attempt {attempt}", Fore.RESET)
        except requests.exceptions.ChunkedEncodingError as exc:
            attempt += 1
            logger.warning(
                "Download chunk error, retrying (attempt %d/4): url=%s file=%s: %s",
                attempt,
                url,
                filename,
                exc,
            )
        except Exception as exc:
            attempt += 1
            logger.warning(
                "Download error (attempt %d/4): url=%s file=%s: %r",
                attempt,
                url,
                filename,
                exc,
            )
            print(Fore.RED, f"Error: {str(exc)}", Fore.RESET)
        else:
            logger.info("Download finished: file=%s url=%s", download_path, url)
            print(
                Style.BRIGHT,
                Fore.GREEN,
                f"{download_path} downloaded successfully.",
                Style.RESET_ALL,
            )
            return True
    logger.error("Download failed after 4 attempts: url=%s file=%s", url, filename)
    print(Fore.RED, "Download was not successfuly please try later", Fore.RESET)


def watch_stream(url):
    logger.info("Opening stream: url=%s", url)
    command = ["mpv", "--autofit=80%", url]
    try:
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        logger.error("Cannot start stream: mpv executable not found (url=%s)", url)
        print(Fore.RED, "mpv player not found; cannot stream", Fore.RESET)
        return
    except Exception as exc:
        logger.error("Failed to start stream url=%s: %r", url, exc)
        print(Fore.RED, f"Error starting stream: {exc}", Fore.RESET)
        return
    print(Style.BRIGHT, Fore.GREEN, "Enjoy your movie/serie!", Style.RESET_ALL)


# main loop
def main():
    while True:
        ## ask user for movie or serie
        type_name = input("What you want serie or movie? (s, m): ").lower()
        if type_name not in ("s", "m"):
            logger.warning("Invalid media type input: %r", type_name)
            print(Fore.RED, "## type_name must be 's(serie)' or 'm(movie)'", Fore.RESET)
            continue

        name = input("Enter your movie/serie name: ")
        logger.info("Search requested: query=%r type=%s", name, type_name)
        data = find_movie_or_serie(name, type_name)
        if not data:
            logger.info("Search returned 0 results: query=%r type=%s", name, type_name)
            print(f"{'movie' if type_name == 'm' else 'serie'} with {name} not found")
        else:
            logger.info(
                "Search returned %d result(s): query=%r type=%s",
                len(data),
                name,
                type_name,
            )
            ## select one of this movies/series
            while True:
                print(
                    Style.BRIGHT,
                    Fore.BLUE,
                    f"## select one of this {'movie' if type_name == 'm' else 'serie'}: ",
                    Style.RESET_ALL,
                )
                for i, item in enumerate(data):
                    print(
                        Fore.GREEN,
                        f"[{i}] ==> ",
                        Fore.RESET,
                        Style.BRIGHT,
                        data[i]["name"],
                        Style.RESET_ALL,
                    )
                try:
                    selected = int(input("ID: ").strip())
                except ValueError:
                    logger.warning("Non-integer ID input for media selection")
                    print(Fore.RED, "Wrong input, must be an integer", Fore.RESET)
                    continue

                if selected < len(data):
                    logger.info(
                        "Media selected: idx=%d name=%r",
                        selected,
                        data[selected].get("name"),
                    )
                    break
                logger.warning(
                    "Out-of-range media index: %d (0..%d)", selected, len(data) - 1
                )
                print(
                    Fore.RED,
                    f"Wrong index, must be in range[{0}, {len(data) - 1}]",
                    Fore.RESET,
                )

            ## show all types of this movie/serie
            print(f"\n#### {data[selected]['name']} ####\n")
            item_name = data[selected]["name"]
            data[selected].pop("name")
            ### if it's a movie show all types of this movie and ask user to select one of them
            if type_name == "m":
                while True:
                    no_data = None
                    print(Style.BRIGHT, "What type you want? ", Style.RESET_ALL)
                    for i, movie_type in enumerate(data[selected]):
                        if not data[selected][movie_type]:
                            print(
                                Fore.LIGHTBLACK_EX,
                                f"[{i}]: ",
                                Style.RESET_ALL,
                                movie_type,
                            )
                            no_data = i
                            continue
                        print(Fore.GREEN, f"[{i}]: ", Style.RESET_ALL, movie_type)

                    ### ask user to select one of these types
                    while True:
                        try:
                            id = int(input("? "))
                            if id == no_data:
                                logger.warning("Selected empty movie type idx=%d", id)
                                continue
                        except ValueError:
                            logger.warning("Non-integer input for movie type selection")
                            print(
                                Fore.RED, "Wrong input, must be an integer", Fore.RESET
                            )
                            continue
                        if id < len(data[selected]):
                            break
                        logger.warning("Out-of-range movie type index: %d", id)
                        print(
                            Fore.RED,
                            f"Wrong index must be in range[{0}, {len(data[selected]) - 1}]",
                            Fore.RESET,
                        )

                    ### show all movies of this type and ask user to select one of them
                    for i, value in enumerate(data[selected]):
                        if i == id:
                            ### show all movies of this type and ask user to select one of them
                            movie_type = value
                            while True:
                                print(
                                    Fore.BLUE,
                                    Style.BRIGHT,
                                    "Choise what you want: ",
                                    Style.RESET_ALL,
                                )
                                for i, item in enumerate(data[selected][movie_type]):
                                    print(
                                        Fore.GREEN,
                                        f"[{i}]: ",
                                        Fore.RESET,
                                        item["title"],
                                    )
                                try:
                                    i = int(input("? "))
                                except ValueError:
                                    print(
                                        Fore.RED,
                                        "Wrong input, must be an integer",
                                        Fore.RESET,
                                    )
                                    continue

                                if i < len(data[selected][movie_type]):
                                    print(
                                        f"Link: {data[selected][movie_type][i]['link']}"
                                    )
                                    d = input("Do you want to download this?(y/n)")

                                    if d.lower() == "y":
                                        file_name = data[selected][movie_type][i][
                                            "link"
                                        ].split("/")[-1]
                                        download_file(
                                            data[selected][movie_type][i]["link"],
                                            file_name,
                                            save_dir=f"./downloads/movies/{item_name}",
                                        )
                                    else:
                                        if (
                                            input(
                                                "Do you want to watch this online?(y/n)"
                                            )
                                            .lower()
                                            .strip()
                                            == "y"
                                        ):
                                            watch_stream(
                                                data[selected][movie_type][i]["link"]
                                            )
                                    print(
                                        Fore.BLUE,
                                        "If you want to exit press q: ",
                                        Fore.RESET,
                                    )
                                    q = input("?")
                                    if q.lower() == "q":
                                        return 1
                                    return 0
                                print(
                                    Fore.RED,
                                    f"Wrong index, must be in range[{0}, {len(data[selected][movie_type])}]",
                                    Fore.RESET,
                                )
            else:
                while True:
                    no_data = None
                    print(Style.BRIGHT, "What type you want? ", Style.RESET_ALL)
                    for i, movie_type in enumerate(data[selected]):
                        if not data[selected][movie_type]:
                            print(
                                Fore.LIGHTBLACK_EX,
                                f"[{i}]: ",
                                Style.RESET_ALL,
                                movie_type,
                            )
                            no_data = i
                            continue
                        print(Fore.GREEN, f"[{i}]: ", Style.RESET_ALL, movie_type)
                    ### ask user to select one of these types
                    while True:
                        try:
                            id = int(input("? "))
                            if id == no_data:
                                logger.warning("Selected empty serie type idx=%d", id)
                                continue
                        except ValueError:
                            logger.warning("Non-integer input for serie type selection")
                            print(
                                Fore.RED, "Wrong input, must be an integer", Fore.RESET
                            )
                            continue
                        if id < len(data[selected]):
                            break
                        logger.warning("Out-of-range serie type index: %d", id)
                        print(
                            Fore.RED,
                            f"Wrong index must be in range[{0}, {len(data[selected]) - 1}]",
                            Fore.RESET,
                        )

                    ### show all movies of this type and ask user to select one of them
                    for i, value in enumerate(data[selected]):
                        if i == id:
                            ### show all movies of this type and ask user to select one of them
                            movie_type = value
                            while True:
                                logger.info("Season selection for serie=%s type=%s", item_name, movie_type)
                                print(Fore.BLUE, "Choise season: ")
                                for i, s in enumerate(data[selected][movie_type]):
                                    print(Fore.GREEN, f"[{i}] ==>", Fore.RESET, s)
                                try:
                                    season = int(input("? "))
                                except ValueError:
                                    logger.warning("Non-integer input for season selection")
                                    print(
                                        Fore.RED,
                                        "Wrong input, must be an integer",
                                        Fore.RESET,
                                    )
                                    continue
                                if id < len(data[selected]):
                                    break
                            season = list(data[selected][movie_type].keys())[season]
                            logger.info("Quality selection for season=%s", season)
                            while True:
                                print(
                                    Fore.BLUE,
                                    Style.BRIGHT,
                                    "Choise what you want: ",
                                    Style.RESET_ALL,
                                )
                                for i, item in enumerate(
                                    data[selected][movie_type][season]
                                ):
                                    print(Fore.GREEN, f"[{i}]: ", Fore.RESET, item)
                                try:
                                    i = int(input("? "))
                                    if i < len(data[selected][movie_type][season]):
                                        quality = list(
                                            data[selected][movie_type][season].keys()
                                        )[i]
                                    else:
                                        continue
                                except ValueError:
                                    logger.warning("Non-integer input for quality selection")
                                    print(
                                        Fore.RED,
                                        "Wrong input, must be an integer",
                                        Fore.RESET,
                                    )
                                    continue

                                else:
                                    while True:
                                        print(
                                            Fore.BLUE,
                                            f"Do you want to download all episode from {season} (y,n)",
                                            Fore.RESET,
                                        )
                                        all_episodes = input("? ").strip().lower()
                                        if all_episodes not in ("y", "n"):
                                            print(
                                                Fore.RED,
                                                "Must be in (y, n)!",
                                                Fore.RESET,
                                            )
                                            continue
                                        break

                                    if all_episodes == "y":
                                        logger.info(
                                            "Batch download: serie=%s type=%s season=%s quality=%s episodes=%d",
                                            item_name,
                                            movie_type,
                                            season,
                                            quality,
                                            len(data[selected][movie_type][season][quality]),
                                        )
                                        for episode, value in data[selected][
                                            movie_type
                                        ][season][quality].items():
                                            logger.info(
                                                "Downloading episode %s from %s",
                                                episode,
                                                value['link'][:80],
                                            )
                                            print(
                                                Fore.GREEN,
                                                f"Start Downloading {episode} with link: {value['link']}....",
                                                Fore.RESET,
                                            )
                                            file_name = data[selected][movie_type][season][
                                                quality
                                            ][episode]["link"].split("/")[-1]
                                            if not download_file(
                                                data[selected][movie_type][season][
                                                    quality
                                                ][episode]["link"],
                                                file_name,
                                                save_dir=f"./downloads/series/{item_name}/{season}",
                                            ):
                                                logger.error(
                                                    "Failed to download episode %s for serie=%s",
                                                    episode,
                                                    item_name,
                                                )
                                                print(
                                                    Fore.RED,
                                                    f"We have truble in downloading episode {episode}!",
                                                    Fore.RESET,
                                                )
                                            else:
                                                logger.info(
                                                    "Episode %s downloaded successfully",
                                                    episode,
                                                )
                                                print(
                                                    Fore.GREEN,
                                                    f"Episode {episode} downloaed successfuly",
                                                    Fore.RESET,
                                                )
                                    else:
                                        while True:
                                            print(Fore.BLUE, "Choise episode: ")
                                            for i, episode in enumerate(
                                                data[selected][movie_type][season][
                                                    quality
                                                ]
                                            ):
                                                print(
                                                    Fore.GREEN,
                                                    f"[{i}] ==>",
                                                    Fore.RESET,
                                                    episode,
                                                )
                                            try:
                                                i = int(input("?"))
                                            except ValueError:
                                                logger.warning("Non-integer input for episode selection")
                                                print(
                                                    Fore.RED,
                                                    "Wrong input, must be an integer",
                                                    Fore.RESET,
                                                )
                                                continue
                                            break
                                        episode = list(
                                            data[selected][movie_type][season][
                                                quality
                                            ].keys()
                                        )[i]

                                        logger.info(
                                            "Single episode selected: %s (quality=%s)",
                                            episode,
                                            quality,
                                        )
                                        print(
                                            f"Link: {data[selected][movie_type][season][quality][episode]['link']}"
                                        )
                                        d = input("Do you want to download this?(y/n)")

                                        if d.lower() == "y":
                                            file_name = data[selected][movie_type][season][
                                                quality
                                            ][episode]["link"].split("/")[-1]
                                            download_file(
                                                data[selected][movie_type][season][
                                                    quality
                                                ][episode]["link"],
                                                file_name,
                                                save_dir=f"./downloads/series/{item_name}/{season}",
                                            )
                                        else:
                                            if (
                                                input(
                                                    "Do you want to watch this online?(y/n)"
                                                )
                                                .lower()
                                                .strip()
                                                == "y"
                                            ):
                                                watch_stream(
                                                    data[selected][movie_type][season][
                                                        quality
                                                    ][episode]["link"]
                                                )
                                        print(
                                            Fore.BLUE,
                                            "If you want to exit press q: ",
                                            Fore.RESET,
                                        )
                                        q = input("?")
                                        if q.lower() == "q":
                                            logger.info("User requested exit from episode menu")
                                            return 1
                                        return 0
                                    print(
                                        Fore.RED,
                                        f"Wrong index, must be in range[{0}, {len(data[selected][movie_type])}]",
                                        Fore.RESET,
                                    )


if __name__ == "__main__":
    logger.info("Application started")
    while main() == 0:
        logger.debug("Main loop returned 0, continuing")
        continue
    logger.info("Application exiting")
    print(Fore.GREEN, "Good luck", Fore.RESET)

from colorama import Style, Fore
import requests
from storage_db import find_movie_or_serie
from tqdm import tqdm
import subprocess
import os


# function to download file from url
def download_file(url, filename):
    attempt = 0
    while attempt <= 3:
        try:
            downloaded_size = 0
            if os.path.exists(filename):
                downloaded_size = os.path.getsize(filename)
                print(
                    Fore.YELLOW,
                    f"{downloaded_size} of {filename} downloaded",
                    Fore.RESET,
                )

            headers = {}
            if downloaded_size > 0:
                headers["Range"] = f"bytes={downloaded_size}-"

            response = requests.get(url, stream=True, headers=headers, timeout=30)

            if downloaded_size > 0:
                total_size = (
                    int(response.headers.get("content-length", 0)) + downloaded_size
                )
            else:
                total_size = int(response.headers.get("content-length", 0))

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
                with open(filename, mode) as file:
                    for data in response.iter_content(block_size):
                        file.write(data)
                        progress_bar.update(len(data))
            print(Fore.RESET)
        except requests.exceptions.ConnectionError:
            attempt += 1
            print(Fore.RED, f"Connection error in attempt {attempt}", Fore.RESET)
            attempt += 1
        except requests.exceptions.ConnectTimeout:
            attempt += 1
            print(Fore.RED, f"Connection timeoute in attempt {attempt}", Fore.RESET)
        except requests.exceptions.ChunkedEncodingError:
            pass
        except Exception as Error:
            attempt += 1
            print(Fore.RED, f"Error: {str(Error)}", Fore.RESET)
        else:
            print(
                Style.BRIGHT,
                Fore.GREEN,
                f"{filename} downloaded successfully.",
                Style.RESET_ALL,
            )
            return True
    print(Fore.RED, "Download was not successfuly please try later", Fore.RESET)


def watch_stream(url):
    command = ["mpv", "--autofit=80%", url]
    subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(Style.BRIGHT, Fore.GREEN, "Enjoy your movie/serie!", Style.RESET_ALL)


# main loop
def main():
    while True:
        ## ask user for movie or serie
        type_name = input("What you want serie or movie? (s, m): ").lower()
        if type_name not in ("s", "m"):
            print(Fore.RED, "## type_name must be 's(serie)' or 'm(movie)'", Fore.RESET)
            continue

        name = input("Enter your movie/serie name: ")
        data = find_movie_or_serie(name, type_name)
        if not data:
            print(f"{'movie' if type_name == 'm' else 'serie'} with {name} not found")
        else:
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
                    print(Fore.RED, "Wrong input, must be an integer", Fore.RESET)
                    continue

                if selected < len(data):
                    break
                print(
                    Fore.RED,
                    f"Wrong index, must be in range[{0}, {len(data) - 1}]",
                    Fore.RESET,
                )

            ## show all types of this movie/serie
            print(f"\n#### {data[selected]['name']} ####\n")
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
                                continue
                        except ValueError:
                            print(
                                Fore.RED, "Wrong input, must be an integer", Fore.RESET
                            )
                            continue
                        if id < len(data[selected]):
                            break
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
                                        name = data[selected][movie_type][i][
                                            "link"
                                        ].split("/")[-1]
                                        download_file(
                                            data[selected][movie_type][i]["link"], name
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
                                continue
                        except ValueError:
                            print(
                                Fore.RED, "Wrong input, must be an integer", Fore.RESET
                            )
                            continue
                        if id < len(data[selected]):
                            break
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
                                print(Fore.BLUE, "Choise season: ")
                                for i, s in enumerate(data[selected][movie_type]):
                                    print(Fore.GREEN, f"[{i}] ==>", Fore.RESET, s)
                                try:
                                    season = int(input("? "))
                                except ValueError:
                                    print(
                                        Fore.RED,
                                        "Wrong input, must be an integer",
                                        Fore.RESET,
                                    )
                                    continue
                                if id < len(data[selected]):
                                    break
                            season = list(data[selected][movie_type].keys())[season]
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
                                        for episode, value in data[selected][
                                            movie_type
                                        ][season][quality].items():
                                            print(
                                                Fore.GREEN,
                                                f"Start Downloading {episode} with link: {value['link']}....",
                                                Fore.RESET,
                                            )
                                            name = data[selected][movie_type][season][
                                                quality
                                            ][episode]["link"].split("/")[-1]
                                            if not download_file(
                                                data[selected][movie_type][season][
                                                    quality
                                                ][episode]["link"],
                                                name,
                                            ):
                                                print(
                                                    Fore.RED,
                                                    f"We have truble in downloading episode {episode}!",
                                                    Fore.RESET,
                                                )
                                            else:
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

                                        print(
                                            f"Link: {data[selected][movie_type][season][quality][episode]['link']}"
                                        )
                                        d = input("Do you want to download this?(y/n)")

                                        if d.lower() == "y":
                                            name = data[selected][movie_type][season][
                                                quality
                                            ][episode]["link"].split("/")[-1]
                                            download_file(
                                                data[selected][movie_type][season][
                                                    quality
                                                ][episode]["link"],
                                                name,
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
                                            return 1
                                        return 0
                                    print(
                                        Fore.RED,
                                        f"Wrong index, must be in range[{0}, {len(data[selected][movie_type])}]",
                                        Fore.RESET,
                                    )


if __name__ == "__main__":
    while main() == 0:
        continue
    print(Fore.GREEN, "Good luck", Fore.RESET)

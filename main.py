from colorama import Style, init, Fore
from storage_db import find_movie_or_serie

# initialize colorama
init(autoreset=True)

# main loop
while True:
    ## ask user for movie or serie
    type_name = input("What you want serie or movie? (s, m): ").lower()
    if type_name not in ("s", "m"):
        print("## type_name must be 's(serie)' or 'm(movie)'")
    name = input("Enter your movie/serie name: ")
    data = find_movie_or_serie(name, type_name)
    if not data:
        print(f"{"movie" if type_name == "m" else "serie"} with {name} not found")
    else:
        ## select one of this movies/series
        while True:
            print(Style.BRIGHT, Fore.BLUE, f"## select one of this {"movie" if type_name == "m" else "serie"}: ", Style.RESET_ALL)
            for i, item in enumerate(data):
                print(Fore.GREEN, f"[{i}] ==> ", Fore.RESET, Style.BRIGHT, data[i]["name"], Style.RESET_ALL)
            try:
                selected = int(input("ID: "))
            except ValueError:
                print(Fore.RED, "Wrong input, must be an integer", Fore.RESET)
                continue

            if selected < len(data):
                break
            print(Fore.RED, f"Wrong index, must be in range[{0}, {len(data)-1}]", Fore.RESET)

        ## show all types of this movie/serie
        print(f"\n#### {data[selected-1]["name"]} ####\n")
        data[selected-1].pop('name')
        ### if it's a movie show all types of this movie and ask user to select one of them
        if type_name == "m":
            while True:
                print(Style.BRIGHT, "What type you want? ", Style.DIM)
                for i, movie_type in enumerate(data[selected-1]):
                    print(Fore.GREEN, f"[{i}]: ", Style.RESET_ALL, movie_type)

                ### ask user to select one of these types
                while True:
                    try:
                        id = int(input("? "))
                    except ValueError:
                        print(Fore.RED, "Wrong input, must be an integer", Fore.RESET)
                        continue
                    if id < len(data[selected-1]):
                        break
                    print(Fore.RED, f"Wrong index must be in range[{0}, {len(data[selected-1])-1}]", Fore.RESET)

                ### show all movies of this type and ask user to select one of them
                for i, value in enumerate(data[selected-1]):
                    if i == id:

                        ### show all movies of this type and ask user to select one of them
                        movie_type = value
                        while True:
                            print(Fore.BLUE, Style.BRIGHT, "Choise what you want: ", Style.RESET_ALL)
                            for i, item in enumerate(data[selected-1][movie_type]):
                                print(Fore.GREEN, f"[{i}]: ", Fore.RESET, item["title"])
                            try:
                                i = int(input("? "))
                            except ValueError:
                                print(Fore.RED, "Wrong input, must be an integer", Fore.RESET)
                                continue
                            if i < len(data[selected-1][movie_type]):
                                print(f"Link: {data[selected-1][movie_type][i]["link"]}")
                                d = input("Do you want to download this?(y/n)")
                                if d.lower() == 'y':
                                    pass
                                else:
                                    break
                                break
                            print(Fore.RED, f"Wrong index, must be in range[{0}, {len(data[selected-1][movie_type])}]", Fore.RESET)
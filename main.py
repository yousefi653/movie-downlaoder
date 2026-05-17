from colorama import Style, init, Fore
from storage_db import find_movie_or_serie

while True:
    type_name = input("What you want serie or movie? (s, m): ").lower()
    if type_name not in ("s", "m"):
        print("## type_name must be 's(serie)' or 'm(movie)'")
    name = input("Enter your movie/serie name: ")
    data = find_movie_or_serie(name, type_name)
    if not data:
        print(f"{"movie" if type_name == "m" else "serie"} with {name} not found")
    else:
        while True:
            print(Style.BRIGHT, Fore.BLUE, f"## select one of this {"movie" if type_name == "m" else "serie"}: ", Style.RESET_ALL)
            for i, item in enumerate(data):
                print(Fore.GREEN, f"[{i}] ==> ", Fore.RESET, Style.BRIGHT, data[i]["name"], Style.RESET_ALL)
            selected = int(input("ID: "))
            if selected < len(data):
                break
            print(Fore.RED, f"Wrong index, must be in range[{0}, {len(data)-1}]", Fore.RESET)
        print(f"\n#### {data[selected-1]["name"]} ####\n")
        data[selected-1].pop('name')
        if type_name == "m":
            while True:
                print(Style.BRIGHT, "What type you want? ", Style.DIM)
                for i, movie_type in enumerate(data[selected-1]):
                    print(Fore.GREEN, f"[{i}]: ", Style.RESET_ALL, movie_type)
                while True:
                    id = int(input("? "))
                    if id < len(data[selected-1]):
                        break
                    print(Fore.RED, f"Wrong index must be in range[{0}, {len(data[selected-1])-1}]", Fore.RESET)

                for i, value in enumerate(data[selected-1]):
                    if i == id:
                        movie_type = value
                        while True:
                            print(Fore.BLUE, Style.BRIGHT, "Choise what you want: ", Style.RESET_ALL)
                            for i, item in enumerate(data[selected-1][movie_type]):
                                print(Fore.GREEN, f"[{i}]: ", Fore.RESET, item["title"])
                            i = int(input("? "))
                            if i < len(data[selected-1][movie_type]):
                                print(f"Link: {data[selected-1][movie_type][i]["link"]}")
                                d = input("Do you want to download this?(y/n)")
                                if d.lower() == 'y':
                                    pass
                                else:
                                    break
                                break
                            print(Fore.RED, f"Wrong index, must be in range[{0}, {len(data[selected-1][movie_type])}]", Fore.RESET)
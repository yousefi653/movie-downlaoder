# Movie Downloader - DonyayeSerial Downloader

A Python-based downloader for movies and TV series from DonyayeSerial archive.

## Features

- **Browse and search** movies and series by name
- **Multiple quality options**: SoftSub, Dubbed, NoSub
- **Serie episode selection**: Choose specific seasons and qualities
- **Resume downloads**: Automatically resume interrupted downloads
- **Organized file saving**:
  - Movies: `./downloads/movies/movie-name/filename`
  - Series: `./downloads/series/serie-name/season/filename`
- **Colorful terminal output** with progress bars
- **Logger configuration**: Outputs to both console and `logs/app.log`

## Prerequisites

- Python 3.8+
- MongoDB running at `127.0.0.1:27017` (for database storage)

## Requirements

The required Python packages are listed in `requirements.txt`. Install them using:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install beautifulsoup4 bs4 certifi charset-normalizer colorama dnspython filelock idna platformdirs pymongo requests requests-file simple-header simple-useragent soupsieve tldextract tqdm typing_extensions ua-parser ua-parser-builtins urllib3 validators
```

## Project Structure

```
main.py              # Main interactive application
fetch_data.py        # Data fetching and parsing
storage_db.py        # MongoDB storage operations
logger_config.py     # Logging configuration
html_code.txt        # Cached HTML archive
html_code_with_a.txt # Prettified HTML archive
info                 # Cache modification date (pickle)
logs/                # Log directory
backups/             # Backup directory
downloads/           # Downloaded files directory
  ├── movies/        # Movie downloads
  └── series/        # Series downloads
parsed_links.txt     # Already parsed links cache
remains_data.json    # Failed download records
README.md            # This file
```

## Quick Start

1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   pip install requests colorama tqdm pymongo bs4 simple-header urllib3
   ```
3. **Ensure MongoDB is running** at the default connection
4. **Run the application**:
   ```bash
   python main.py
   ```

## Usage

When you run `main.py`:

1. **Select media type**: Enter `m` for movie or `s` for serie
2. **Enter search name**: The name you want to search for
3. **Select from results**: Choose the desired movie/serie from the list
4. **For movies**: Select quality type (SoftSub, Dubbed, NoSub) then choose the specific file
5. **For series**: 
   - Select quality type
   - Choose season
   - Choose quality for that season
   - Download all episodes from a season or select individual episodes

## File Organization

### Movies
Downloaded files are saved to:
```
./downloads/movies/{movie-name}/{filename}
```

### Series
Downloaded files are saved to:
```
./downloads/series/{serie-name}/{season}/{filename}
```

## Logging

- Console output can be suppressed by setting `quiet=True` in `setup_logging()`
- All logs are written to `logs/app.log`
- Log level can be configured via `LOG_LEVEL` environment variable

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

## License

MIT
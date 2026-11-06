# Movie and Series Downloader

A Python command-line application for browsing and downloading movies and TV series from the DonyayeSerial archive.

## Features

- Search movies and series by name
- Choose between available subtitle and audio options
- Select seasons and individual episodes
- Resume interrupted downloads
- Organize downloaded files into movie and series directories
- Display download progress in the terminal
- Log application activity to the console and a log file

## Requirements

- Python 3.8 or newer
- MongoDB running locally at `127.0.0.1:27017`
- Python dependencies listed in `requirements.txt`

## Installation

Clone the repository:

```bash
git clone https://github.com/yousefi653/movie-downlaoder.git
cd movie-downlaoder
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Make sure MongoDB is running, then start the application:

```bash
python main.py
```

## Usage

After starting the application:

1. Choose whether to search for a movie or a series.
2. Enter a title to search.
3. Select an item from the search results.
4. Choose the available quality or audio/subtitle option.
5. For a series, select a season and then choose whether to download all episodes or specific episodes.

## Download Organization

Downloaded files are organized under the `downloads/` directory:

```text
downloads/
├── movies/
└── series/
    └── <series-name>/
        └── <season>/
```

## Logging

Application logs are written to `logs/app.log` as well as displayed in the terminal.

## Important

This project is intended for learning and personal use. Make sure you have the right to access and download any content you use it with, and follow the source website's terms.

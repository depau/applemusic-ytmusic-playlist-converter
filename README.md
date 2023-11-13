# Apple Music playlist scraper and YouTube Music playlist uploader

This project contains two scripts:

- One to scrape an Apple Music playlist and save the list of tracks to a JSON
  file
- One to read the JSON file and upload the tracks to a YouTube Music playlist

## Usage

### Create virtualenv and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Scrape Apple Music playlist

```bash
./applemusic2json.py 'https://music.apple.com/xx/playlist/...' > playlist.json
```

### Upload to YouTube Music playlist

The playlist ID is the last part of the URL, after the last `/`, when viewing
the playlist in the browser.

```bash
# Authenticate with YouTube Music
ytmusicapi oauth --file oauth.json

# Upload playlist
./json2ytmusic.py 'PlaylistID' 'playlist.json'
```

## License

MIT License. See [LICENSE](LICENSE) file.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import sys

import requests
from bs4 import BeautifulSoup

YELLOW = '\033[33m'
GREEN = '\033[32m'
RED = '\033[31m'
RESET = '\033[0m'


def main():
    # Parse one argument: the playlist URL
    parser = argparse.ArgumentParser(description='Convert Apple Music playlist to a JSON file')
    parser.add_argument('playlist_url', help='Apple Music playlist URL')
    parser.add_argument('-r', '--reverse', action='store_true', help='reverse the order of the songs')
    args = parser.parse_args()

    playlist_url = args.playlist_url

    print(f'Getting playlist from Apple Music...', file=sys.stderr)
    songs = get_songs_from_apple_playlist(playlist_url)
    if args.reverse:
        songs.reverse()

    json.dump(songs, sys.stdout, indent=4)

    print(f'{GREEN} Done!{RESET}', file=sys.stderr)


def get_songs_from_apple_playlist(playlist_url):
    r = requests.get(playlist_url)

    # Check if the request was successful
    if r.status_code != 200:
        print(f'{RED} there was an error while getting playlist from Apple Music: {r.text} ({r.status_code}){RESET}',
              file=sys.stderr)
        pass

    bellazuppa = BeautifulSoup(r.content, 'html.parser')
    script_tag = bellazuppa.find("script", {"id": "serialized-server-data"})

    j = json.loads(script_tag.text)

    try:
        print(f'{YELLOW} Found playlist "{j[0]["data"]["seoData"]["schemaContent"]["name"]}" '
              f'by {j[0]["data"]["seoData"]["schemaContent"]["author"]["name"]}{RESET}', file=sys.stderr)
    except KeyError:
        pass

    # JQ query: '.[].data.sections[1].items[] | ([.title, .artistName, .tertiaryLinks[0].title])'
    songs = []
    for song in j[0]['data']['sections'][1]['items']:
        title = song['title']
        artist = song['artistName']
        album = song['tertiaryLinks'][0]['title']
        duration = song['duration']

        songs.append({
            'title': title,
            'artist': artist,
            'album': album,
            'duration': duration,
        })

    return songs


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json
import os
import re
import sys
import warnings
from typing import Optional

import requests

YELLOW = '\033[33m'
GREEN = '\033[32m'
RED = '\033[31m'
RESET = '\033[0m'


class AppleMusicClient:
    def __init__(self, bearer_token: str, music_token: Optional[str], api_url='https://amp-api.music.apple.com',
                 search_country_code='US'):
        self.bearer_token = bearer_token
        self.music_token = music_token
        self.api_url = api_url
        self.search_country_code = search_country_code
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Accept": '*/*',
            "Accept-Language": 'en-US,en;q=0.5',
            "Accept-Encoding": 'gzip, deflate',
            "Referer": 'https://music.apple.com/',
            "Origin": 'https://music.apple.com',
            "Sec-Fetch-Dest": 'empty',
            "Sec-Fetch-Mode": 'cors',
            "Sec-Fetch-Site": 'same-site',
            "Te": 'trailers'
        }
        if self.music_token:
            self.headers['Music-User-Token'] = self.music_token

    def search_songs(self, search_term, limit=10):
        """Search for songs on Apple Music."""
        url = f"{self.api_url}/v1/catalog/{self.search_country_code.lower()}/search"
        params = {
            'term': search_term,
            'types': 'songs',
            'limit': limit
        }
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error searching songs: {response.text}")

    def add_songs_to_playlist(self, playlist_id, song_ids):
        """Add a list of songs to an existing playlist."""
        url = f"{self.api_url}/v1/me/library/playlists/{playlist_id}/tracks"

        for chunk in (song_ids[i:i + 100] for i in range(0, len(song_ids), 100)):
            data = {
                'data': [{'id': song_id, 'type': 'songs'} for song_id in chunk]
            }
            response = requests.post(url, headers=self.headers, json=data)
            if response.status_code not in [200, 201, 204]:
                raise warnings.warn(f"Error adding songs to playlist: {response.text}")

    def make_playlist_public(self, playlist_id):
        """Make a playlist public."""
        url = f"{self.api_url}/v1/me/library/playlists/{playlist_id}"
        data = {
            'attributes': {
                'name': 'playlist',
                'visibility': 'public',

            }
        }
        response = requests.patch(url, headers=self.headers, json=data)
        if response.status_code not in [200, 201, 204]:
            raise Exception(f"Error making playlist public: {response.text}")

    def get_playlist(self, playlist_id):
        url = f"{self.api_url}/v1/me/library/playlists/{playlist_id}"
        return requests.get(url, headers=self.headers).json()

    def get_library_playlists(self):
        url = f"{self.api_url}/v1/me/library/playlists"
        return requests.get(url, headers=self.headers).json()

    def get_playlist_tracks(self, playlist_id):
        url = f"{self.api_url}/v1/me/library/playlists/{playlist_id}/tracks"
        tracks = []
        while True:
            r = requests.get(url, headers=self.headers)
            if r.status_code != 200:
                raise Exception(f"Error getting playlist tracks: {r.text}")
            j = r.json()
            if 'data' in j:
                tracks.extend(j['data'])
            if 'next' in j:
                url = f"{self.api_url}{j['next']}"
            else:
                break
        return tracks


def main():
    parser = argparse.ArgumentParser(description='Upload a JSON playlist to Apple Music',
                                     epilog="To get the tokens, log into Apple Music on a web browser and get the "
                                            "tokens from the `Authorization` and `Music-User-Token` headers in an API "
                                            "request")

    parser.add_argument('playlist_id', help='Apple Music playlist ID')
    parser.add_argument('input', nargs='?', type=argparse.FileType('r'), default='-',
                        help='JSON playlist file (default stdin)')
    parser.add_argument('-b', '--bearer-token', help='Apple Music bearer token')
    parser.add_argument('-m', '--music-token', help='Apple Music music token')
    parser.add_argument('-C', '--country-code', default='US', help='Country code (default US)')
    parser.add_argument('-c', '--cache', default='applemusic-cache.json',
                        help='Cache file (default applemusic-cache.json)')

    args = parser.parse_args()

    client = AppleMusicClient(args.bearer_token, args.music_token, search_country_code=args.country_code)

    with args.input as f:
        songs = json.load(f)

    song_ids = []

    cache = {}
    if os.path.exists(args.cache):
        with open(args.cache, 'r') as f:
            cache = json.load(f)

    playlist_id = args.playlist_id

    existing = set()
    if args.music_token:
        playlist_data = client.get_playlist(playlist_id)
        if 'data' not in playlist_data:
            # Try to convert from global playlist ID to library playlist ID
            response = client.get_library_playlists()
            for playlist in response['data']:
                if playlist["attributes"]["playParams"].get("globalId") == playlist_id:
                    playlist_id = playlist["id"]
                    break
            else:
                raise Exception(f"Playlist {playlist_id} not found")

            playlist_data = client.get_playlist(playlist_id)
            if 'data' not in playlist_data:
                raise Exception(f"Playlist {playlist_id} not found")

        print(f"Found playlist in library with library ID {playlist_id}; fetching tracks...", file=sys.stderr)

        tracks = client.get_playlist_tracks(playlist_id)
        for track in tracks:
            existing.add(track['attributes']['playParams']['catalogId'])

        print(f"Found playlist containing {len(existing)} songs in library", file=sys.stderr)

    try:
        for song in songs:
            title = song['title'] or ''
            artist = song['artist'] or ''

            query = f'{artist} {title}'.replace(".mp3", "").replace(".m4a", "").replace(".wav", "")
            query = re.sub(r'\(official \w*\)', '', query, flags=re.IGNORECASE).strip()

            if 'appleId' in song:
                cache[query] = song['appleId']
                print(f'{GREEN} {title} - {artist} '.ljust(60, ' '), end='')
                print(f'-> provided: {song["appleId"]}{RESET}')
                song_ids.append(song['appleId'])
                continue

            if query in cache:
                print(f'{YELLOW} {title} - {artist} '.ljust(60, ' '), end='')
                print(f'-> cached: {cache[query]}{RESET}')
                if cache[query] not in existing:
                    song_ids.append(cache[query])
                continue

            results = client.search_songs(query, limit=5)

            if not results or not results['results'] or not results['results']['songs'] or not \
                    results['results']['songs']['data']:
                print(f'{RED} {title} - {artist} '.ljust(60, ' '), end='')
                print(f'-> not found{RESET}')
                continue

            tracks = results['results']['songs']['data']

            song_id = tracks[0]['id']
            song_attributes = tracks[0]['attributes']

            cache[query] = song_id
            print(f'{GREEN} {title} - {artist} '.ljust(60, ' '), end='')
            print(f'-> found: {song_attributes["name"]} - {song_attributes["artistName"]}{RESET}')

            if song_id not in existing:
                song_ids.append(song_id)
    finally:
        with open(args.cache, 'w') as f:
            json.dump(cache, f, indent=4)

    if not args.music_token:
        print(f"{YELLOW}No music token provided, skipping adding songs to playlist{RESET}")
        return

    print(f"Adding {len(song_ids)} songs to playlist {playlist_id}")

    if len(song_ids) > 0:
        client.add_songs_to_playlist(playlist_id, song_ids)


if __name__ == '__main__':
    main()

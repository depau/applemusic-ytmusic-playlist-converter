#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json
import os
from typing import Optional

import requests

YELLOW = '\033[33m'
GREEN = '\033[32m'
RESET = '\033[0m'


class AppleMusicClient:
    def __init__(self, bearer_token: str, music_token: Optional[str], api_url='https://amp-api.music.apple.com',
                 search_country_code='IT'):
        self.bearer_token = bearer_token
        self.music_token = music_token
        self.api_url = api_url
        self.search_country_code = search_country_code
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
        }
        if self.music_token:
            self.headers['Music-User-Token'] = self.music_token

    def search_songs(self, search_term, limit=10):
        """Search for songs on Apple Music."""
        url = f"{self.api_url}/v1/catalog/{self.search_country_code}/search"
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
        data = {
            'data': [{'id': song_id, 'type': 'songs'} for song_id in song_ids]
        }
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Error adding songs to playlist: {response.text}")


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
    parser.add_argument('-C', '--country-code', default='IT', help='Country code (default IT)')
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

    for song in songs:
        title = song['title'] or ''
        artist = song['artist'] or ''

        query = f'{artist} {title}'.strip()

        if 'appleId' in song:
            cache[query] = song['appleId']
            print(f'Provided: {title} - {artist} -> {song["id"]}')
            song_ids.append(song['appleId'])
            continue

        if query in cache:
            print(f'Cached: {title} - {artist} -> {cache[query]}')
            song_ids.append(cache[query])
            continue

        results = client.search_songs(query, limit=5)

        if len(results['results']['songs']['data']) == 0:
            print(f'Not found: {title} - {artist}')
            continue

        song_id = results['results']['songs']['data'][0]['id']
        cache[query] = song_id
        print(f'Found: {title} - {artist} -> {song_id}')
        song_ids.append(song_id)

    if not args.music_token:
        print(f"{YELLOW}No music token provided, skipping adding songs to playlist{RESET}")
        return

    print(f"Adding {len(song_ids)} songs to playlist {args.playlist_id}")

    if len(song_ids) > 0:
        client.add_songs_to_playlist(args.playlist_id, song_ids)


if __name__ == '__main__':
    main()

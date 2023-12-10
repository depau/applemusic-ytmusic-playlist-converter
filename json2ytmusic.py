#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json
import os

from ytmusicapi import YTMusic

YELLOW = '\033[33m'
GREEN = '\033[32m'
RESET = '\033[0m'


def main():
    parser = argparse.ArgumentParser(description='Convert Apple Music playlist to YouTube Music')
    parser.add_argument('playlist_id', help='YouTube Music playlist ID')
    parser.add_argument('input', nargs='?', type=argparse.FileType('r'), default='-',
                        help='Apple Music playlist JSON file (default stdin)')
    parser.add_argument('-o', '--oauth', default='oauth.json', help='OAuth file (default oauth.json)')
    parser.add_argument('-c', '--cache', default='ytmusic-cache.json', help='Cache file (default ytmusic-cache.json)')
    args = parser.parse_args()

    yt = YTMusic(args.oauth)

    cache = {}
    if os.path.exists(args.cache):
        with open(args.cache, 'r') as f:
            cache = json.load(f)

    # noinspection PyTypeChecker
    dst_playlist = yt.get_playlist(args.playlist_id, limit=None)

    # Read the Apple Music playlist
    src_playlist = json.load(args.input)

    existing = set()
    for song in dst_playlist["tracks"]:
        existing.add(song['videoId'])

    to_add = []

    try:
        for song in src_playlist:
            title = song['title']
            artist = song['artist']

            query = f'{title} {artist}'

            if query in cache and cache[query] not in existing and cache[query] not in to_add:
                # print the line in yellow
                print(f'{YELLOW} {title} - {artist} '.ljust(60, ' '), end='')
                print(f'-> cached: {cache[query]}{RESET}')
                to_add.append(cache[query])
                continue

            results = yt.search(query, filter='songs', limit=5)
            if len(results) == 0:
                print(f'\033[31m No results for {query}{RESET}')
                continue

            # YouTube search is kinda good, so just take the first result
            best_result = results[0]

            print(f'{GREEN} {title} - {artist} '.ljust(60, ' '), end='')
            print(f'-> {best_result["title"]} - {best_result["artists"][0]["name"]}{RESET}')

            if best_result['videoId'] not in existing and best_result['videoId'] not in to_add:
                to_add.append(best_result['videoId'])
                cache[query] = best_result['videoId']
    finally:
        with open(args.cache, 'w') as f:
            json.dump(cache, f, indent=4)

    print(f'{YELLOW} Adding {len(to_add)} songs...{RESET}')

    if len(to_add) > 0:
        yt.add_playlist_items(args.playlist_id, videoIds=to_add)

    print(f'{GREEN} Done!{RESET}')


if __name__ == '__main__':
    main()

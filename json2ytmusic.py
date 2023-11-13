#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json

from ytmusicapi import YTMusic


def main():
    parser = argparse.ArgumentParser(description='Convert Apple Music playlist to YouTube Music')
    parser.add_argument('playlist_id', help='YouTube Music playlist ID')
    parser.add_argument('input', nargs='?', type=argparse.FileType('r'), default='-',
                        help='Apple Music playlist JSON file (default stdin)')
    args = parser.parse_args()

    yt = YTMusic("oauth.json")

    # noinspection PyTypeChecker
    dst_playlist = yt.get_playlist(args.playlist_id, limit=None)

    # Read the Apple Music playlist
    src_playlist = json.load(args.input)

    existing = set()
    for song in dst_playlist["tracks"]:
        existing.add(song['videoId'])

    to_add = []

    for song in src_playlist:
        title = song['title']
        artist = song['artist']

        query = f'{title} {artist}'

        results = yt.search(query, filter='songs', limit=5)
        if len(results) == 0:
            print(f'\033[31m No results for {query}\033[0m')
            continue

        # YouTube search is kinda good, so just take the first result
        best_result = results[0]

        print(f'\033[32m {title} - {artist} '.ljust(60, ' '), end='')
        print(f'-> {best_result["title"]} - {best_result["artists"][0]["name"]}\033[0m')

        if best_result['videoId'] not in existing and best_result['videoId'] not in to_add:
            to_add.append(best_result['videoId'])

    print(f'\033[33m Adding {len(to_add)} songs...\033[0m')

    print(json.dumps(to_add))
    yt.add_playlist_items(args.playlist_id, videoIds=to_add)

    print('\033[32m Done!\033[0m')


if __name__ == '__main__':
    main()

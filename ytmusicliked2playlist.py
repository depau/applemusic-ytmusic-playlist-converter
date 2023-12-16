#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys

from ytmusicapi import YTMusic


def main():
    # Parse one argument: the playlist ID
    parser = argparse.ArgumentParser(description='Sync the YouTube Music liked songs to a playlist')
    parser.add_argument('playlist_id', help='YouTube Music playlist ID')
    parser.add_argument('-o', '--oauth', default='oauth.json', help='OAuth file (default oauth.json)')
    args = parser.parse_args()

    playlist_id = args.playlist_id

    print(f'Getting playlist from YouTube Music...', file=sys.stderr)

    yt = YTMusic(args.oauth)

    # noinspection PyTypeChecker
    liked_songs = yt.get_liked_songs(limit=None)
    # noinspection PyTypeChecker
    dst_playlist = yt.get_playlist(args.playlist_id, limit=None)

    existing = set()
    for song in dst_playlist["tracks"]:
        existing.add(song['videoId'])

    to_add = []

    for song in liked_songs['tracks']:
        if song['videoId'] not in existing and song['videoId'] not in to_add:
            to_add.append(song['videoId'])

    print(f'Adding {len(to_add)} songs to playlist "{dst_playlist["title"]}" by {dst_playlist["author"]["name"]}',
          file=sys.stderr)

    yt.add_playlist_items(playlist_id, to_add)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import sys

from ytmusicapi import YTMusic

YELLOW = '\033[33m'
GREEN = '\033[32m'
RED = '\033[31m'
RESET = '\033[0m'


def main():
    # Parse one argument: the playlist ID, which can be `likedmusic` (default) or an actual playlist ID
    parser = argparse.ArgumentParser(description='Sync a YouTube Music playlist to a JSON file')
    parser.add_argument('playlist_id', help='YouTube Music playlist ID, or `likedmusic` (default)', nargs='?',
                        default='likedmusic')
    parser.add_argument('-O', '--output', type=argparse.FileType('w'), default='-', help='Output file (default stdout)')
    parser.add_argument('-r', '--reverse', action='store_true', help='reverse the order of the songs')
    parser.add_argument('-o', '--oauth', default='oauth.json', help='OAuth file (default oauth.json)')

    args = parser.parse_args()

    if not os.path.exists(args.oauth):
        if args.playlist_id == 'likedmusic':
            print(f'{RED} OAuth file not found, cannot read liked music{RESET}', file=sys.stderr)
            sys.exit(1)
        oauth = None
    else:
        oauth = args.oauth

    yt = YTMusic(oauth)

    print(f'Getting playlist from YouTube Music...', file=sys.stderr)

    if args.playlist_id == 'likedmusic':
        # noinspection PyTypeChecker
        playlist = yt.get_liked_songs(limit=None)
        print(f'{YELLOW} Found liked songs playlist{RESET}', file=sys.stderr)
    else:
        # noinspection PyTypeChecker
        playlist = yt.get_playlist(args.playlist_id, limit=None)
        author = playlist.get('author', {}).get('name', 'Unknown')
        print(f'{YELLOW} Found playlist "{playlist["title"]}" by {author}{RESET}', file=sys.stderr)

    tracks = list(playlist['tracks'])
    if args.reverse:
        tracks.reverse()

    output = []

    for track in tracks:
        output.append({
            'title': track['title'],
            'artist': ", ".join((i["name"] for i in (track.get('artists') or []))),
            'album': (track['album'] or {}).get('name'),
            'duration': (track.get('duration_seconds', 0) * 1000) or None, 'videoId': track['videoId'],
        })

    json.dump(output, args.output, indent=4)

    print(f'{GREEN} Done!{RESET}', file=sys.stderr)


if __name__ == '__main__':
    main()

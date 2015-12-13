#!/usr/bin/python3

import requests
import urllib
import sys


def search(query):
    params = {
        'action': 'wbsearchentities',
        'search': query,
        'language': 'en',
        'format': 'json',
        'limit': 10,
    }

    r = requests.get('https://www.wikidata.org/w/api.php', params)
    r.raise_for_status()
    json = r.json()

    results = []

    for res in json['search']:
        results.append((
            int(res['id'][1:]),
            res['label'],
            res['description'] if 'description' in res else '',
        ))

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: {} <query> ...'.format(sys.argv[0]))
        sys.exit(1)

    for q in sys.argv[1:]:
        results = search(q)
        print('Results for "{}":'.format(q))
        for r in results:
            print('{} : {} ({})'.format(*r))
        print()

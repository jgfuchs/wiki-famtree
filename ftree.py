#!/usr/bin/python3

from datetime import datetime
import argparse
import pickle
import requests
import sys


def build_tree(tree, roots, depth):
    '''
        Expand a family tree

        tree -- existing tree to add to (can be empty)
        roots -- array of IDs of people to start at
        depth -- maximum # of new layers to add
    '''

    queue = list()  # queue of IDs to look at
    queue.extend(roots)

    for d in range(depth):
        nextq = list()

        for qid in queue:
            if qid in tree:
                continue
            info = get_info(qid)
            tree[qid] = info
            for p in ['father', 'mother']:
                if info[p] and not info[p] in tree:
                    nextq.append(info[p])

        queue = nextq

        print('{}: {} nodes, {} in queue'.format(d + 1, len(tree), len(queue)))

    return queue


def get_info(qid):
    '''Get data about someone from Wikidata. Unknown fields set to None.'''

    data = fetch_data(qid)

    # Wikidata dates are hard to parse: if only the year 1273 is known, then
    # the date provided would be +1273-00-00T00:00:00Z, which isn't a valid
    # ISO 8601 string. Hence this kludge:
    get_year = lambda x: int(x[1:].split('-')[0])

    # (Wikidata property ID, field name, post-processing function)
    properties = [
        (21, 'gender', lambda x: {6581097: 'm', 6581072: 'f'}.get(x, '?')),
        (22, 'father', None),
        (25, 'mother', None),
        (26, 'spouse', None),
        (19, 'place_of_birth', fetch_label),
        (20, 'place_of_death', fetch_label),
        (569, 'date_of_birth', get_year),
        (570, 'date_of_death', get_year),
    ]

    info = dict()
    info['id'] = qid

    # sometimes there's no English label
    if 'en' in data['labels']:
        info['name'] = data['labels']['en']['value']
    else:
        info['name'] = '?'

    for pkey, label, func in properties:
        prop = get_prop(data, pkey)
        if func and prop:
            prop = func(prop)
        info[label] = prop

    return info


def get_prop(data, prop):
    '''Get the property P{prop} of an object, or None if it's missing'''

    prop = 'P' + str(prop)
    if prop in data['claims']:
        snak = data['claims'][prop][0]['mainsnak']
        if snak['snaktype'] != 'value':
            return None

        val = snak['datavalue']
        if val['type'] == 'wikibase-entityid':
            return val['value']['numeric-id']
        elif val['type'] == 'time':
            return val['value']['time']
        else:
            return None
    else:
        return None


def fetch_data(qid, props='labels|claims'):
    '''Get the data for Wikidata object Q{qid}'''

    params = {
        'action': 'wbgetentities',
        'ids': 'Q' + str(qid),
        'languages': 'en',
        'props': props,
        'format': 'json',
    }

    r = requests.get('https://www.wikidata.org/w/api.php', params)
    r.raise_for_status()
    json = r.json()
    return json['entities']['Q' + str(qid)]


def fetch_label(qid):
    '''Just get something's name without all the other data'''

    if qid in label_cache:
        return label_cache[qid]
    else:
        data = fetch_data(qid, 'labels')['labels']
        label = data['en']['value'] if 'en' in data else None
        label_cache[qid] = label
        return label

label_cache = dict()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='path to saved tree file')
    parser.add_argument('-o', '--output', help='path to save new tree file')
    parser.add_argument(
        '-d', '--depth', help='number of layers to add (default: 4)', type=int, default=4)
    parser.add_argument(
        '-r', '--roots', help='people to start at, by Wikidata ID', type=int, nargs='+')
    args = parser.parse_args()

    tree = {}
    queue = []

    if args.input:
        try:
            with open(args.input, 'rb') as fp:
                tree, queue = pickle.load(fp)
        except Exception as e:
            print(str(e))
            sys.exit(1)

        print('Loaded from \'{}\': {} nodes, {} in queue'.format(
            args.input, len(tree), len(queue)))
    else:
        print('Creating new empty tree')

    if args.roots:
        queue.extend(args.roots)

    queue = build_tree(tree, queue, args.depth)

    if args.output:
        try:
            with open(args.output, 'wb') as fp:
                pickle.dump((tree, queue), fp)
        except Exception as e:
            print(str(e))
            sys.exit(1)

        print('Saved to \'{}\''.format(args.output))

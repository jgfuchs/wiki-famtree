#!/usr/bin/python3

import argparse
import json
import requests
from datetime import datetime


def build_tree(tree, roots, depth):
    '''
        Expand a family tree

        tree -- existing tree to add to (can be empty)
        roots -- IDs of people to start at
        depth -- maximum # of new layers to add
    '''

    queue = list()  # queue of IDs to look at
    queue.extend(roots)

    for _ in range(depth):
        nextq = list()

        for qid in queue:
            info = get_info(qid)
            tree[qid] = info
            for p in ['father', 'mother']:
                if info[p] and not p in tree:
                    nextq.append(info[p])

        queue = nextq

    return queue


def get_info(qid):
    '''Get data about someone from Wikidata. Any unknown fields set to None.'''

    data = fetch_data(qid)

    # Wikidata dates are hard to parse: if just the year 1273 is known, then
    # the date provided would be +1273-00-00T00:00:00Z, which isn't a valid
    # ISO 8601 string. Hence this kludge:
    get_year = lambda x: int(x.split('-')[0])

    # (Wikidata property ID, , post-processing function)
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
    info['name'] = data['labels']['en']['value']
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
        val = data['claims'][prop][0]['mainsnak']['datavalue']
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


label_cache = dict()


def fetch_label(qid):
    '''Just get something's name without all the other data'''

    if qid in label_cache:
        return label_cache[qid]
    else:
        label = fetch_data(qid, 'labels')['labels']['en']['value']
        label_cache[qid] = label
        return label

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
        with open(args.input, 'r') as fp:
            data = json.load(fp)
            tree = data['tree']
            queue = data['queue']
        print('Loaded tree from \'{}\': {} nodes, {} in queue'.format(
            args.input, len(tree), len(queue)))
    else:
        print('Creating new empty tree')

    if args.roots:
        queue.extend(args.roots)

    queue = build_tree(tree, queue, args.depth)

    if not args.output:
        args.output = 'tree-{}.json'.format(int(time.time()))

    with open(args.output, 'w') as fp:
        data = {'tree': tree, 'queue': queue}
        json.dump(data, fp)

    print('Saved tree to \'{}\''.format(args.output))

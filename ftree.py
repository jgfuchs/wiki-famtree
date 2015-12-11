#!/usr/bin/python3

import argparse
import json
import requests
import time


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='path to saved tree file')
    parser.add_argument('-o', '--output', help='path to save new tree file')
    parser.add_argument(
        '-d', '--depth', help='number of layers to add (default: 4)', type=int, default=4)
    parser.add_argument(
        '-r', '--roots', help='IDs of people to start at', type=int, nargs='+')
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

    properties = [
        (21, 'gender'),
        (22, 'father'),
        (25, 'mother'),
        (26, 'spouse'),
        # (39, 'position'),
        # (19, 'place_of_birth'),
        # (20, 'place_of_death'),
        # (569, 'date_of_birth'),
        # (570, 'date_of_death'),
    ]

    info = dict()
    info['id'] = qid
    info['name'] = data['labels']['en']['value']
    for pkey, label in properties:
        info[label] = get_prop(data, pkey)

    # convert the IDs for male and female into more useful strings
    if info['gender']:
        info['gender'] = {6581097: 'm', 6581072: 'f'}.get(info['gender'], '?')

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


def fetch_label(qid):
    '''Just get something's name without all the other data'''
    return fetch_data(qid, 'labels')['labels']['en']['value']


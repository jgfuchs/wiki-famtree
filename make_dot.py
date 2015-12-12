#!/usr/bin/python3

import pickle
import sys
import textwrap


def get_tooltip(node):
    get = lambda x: node[x] if node[x] else '?'
    fields = ['date_of_birth', 'place_of_birth',
              'date_of_death', 'place_of_death']
    return '{}, {} – {}, {}'.format(*[get(f) for f in fields])


if len(sys.argv) != 2:
    print('Usage: {} <filename>'.format(sys.argv[0]))
    sys.exit(1)

tree = {}

try:
    with open(sys.argv[1], 'rb') as fp:
        tree, _ = pickle.load(fp)
except Exception as e:
    print(str(e))
    sys.exit(1)

fp = open(sys.argv[1] + '.dot', 'wt')
fp.write('digraph tree {\n')
fp.write('''
    // nodesep=0.1
    rankdir=RL
    node [shape=box]
''')

for qid in tree:
    node = tree[qid]

    attrs = {
        'label': textwrap.fill(node['name'], width=24),
        'URL': 'https://www.wikidata.org/wiki/Q{}'.format(qid),
        'tooltip': get_tooltip(node),
    }

    attr_string = ', '.join(('{}="{}"'.format(k, v) for k, v in attrs.items()))
    fp.write('\tN{} [{}]\n'.format(qid, attr_string))

    # draw edge from parents, if they're in tree
    for p in ['father', 'mother']:
        if node[p] and node[p] in tree:
            fp.write('\tN{} -> N{}\n'.format(node[p], qid))

fp.write('}\n')

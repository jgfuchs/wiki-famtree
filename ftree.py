#!/usr/bin/python
# -*- coding: utf-8 -*-

import time

import networkx as nx
import matplotlib.pyplot as plt

from wiki_utils import *

def get_info(title):
	'''
		get name and relations from given article

		always returns the name, but the other values may not be included
		if the article doesn't have them
	'''
	
	# get (title, section) 0 text
	ret = get_section0(title)
	if ret is None: return None
	title, text = ret
	
	result = {'name': title}
	
	# get dict of royalty/nobility infobox
	infobox = parse_template(text, ['Infobox royalty', 'Infobox nobility', 'Infobox monarch'])
	if infobox is None:	
		return result		# can't find any children or relations
	
	# get geneological information, if available
	for prop in ['father', 'mother', 'spouse']:
		if prop in infobox:
			values = get_links(infobox[prop])
			if len(values):
				result[prop] = values[0]
		
	if 'issue' in infobox:
		children = get_links(infobox['issue'])
		
		# filter out stupid links that sometimes sneak in
		blacklist = ['illegitimate']
		children = filter(lambda c: c not in blacklist, children)
		
		result['children'] = children
		
	return result

# depth-first search
def dfs(G, name, depth):
	if depth > 9: return
	
	info = get_info(name)
	if info is None:
		return
	
	if depth == 0:
		G.add_node(info['name'])
		
	if name != info['name']:
		nx.relabel_nodes(G, {name: info['name']}, copy=False)
	
	print '  ' * depth + info['name']
	
	time.sleep(0.5)
	
	if 'father' in info:
		G.add_edge(info['name'], info['father'])
		dfs(G, info['father'], depth + 1)

	
	if 'mother' in info:
		G.add_edge(info['name'], info['mother'])
		dfs(G, info['mother'], depth + 1)


if __name__ == '__main__':
	G = nx.DiGraph()
	dfs(G, 'Elizabeth II', 0)

	H = nx.convert_node_labels_to_integers(G, label_attribute="label")

	A = nx.to_agraph(H)
	A.layout()
	A.write('out.dot')
	

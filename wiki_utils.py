# -*- coding: utf-8 -*-

import requests, re

def make_wiki_url(title):
	return 'https://en.wikipedia.org/wiki/{}'.format(title)

def get_section0(title):
	"""
		fetch the content of section 0 (i.e., the top) of any page
		also returns the page's title, in case the given name was a redirect
	"""
	
	params = {
		"format": "json",
		"action": "query",
		"prop": "revisions",
		"rvprop": "content",
		"rvsection": "0",
		"redirects": "true",
		"titles": title
	}

	r = requests.get('https://en.wikipedia.org/w/api.php', params=params)
	
	pages = r.json()['query']['pages']	# array of page id=>page info
	pageid = int(pages.keys()[0])		# but we only requested one page
	if pageid <= 0:						# something went wrong
		return None

	page = pages[str(pageid)]
	title = page['title']
	text = page['revisions'][0]['*']	# only queried the most recent revision

	return (title, text)

def parse_template(text, names):
	"""
		finds the first tranclusion of any template with name in names
		returns a dict of of the parameters
	"""
	
	start = -1
	
	for n in names:
		m = re.search(r'{{\s*%s' % n, text, re.I)
		if m:
			start = m.start(0)
			break
	
	if start == -1:		# doesn't appear in text
		return None

	tokens = []		# each token is the string between depth-1 pipes
	
	depth = 0		# how many nested [[ and {{ we are (1 = just inside template)
	cur = start		# current position
	last = start		# last cut position
	while True:
		if text[cur] == '|':
			if depth == 1:
				tokens.append(text[last:cur])	# don't include this pipe
				last = cur+1					# or the previous
				
		if text[cur:cur+2] in ['[[', '{{']:
			depth += 1
			cur += 2
		elif text[cur:cur+2] in [']]', '}}']:
			depth -= 1
			cur += 2
		else:
			cur += 1
		
		if depth == 0:	# reached the closing }} of the template
			break

	tokens.pop(0)	# get rid of template name
	
	result = {}
		
	for tok in tokens:
		s = tok.split("=", 1)
		key = s[0].rstrip().lstrip()
		if len(key):
			if len(s) == 2:
				value = s[1].lstrip().rstrip()
				if len(value):
					result[key] = value
			else:
				result[key] = ""
	
	return result

def get_links(text):
	"""
		returns list of all links in given wikitext
		extracts only A from [[A|B]]
	"""
	
	rawlinks = re.findall(r'\[\[.*?\]\]', text)

	links = []
	for l in rawlinks:
		m = re.search(r'\[\[(.*?)(\|.*)?\]\]', l)
		links.append(m.group(1))

	return links


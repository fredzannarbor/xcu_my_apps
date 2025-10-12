from scholarly import ProxyGenerator
from scholarly import scholarly

# Set up a ProxyGenerator object to use free proxies
# This needs to be done only once per session
pg = ProxyGenerator()
pg.FreeProxies()
scholarly.use_proxy(pg)

# Now search Google Scholar from behind a proxy
# Get an iterator for the author results
search_query = scholarly.search_author('Robert Chen')
scholarly.pprint(next(search_query))
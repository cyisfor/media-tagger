from bs4 import BeautifulSoup as BeautifulSoupSucks,FeatureNotFound

pypysux = False
def BeautifulSoup(inp):
    global pypysux
    if pypysux:
        return BeautifulSoupSucks(inp,'html.parser')
    try: return BeautifulSoupSucks(inp,'lxml')
    except FeatureNotFound:
        pypysux = True
        return BeautifulSoup(inp)
        

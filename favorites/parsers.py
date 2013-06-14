from things import Tag
import danbooru
import derpibooru
import furaffinity
import inkbunny
import rule34
import sofurry
import weasyl
import pixiv
import flickr
import zerochan
import parseBase as parse
import re

parse.registerFinder("www.zerochan.net",
        {'extract': zerochan.extract})

parse.registerFinder("furry.booru.org",
        {'extract': danbooru.extract,
         'tags': [Tag('booru','furry')]})

parse.registerFinder(re.compile("wildcritters\..*"),
        {'extract': danbooru.extract,
         'tags': ['wildcritters'],
         'normalize': danbooru.normalize},
        name="wildcritters")

parse.registerFinder(re.compile("e621\..*"),
        {'extract': danbooru.extract,
         'tags': ['e621'],
         'normalize': danbooru.normalize},
        name="e621")

parse.registerFinder("mspabooru.com",
        {'extract': danbooru.extract,
         'tags': ['mspaint'],
         'normalize': danbooru.normalize})

parse.registerFinder(re.compile("twentypercentcooler\..*"),
        {'extract': danbooru.extract,
         'tags': ['twentypercentcooler','pony'],
         'normalize': danbooru.normalize},
        name="twentypercentcooler")

parse.registerFinder(re.compile(".*furaffinity.net"),
        {'extract': furaffinity.extract,
         'tags': ['furaffinity'],
         'normalize': furaffinity.normalize},
        name="furaffinity")

parse.registerFinder(re.compile(".*inkbunny.net"),
        {'extract': inkbunny.extract,
         'tags': ['inkbunny']},
        name="inkbunny")

parse.registerFinder('rule34.xxx',
        {'extract': rule34.extract,
            'tags': ['rule34']})

parse.registerFinder(re.compile('.*sofurry.com'),
        {'extract': sofurry.extract,
            'tags': ['sofurry']},
        name="sofurry")

parse.registerFinder(re.compile('.*weasyl.com'),
        {'extract': weasyl.extract,
            'tags': ['weasyl']},
        name="weasyl")

parse.registerFinder('derpibooru.org',
        {'extract': derpibooru.extract,
            'normalize': derpibooru.normalize,
            'tags': ['derpibooru','pony']})

parse.registerFinder('derpiboo.ru',
        {'extract': derpibooru.extract,
            'normalize': derpibooru.normalize,
            'tags': ['derpibooru','pony']})

""" sigh...
parse.registerFinder('www.pixiv.net',
        {'extract': pixiv.extract,
            'tags':['pixiv','japan']})
"""

tags = ['flickr','photo']
parse.registerFinder('flickr.com',
        {'extract': flickr.extract,
            'tags':tags})
parse.registerFinder('www.flickr.com',
        {'extract': flickr.extract,
            'tags':tags})

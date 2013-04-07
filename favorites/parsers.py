import danbooru
import derpibooru
import furaffinity
import inkbunny
import rule34
import sofurry
import weasyl
import pixiv
import parseBase as parse
import re
parse.registerFinder(re.compile("wildcritters\..*"),
        {'extract': danbooru.extract,
         'tags': ['wildcritters'],
         'normalize': danbooru.normalize})

parse.registerFinder(re.compile("e621\..*"),
        {'extract': danbooru.extract,
         'tags': ['e621'],
         'normalize': danbooru.normalize})

parse.registerFinder("mspabooru.com",
        {'extract': danbooru.extract,
         'tags': ['mspaint'],
         'normalize': danbooru.normalize})

parse.registerFinder(re.compile("twentypercentcooler\..*"),
        {'extract': danbooru.extract,
         'tags': ['twentypercentcooler','pony'],
         'normalize': danbooru.normalize})

parse.registerFinder(re.compile(".*furaffinity.net"),
        {'extract': furaffinity.extract,
         'tags': ['furaffinity'],
         'normalize': furaffinity.normalize})

parse.registerFinder(re.compile(".*inkbunny.net"),
        {'extract': inkbunny.extract,
         'tags': ['inkbunny']})

parse.registerFinder('rule34.xxx',
        {'extract': rule34.extract,
            'tags': ['rule34']})

parse.registerFinder(re.compile('.*sofurry.com'),
        {'extract': sofurry.extract,
            'tags': ['sofurry']})

parse.registerFinder(re.compile('.*weasyl.com'),
        {'extract': weasyl.extract,
            'tags': ['weasyl']})

parse.registerFinder('derpibooru.org',
        {'extract': derpibooru.extract,
            'normalize': derpibooru.normalize,
            'tags': ['derpibooru','pony']})

parse.registerFinder('www.pixiv.net',
        {'extract': pixiv.extract,
            'tags':['pixiv','japan']})

def isGood(type):
    category = type.split('/',1)[0]
    return category in {'image','video','audio'} or type in {'application/x-shockwave-flash'}


class NoGood(Exception): pass

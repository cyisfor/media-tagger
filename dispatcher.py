import pages,info,process

modes = {
        'simple': (pages.simple,info.simple),
        'page': (pages.page,info.page),
        'info': (pages.info,info.info),
        'like': (pages.like,info.like),
        'user': (pages.user,info.user,process.user),
        'desktop': (pages.desktop,lambda path,params: path)
        }


def dispatch(mode,path,params):
    handler = modes[mode]
    return handler[0](handler[1](path,params),path,params)

def process(mode,path,params):
    handler = modes[mode]
    return handler[2](path,params)

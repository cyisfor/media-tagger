import pages,info

modes = {
        'page': (pages.page,info.page),
        'info': (pages.info,info.info),
        'like': (pages.like,info.like),
        'desktop': (pages.desktop,lambda i: i)
        }


def dispatch(mode,id,params):
    mode = modes[mode]
    return mode[0](mode[1](id),params)

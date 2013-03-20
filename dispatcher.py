import pages,info

modes = {
        'page': (pages.page,info.page),
        'info': (pages.info,info.info),
        'like': (pages.like,info.like)
        }


def dispatch(mode,id):
    mode = modes[mode]
    return mode[0](mode[1](id))

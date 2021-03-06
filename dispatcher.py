import pages,info,process,uploader,jsony
import randomDerp

modes = {
  'random': (randomDerp.page, randomDerp.info),
  'resized': (pages.resized,lambda path,params: None),
  'simple': (pages.simple,info.simple),
  'page': (pages.page,info.page),
  'info': (pages.info,info.info),
  'like': (pages.like,info.like),
  'user': (pages.user,
					 info.user,
					 process.user),
  'desktop': (pages.desktop,lambda path,params: path),
  'comic': (pages.showComic,(lambda *a: None)),
  'uploads': (uploader.page,
							(lambda path, params: (path, params)),
							uploader.post),
  'oembed': (pages.oembed, info.oembed),
	'direct': (pages.direct, info.simple)
}


def dispatch(json,mode,path,params):
    try:
        handler = modes[mode]
    except KeyError as e:
        raise KeyError("No handler for /~{}/".format(mode),e)

    if json:
        return getattr(jsony,mode)(handler[1](path,params),path,params)
    return handler[0](handler[1](path,params),path,params)

def process(mode,path,params,data):
    handler = modes[mode]
    return handler[2](path,params,data)

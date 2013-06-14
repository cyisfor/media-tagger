import user as derp

def user(path,params):
    params = dict(params)
    rescale = params.get('rescale')
    if rescale:
        rescale = rescale[0]
        if rescale:
            rescale = True
        else:
            rescale = False
    else:
        rescale = False
    news = {'rescaleimages': rescale}
    derp.set(news.items())
    return ""

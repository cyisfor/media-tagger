from override import override

import tornado.concurrent

@override(tornado.concurrent.Future,'_set_done')
def _set_done(self, superduper):
    try: return superduper(self)
    except TypeError:
        print('ugh bad future')

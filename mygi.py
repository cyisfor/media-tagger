try: import gi.repository
except ImportError:
    import pgi
    pgi.install_as_gi()
    import gi.repository

import sys
sys.modules[__name__] = gi.repository

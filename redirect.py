class Redirect(Exception):
    def __init__(self,where,code=301):
        self.where = where
        self.code = code

class Refresh(Exception):
    def __init__(self,delay,document):
        self.document = document
        self.delay = delay

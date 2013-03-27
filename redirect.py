class Redirect(Exception):
    def __init__(self,where,code=301):
        self.where = where
        self.code = code

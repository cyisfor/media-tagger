class Redirect(Exception):
    def __init__(self,location,code=302,message='boink'):
        self.code = code
        self.message = message
        self.location = location
    def __str__(self):
        return '<Redirect '+self.code+' '+self.location+'>'

class Refresh(Exception):
    def __init__(self,delay,document):
        self.document = document
        self.delay = delay

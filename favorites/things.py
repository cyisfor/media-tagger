class Media:
    def __init__(self,url,headers={}):
        self.url = url
        self.headers = headers

Image = Media

class Tag:
    def __init__(self,category,name):
        self.category = category
        self.name = name
    def __str__(self):
        return self.category + ':' + self.name
    def __repr__(self):
        return 'Tag('+repr(self.category)+','+repr(self.name)+')'
    def __hash__(self):
        return hash(self.category)^hash(self.name)
    def __eq__(self,other):
        return self.category == other.category and self.name == other.name
class Source(str): pass
class Name(str): pass

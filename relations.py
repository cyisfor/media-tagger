class Tables:
    def __init__(self,red,blue):
        self.red = red
        self.blue = blue
        if red == 'people':
            self.singular = 'person'
        elif red == 'media':
            self.singular = 'medium'
        else:
            assert(red[-1] == 's')
            self.singular = red[:-1]

class DT(Tables):
    def __init__(self,red,blue):
        self.selector = red+'.id FROM '+red+' WHERE '+red+'.name = '
        super().__init__(red,blue)

Drew = Tables('artists','media')
Drew.selector = 'artists.id FROM artists INNER JOIN people ON people.id = artists.id WHERE\n    people.name = '

tables = {
    'describes': DT('tags','media'),
    'drew': Drew,
    'portrays': DT('people','media'),
    'performsin': DT('acts','media'),
    'contains': DT('things','media'),
    'references': DT('verses','media')
}

summary = {'describes','drew','portrays','performsin','contains','references'}
info = summary + {'acquiredfrom','uploaded'}
user = {'wantstags','uploaded','webmasters','visited'}
everything = info + user

lookupSpecial = {
    'performsin': 'ROW(acts.id,acts.name,acts.sexiness)::derp2'
}

def lookup(medium,relations):
    s = None
    oppositeday = False
    relations.sort(key=lambda pair: pair[0] is False)
    idents = []
    for nega,relation,ident in relations:
        ts = tables.get(relation)        
        idents.append(ident)
        if s is None:
            if nega:
                # no positags to counteract these
                s = 'SELECT * from media\n    WHERE id NOT IN (\n'
                oppositeday = True
            else:
                s = 'SELECT * from media\n    WHERE id IN (\n'
        else:
            if oppositeday:
                s += 'UNION\n'
            elif nega:
                s += 'EXCEPT\n'
            else:
                s += 'INTERSECT\n'
        s += '-- '+relation
        if not ts:
            s += ' (no special relation known):\n    SELECT medium FROM r.describes WHERE\n    tag = (SELECT tags.id FROM tags WHERE tags.name = $'+str(len(idents)+1)+')\n'
        else:
            s += ':\n    SELECT medium FROM r.'+relation+' WHERE\n    '+ts.singular+' = (SELECT '+
                ts.selector+'$'+str(len(idents)+1)+')\n'





        s += 'array(SELECT '+selector+'\n    FROM '+ts[0]+'\n'+
        # argh, but how to artists / people join?
            '\n        INNER JOIN r.'+relation+' ON '+ts[0]+'.id  = r.'+relation+'.'+singular(ts[0])+
            '\n    WHERE r.'+relation+'.'+singular(ts[0])+' = '+ts[0]+'.id)'


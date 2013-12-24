from db import cursor
import schema
import create
images = {}
tags = {}

with cursor() as c:
    for name in ('ferret in tube.gif',
        'another ferret in tube.gif',
        'ferret mid jump.jpg',
        'ferretspin.gif',
        'horse in tube.gif'):
        images[name] = create.image(c,name)

    for name in ('ferret','species','species:ferret','species:horse','tube','animated'):
        tags[name] = create.tag(c,name)

    for pair in (('species:ferret','ferret'),
            ('species:ferret','species'),
            ('species:horse','species')):
        create.connect(c,*(tags[name] for name in pair))

    for pair in (('ferret','another ferret in tube.gif'),
            ('ferret','ferret mid jump.jpg'),
            ('species:ferret','ferret in tube.gif'),
            ('species:ferret','ferretspin.gif'),
            ('species:horse','horse in tube.gif'),
            ('animated','horse in tube.gif'),
            ('animated','ferretspin.gif'),
            ('animated','ferret in tube.gif'),
            ('animated','another ferret in tube.gif'),
            ('tube','horse in tube.gif'),
            ('tube','ferret in tube.gif'),
            ('tube','another ferret in tube.gif')):
        create.connect(c,tags[pair[0]],images[pair[1]])

    image = create.image(c,"ferret tubes1.jpg")
    for name in ('species:ferret','tube'):
        create.connect(c,tags[name],image)

    image = create.image(c,"ferret tubes2.jpg")
    for name in ('ferret','tube'):
        create.connect(c,tags[name],image)

    harness = create.tag(c,'harness')

    create.connect(c,harness,image)

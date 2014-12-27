sources = {
    'e621': 'https://e621.net/',
    'furaffinity': 'http://furaffinity.net/',
    'laptop': 'local://laptop/',
    'pixiv': 'https://pixiv.net/',
}
organisms = {
    'pony','fox','human','cat','ferret','eeveelution','unicorn',',dragon','pegasus','dog',
    'wolf','rabbit','tree','weasels','grass','wood','apple','synx','alicorn',
    'earth pony','otter','flower','skunk','squirrel','umbreon','weasel','raccoon',
    'pikachu','tiger','mouse','bear','leafeon','bat',
}
parts = {
    'penis','breasts','pussy','hair','wings','horn','tail','tongue','balls',
    'anus','butt','nipples','blonde hair','paws','long hair','fur','animal','claws',
    'hindpaws','closed eyes','blood','sweat','pussy juice','pawpads','vagina','bird',
    'chest tuft','hindpaw','teeth','horns','big breasts','clitoris',
    'saliva','hooves','drool','fangs',
}

clothing = {
    'hat','clothing','glasses','collar','piercing','eyewear','clothes','underwear','shirt',
    'bow','panties','sex toy','crown','ear piercing','dress',
}

places = {
    'outside','sky','night','forest','clouds',
}

things = organisms + parts + clothing + {
    'dialogue','cutie mark','hat','tears','bed','net','video games','water','moon','weapon','tooth',
    'fire','book','comb','camera','snow','schwartz','pillow',
}

acts = {
    'incest': 2,
    'hug': 1,
    'on back': 2,
    'rape': 2,
    'kissing': 1,
    'crying': 0,
    'lying': 0,
    'reaction': -1,
    'raised tail': 1,
    'presenting': 2,
    'pose': 1,
    'fellatio': 2,
    'sleeping': -1,
    'spread': 1,
    'knot': 2,
    'tongue out': 1,
    'erection': 2,
    'looking back': 1,
    'cum in pussy': 2,
    'oral sex': 2,
    'standing': 0,
    'from behind': 1,
    'licking': 1,
    'orgasm': 3,
    'anal': 2,
    'blush': 1,
    'gay': 1,
    'sex': 2,
    'straight': 2,
    'vaginal': 3,
    'penetration': 3,
    'open mouth': 0,
    'vaginal penetration': 3,
    'looking at viewer': 1,
    'eyes closed': 0,
    'smile': -1,
    'oral': 2,
    'transformation': 1,
    'what': 0,
    'sitting': 0,
    'interspecies': 1,
    'lying': 0,
    'spreading': 2,
    'spread legs': 2,
    'cum inside': 3,
}

for colors in {'red','orange','yellow','green','cyan','blue','purple','violet','magenta','pink','multi-colored'}:
    upgrade['things'].add(color+' hair')
    upgrade['things'].add(color+' eyes')


def circular(root):
    if not hasattr(root,'children'):
        raise RuntimeException("huh");
    higher = set()
    events = []
    def doit(root):
        print('doing',repr(root))
        higher.add(id(root))
        for child in root.flat_children:
            print('child',repr(child))
            if id(child) in higher:
                raise RuntimeError('appears twice!',child)
            if hasattr(child,'children'):
                events.append((doit,child))
        higher.remove(id(root))
        # don't care if same node appears in two different branches
    doit(root)
    while events:
        print('doing event')
        event = events.pop()
        event[0](event[1])
#    raise SystemExit;

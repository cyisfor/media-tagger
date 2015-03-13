def circular(root):
    higher = set()
    def doit(root):
        higher.add(root)
        for child in root.children:
            if id(child) in higher:
                raise RuntimeException('appears twice!',child)
            doit(child)
        higher.remove(root)
        # don't care if same node appears in two different branches
    doit(root)

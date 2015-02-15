def schlorp(name,text=True):
    with open(name,"rt" if text else "rb") as inp:
        return inp.read()

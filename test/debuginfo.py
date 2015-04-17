def derp():
    try:
        raise Exception
    except Exception as e:
        tb = e.__traceback__

    while tb.tb_next:
        tb = tb.tb_next
    f = tb.tb_frame.f_back
    for n,v in f.f_globals.items():
        print(n,v)

derp()

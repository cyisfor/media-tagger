from imagecheck import NoGood,isGood

import note

import textwrap

def manuallyGet(data,badtype):
    note("What is {}?".format(badtype))
    bit = data.read(0x100)
    bit = textwrap.fill(repr(bit))
    
    def getByTTY():
        import os
        if not os.isatty(sys.stdin.fileno()): return False
        try:
            print(path)
            print("What type is that?")
            while True:
                type = input()
                if '/' in type:
                    return type
                else:
                    print('not sure what type is '+type)
        except KeyboardInterrupt:
                raise NoGood("User wouldn't enter a good type for",badtype,type)
    
    
    def getByGUI():
        from gi.repository import Gtk
        ok,eh = Gtk.init_check()
        if not ok: return False
            
        win = Gtk.Window()
        vbox = Gtk.Box(Gtk.Orientation.VERTICAL)
        win.add(vbox)
        def lbl(s):
            vbox.pack_start(Gtk.Label(s),True,True,2)
        lbl(bit)
        lbl(path)
        lbl("What type is that?")
        ent = Gtk.Entry()
        vbox.pack_start(ent,True,True,2)
        btn = Gtk.Button.new_with_label("OK")
        fail = Gtk.Button.new_with_label("Fail")
        fail.connect('clicked',Gtk.main_quit)
        def yay(*a):
            nonlocal mimetype
            test = ent.get_text()
            if '/' in test:
                mimetype = test
                Gtk.main_quit()
            else:
                Gtk.MessageDialog(win,
                                  Gtk.DialogFlags.MODAL |
                                  Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                  Gtk.MessageType.ERROR,
                                  Gtk.ButtonsType.CLOSE,
                                  "The type "+repr(test)+" wasn't good.").show_all()
        ent.connect('activate',yay)
        btn.connect('clicked',yay)
        win.show_all()
        Gtk.main()
        return True
    if not ( getByGUI() or getByTTY() ):
        raise NoGood("Couldn't find a way to manually get the type.",badtype,bit);
        
    
                                          
                    

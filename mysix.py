import six
if six.PY2:
    def textreader(inp=None, encoding='utf-8'):
        if inp is None:
            import sys
            inp = sys.stdin
        if isinstance(inp, io.RawIOBase):
            buffer = io.BufferedIOBase(inp)
        else:
            # This is to handle passed objects that aren't in the
            # IOBase hierarchy, but just have a write method
            buffer = io.BufferedIOBase()
            buffer.readable = lambda: True
            buffer.read = inp.read
            try:
                # TextIOWrapper uses this methods to determine
                # if BOM (for UTF-16, etc) should be added
                buffer.seekable = inp.seekable
                buffer.tell = inp.tell
            except AttributeError:
                pass
        # wrap a binary writer with TextIOWrapper
        class UnbufferedTextIOWrapper(io.TextIOWrapper):
            def write(self, s):
                super(UnbufferedTextIOWrapper, self).write(s)
                self.flush()
        return UnbufferedTextIOWrapper(buffer, encoding=encoding,
                                       errors='xmlcharrefreplace',
                                       newline='\n')
    

            
    def textwriter(out=None, encoding='utf-8'):
        if out is None:
            import sys
            out = sys.stdout
    
        if isinstance(out, io.RawIOBase):
            buffer = io.BufferedIOBase(out)
        else:
            # This is to handle passed objects that aren't in the
            # IOBase hierarchy, but just have a write method
            buffer = io.BufferedIOBase()
            buffer.writable = lambda: True
            buffer.write = out.write
            try:
                # TextIOWrapper uses this methods to determine
                # if BOM (for UTF-16, etc) should be added
                buffer.seekable = out.seekable
                buffer.tell = out.tell
            except AttributeError:
                pass
        # wrap a binary writer with TextIOWrapper
        class UnbufferedTextIOWrapper(io.TextIOWrapper):
            def write(self, s):
                super(UnbufferedTextIOWrapper, self).write(s)
                self.flush()
        return UnbufferedTextIOWrapper(buffer, encoding=encoding,
                                       errors='xmlcharrefreplace',
                                       newline='\n')
    

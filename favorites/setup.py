#!/usr/bin/env python
from distutils.core import setup
from distutils.extension import Extension
import subprocess as s

s.call(['make'])

def pkgconfig(*packages, **kw):
	flag_map = {'-I': 'include_dirs', '-L': 'library_dirs', '-l': 'libraries'}
	for token in s.run(("pkg-config","--libs","--cflags")+packages
					   ,stdout=s.PIPE).stdout.split():
		token = token.decode('utf-8')
		if token[:2] in flag_map:
			kw.setdefault(flag_map.get(token[:2]), []).append(token[2:])
	return kw


setup(name = 'FU',
	  ext_modules=[Extension('_parseui',
							 sources = ['parseui.c',
							            'squeetie.png.gen.c',
							            'sweetie_thinking.gif.gen.c',
							            "parseui.xml.gen.c",
							 ],
							 **pkgconfig("gtk+-3.0"))])

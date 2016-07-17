all: cify squeetie.png.gen.c sweetie_thinking.gif.gen.c parseui.xml.gen.c

cify: cify.c

%.gen.c: % cify
	./cify $(firstword $(subst ., ,$*)) <$< source.temp header.temp
	mv header.temp $*.h
	mv source.temp $@

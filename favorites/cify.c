int main(int argc, char *argv[])
{
	assert(argc==2);
	struct stat info;
	assert(0==fstat(STDIN_FILENO,&info));
	char* name = argv[1];
	WRITELIT("size_t ");
	write(STDOUT_FILENO,name,namelen);
	WRITELIT("_size = ");
	char buf[0x100];	
	write(STDOUT_FILENO, buf,
				snprintf(buf,0x100,"%ld",info.st_size));
	WRITELIT("L;\n"
					 "char ");
	write(STDOUT_FILENO,name,namelen);
	WRITELIT("[] = \n\\");
	void* data = mmap(VOID, info.st_size, PROT_READ, MAP_SHARED, STDIN_FILENO, 0);
	assert(data != FAILED);
	char* c = (char*) data;
	for(i=0;i<info.st_size;++i, ++c) {
		if(i && i % 40 == 0) {
			WRITELIT("\"\n\"");
		}
#define ESCAPE(c,r) if(*c == c) {								 \
			write(STDOUT_FILENO, "\\" r, sizeof(r));	 \
			continue; \
		}
		ESCAPE('\\',"\\");
		ESCAPE('"',"\"");
		ESCAPE('\n',"n");
		ESCAPE('\r',"r");
		ESCAPE('\a',"a");
		if(!isprint(*c)) {
			write(STDOUT_FILENO, "\\x", 2);
		} else {
			write(STDOUT_FILENO, &c, 1);
		}
	}

	return 0;
}

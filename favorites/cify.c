#include <unistd.h> // write
#include <sys/stat.h>
#include <assert.h>
#include <string.h> // strlen
#include <sys/mman.h> // mmap stuff
#include <stdio.h> // snprintf sigh
#include <ctype.h> // isprint
#include <fcntl.h> // open, O_WRONLY

#define WRITELIT(lit) write(out, lit, sizeof(lit)-1);
#define WRITE(s,len) write(out, s, len)

int main(int argc, char *argv[])
{
	assert(argc==4);
	struct stat info;
	assert(0==fstat(STDIN_FILENO,&info));
	char* name = argv[1];
	int out = open(argv[2], O_WRONLY|O_CREAT|O_TRUNC, 0644);
	ssize_t namelen = strlen(name);
	WRITELIT("unsigned long int ");
	WRITE(name,namelen);
	WRITELIT("_size = ");
	char numbuf[0x100];
	ssize_t numsize = snprintf(numbuf,0x100,"%ld",info.st_size);
	WRITE(numbuf,
				numsize);
	WRITELIT("L;\n"
					 "unsigned char ");
	WRITE(name,namelen);
	WRITELIT("[");
	WRITE(numbuf, numsize);
	WRITELIT("L] = \n\"");
	void* data = mmap(NULL, info.st_size, PROT_READ, MAP_SHARED, STDIN_FILENO, 0);
	assert(data != MAP_FAILED);
	unsigned char* c = (unsigned char*) data;
	int i;
	int width = 0;
	for(i=0;i<info.st_size;++i, ++c) {
		if(width > 72) {
			width = 0;
			WRITELIT("\"\n\"");
		}
/*		WRITE(buf,
					snprintf(buf,0x100,"\n%x - %c\n",*c,*c)); */
#define ESCAPE(test,r) if(*c == test) {								 \
			WRITE( "\\" r, sizeof(r));	 \
			width += 2; \
			continue; \
		}
		ESCAPE('\\',"\\");
		ESCAPE(0,"0");
		ESCAPE(1,"1");
		ESCAPE('"',"\"");
		ESCAPE('\t',"t");
		ESCAPE('\n',"n");
		ESCAPE('\r',"r");
		ESCAPE('\a',"a");
		if(!isprint(*c)) {
			char oct[0x10] = "01234567";
			WRITE( "\\", 1);
			WRITE( &oct[(*c >> 6) & 7], 1);
			WRITE( &oct[(*c >> 3) & 7], 1);
			WRITE( &oct[*c & 7], 1);
			width += 4;
		} else {
//			WRITELIT("boop\n");
			WRITE( c, 1);
			++width;
		}
	}
	WRITELIT("\";\n");
	close(out);

	out = open(argv[3], O_WRONLY|O_CREAT|O_TRUNC, 0644);
	assert(out > 0);
	WRITELIT("extern unsigned long int ");
	WRITE(name,namelen);
	WRITELIT("_size;\nextern unsigned char ");
	WRITE(name,namelen);
	WRITELIT("[");
	WRITE(numbuf, numsize);
	WRITELIT("];\n");
	return 0;
}

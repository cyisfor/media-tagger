#include <unistd.h> // write
#include <sys/stat.h>
#include <assert.h>
#include <string.h> // strlen
#include <sys/mman.h> // mmap stuff
#include <stdio.h> // snprintf sigh
#include <ctype.h> // isprint

#define WRITELIT(lit) write(STDOUT_FILENO, lit, sizeof(lit)-1);


int main(int argc, char *argv[])
{
	assert(argc==2);
	struct stat info;
	assert(0==fstat(STDIN_FILENO,&info));
	char* name = argv[1];
	ssize_t namelen = strlen(name);
	WRITELIT("unsigned long int ");
	write(STDOUT_FILENO,name,namelen);
	WRITELIT("_size = ");
	char buf[0x100];
	ssize_t numsize = snprintf(buf,0x100,"%ld",info.st_size);
	write(STDOUT_FILENO, buf,
				numsize);
	WRITELIT("L;\n"
					 "unsigned char ");
	write(STDOUT_FILENO,name,namelen);
	WRITELIT("[");
	write(STDOUT_FILENO, buf, numsize);
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
/*		write(STDOUT_FILENO,buf,
					snprintf(buf,0x100,"\n%x - %c\n",*c,*c)); */
#define ESCAPE(test,r) if(*c == test) {								 \
			write(STDOUT_FILENO, "\\" r, sizeof(r));	 \
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
			write(STDOUT_FILENO, "\\", 1);
			write(STDOUT_FILENO, &oct[(*c >> 6) & 7], 1);
			write(STDOUT_FILENO, &oct[(*c >> 3) & 7], 1);
			write(STDOUT_FILENO, &oct[*c & 7], 1);
			width += 4;
		} else {
//			WRITELIT("boop\n");
			write(STDOUT_FILENO, c, 1);
			++width;
		}
	}
	WRITELIT("\";\n");

	return 0;
}

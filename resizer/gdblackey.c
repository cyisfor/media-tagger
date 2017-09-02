#include <stdlib.h> // PATH_MAX

int main(int argc, char *argv[])
{
	char real[PATH_MAX];
	size_t len = strlen(argv[0]);
	memcpy(real,argv[0],len);
	memcpy(real+len,"-real",6);
	execlp("gdbserver","gdbserver",real,NULL);
	return 0;
}

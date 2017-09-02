#include <limits.h> // PATH_MAX
#include <stdlib.h> // NULL

int main(int argc, char *argv[])
{
	char real[PATH_MAX];
	size_t len = strlen(argv[0]);
	memcpy(real,argv[0],len);
	memcpy(real+len,"-real",6);
	setsid();
	execlp("gdbserver","gdbserver","--remote-debug","--debug","127.0.0.1:4411",real,NULL);
	return 0;
}

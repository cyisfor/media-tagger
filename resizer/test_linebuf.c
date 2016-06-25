#include "linebuf.h"

int main(void) {
	struct linebuf self;
	int fd = 0;
	while(linebuf_read(&self, fd)) {
		uv_buf_t dest;
		while(linebuf_next(&self, &dest)) {
			printf("line of length %d\n",dest.len);
			fwrite(dest.base,dest.len,1,stdout);
			putchar('\n');
		}
	}
}

#include <uv.h>
#include <stdbool.h>

struct linebuf;

bool linebuf_read(struct linebuf* self, int fd);
bool linebuf_next(struct linebuf* self, uv_buf_t* dest);

struct linebuf* linebuf_new(char delim);
void linebuf_free(struct linebuf** self);

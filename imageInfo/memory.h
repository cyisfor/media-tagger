#include <stdlib.h> // size_t

void memory_pushContext(void);
void memory_popContext(void);
void memory_finish(void); // or just exit the process

void* memory_alloc(size_t size);
void memory_free(void* buf); // use popContext to free all memory allocated
void* memory_realloc(void* buf, size_t size);

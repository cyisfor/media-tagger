#include <stdint.h>

void filedb_top(const char* newtop);
char* filedb_file(const char* category, const char* name);
char* filedb_path(const char* category, uint32_t id);


#include <stdint.h>
#include <stdbool.h>

struct message {
	uint32_t id:32;
	// 0 means don't resize, just make a default thumbnail
	uint32_t width:32;
} __attribute__((packed));

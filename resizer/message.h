#include <stdbool.h>

struct message {
	bool resize:1;
	union {
		struct {
			uint32_t id:31;
			uint32_t width:32;
		} resized;
		uint32_t id:31;
	};
} __attribute__((packed));

struct message {
	bool resize:1;
	union {
		struct {
			uint16_t id:7;
			uint16_t width:16;
		} resized:31;
		uint16_t id:7;
	}
} __attribute__((packed));

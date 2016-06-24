struct message {
	bool resize:1;
	union {
		struct {
			uint16_t id:7;
			uint16_t width:16;
		} resized;
		uint16_t id:7;
	};
} __attribute__((packed));

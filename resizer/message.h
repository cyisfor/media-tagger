struct message {
	bool resize:1;
	union {
		struct {
			uint16_t id:7;
			uint32_t width:32;
		} resized;
		uint16_t id:7;
	};
} __attribute__((packed));

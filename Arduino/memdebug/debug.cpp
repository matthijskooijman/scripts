// AVR / Arduino dynamic memory debugging code.

// Copyright 2014 Matthijs Kooijman <matthijs@stdin.nl>
//
// Permission is hereby granted, free of charge, to anyone obtaining a
// copy of this document and accompanying files, to do whatever they want
// with them without any restriction, including, but not limited to,
// copying, modification and redistribution.
//
// NO WARRANTY OF ANY KIND IS PROVIDED.

// To use this code, include this source file in the compilation (e.g. dump it
// into your sketch directory or a library that's included in the
// sketch). Furtherome, make sure you add the following options to the
// gcc command that performs the final link:
//
// -Wl,--wrap=malloc -Wl,--wrap=realloc -Wl,--wrap=free
//
// These options tell the linker to let all calls to malloc, realloc and
// free refer to the wrappers below instead (doing it like this, instead
// of using for example preprocessor macros, guarantees that _all_ calls
// are logged, including calls inside the standard library (e.g. inside
// strdup).
//
// On Arduino, these link options can be added in the
// hardware/arduino/avr/platform.txt file, in the
// recipe.c.combine.pattern line.
//
// Additionally, you should make sure that you initialize the Serial
// object as soon as possible in your sketch, certainly before
// malloc is called (otherwise you risk a deadlock by printing to a
// non-initialized Serial object).
//
// Along with every function call, the amount of free memory (see the
// comment for the memleft() function for what this value means exactly)
// and the return address is also printed (which can be matched to the
// disassembler output).

#include <Arduino.h>

extern "C" {

	/* Get available memory. This is the space between the heap and
	 * the stack, but does not include any unused memory inside the
	 * heap (e.g. memory allocated and freed again).
	 *
	 * When this value reaches 0, the stack will start overflowing
	 * the heap, even though memory might still be malloc'd. */
	static size_t memleft() {
		extern void *__brkval;
		extern int __heap_start;
		return SP - (size_t)(__brkval ?: &__heap_start);
	}

#ifndef __AVR_3_BYTE_PC__
	// On 2-byte PC processors, we can just use the builtin function
	// This returns a word address, not a byte address
	static inline uint16_t get_return_address() __attribute__((__always_inline__));
	static inline uint16_t get_return_address() { return (uint16_t)__builtin_return_address(0); }
#else
	// On 3-byte PC processors, the builtin doesn't work, so we'll
	// improvise
	// This returns a word address, not a byte address
	static inline uint32_t get_return_address() __attribute__((__always_inline__));
	static inline uint32_t get_return_address() {
		// Frame layout:
		// [RA0]
		// [RA1]
		// [RA2]
		// ... Variables ...
		// [empty] <-- SP

		// Find out how big the stack usage of the function
		// (into which we are inlined) is. It seems gcc won't
		// tell us, but we can trick the assembler into telling
		// us at runtime.
		uint8_t stack_usage;
		__asm__ __volatile__("ldi %0, .L__stack_usage" : "=r"(stack_usage));

		// Using the stack usage, we can find the top of the
		// frame (the byte below the return address)
		uint8_t *frame_top = (uint8_t*)SP + stack_usage;

		// And then read the return address
		return (uint32_t)frame_top[1] << 16 | (uint16_t)frame_top[2] << 8 | frame_top[3];
	}
#endif

	static bool in_realloc = false;

	void *__real_malloc(size_t n);
	void *__wrap_malloc(size_t n) {
		void *p = __real_malloc(n);
		// realloc calls malloc, so don't print in that case suppress those prints
		if (!in_realloc) {
			Serial.println();
			Serial.print("malloc(");
			Serial.print(n);
			Serial.print(") = 0x");
			Serial.println((uint16_t)p, HEX);
			Serial.print("free = ");
			Serial.println(memleft());
			Serial.print("caller = 0x");
			Serial.println(get_return_address() * 2, HEX);
			Serial.flush();
		}
		return p;
	}

	void *__real_realloc(void * p, size_t n);
	void *__wrap_realloc(void * p, size_t n) {
		in_realloc = true;
		void *newp = __real_realloc(p, n);
		in_realloc = false;

		Serial.println();
		Serial.print("realloc(0x");
		Serial.print((uint16_t)p, HEX);
		Serial.print(", ");
		Serial.print(n);
		Serial.print(") = 0x");
		Serial.println((uint16_t)newp, HEX);
		Serial.print("free = ");
		Serial.println(memleft());
		Serial.print("caller = 0x");
		Serial.println(get_return_address() * 2, HEX);
		Serial.flush();
		return newp;
	}

	void __real_free(void * p);
	void __wrap_free(void * p) {
		__real_free(p);
		// realloc calls free, so don't print in that case suppress those prints
		if (!in_realloc) {
			Serial.println();
			Serial.print("free(0x");
			Serial.print((uint16_t)p, HEX);
			Serial.println(")");
			Serial.print("free = ");
			Serial.println(memleft());
			Serial.print("caller = 0x");
			Serial.println(get_return_address() * 2, HEX);
			Serial.flush();
		}
	}
}

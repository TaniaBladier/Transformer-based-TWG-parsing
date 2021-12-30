/* Fast cross-platform bit counting using intrinsic functions
 *
 * This code is based on https://github.com/Noctune/bitcount
 * Adapted for 64-bit integers instead of 32 bits.
 */

#ifndef BITCOUNT_H_
#define BITCOUNT_H_

#ifdef __cplusplus
extern "C" {
#endif

#if !defined(BITCOUNT_NO_AUTODETECT)
	#if defined(__GNUC__) || defined(__clang__)
		#define BITCOUNT_GCC
	#elif defined(_MSC_VER) && (defined(_M_X64) || defined(_M_IX86))
		#define BITCOUNT_VS_X86
	#endif
#endif

#ifdef _MSC_VER
#define BITCOUNT_INLINE static __inline
#else
#define BITCOUNT_INLINE static inline
#endif

#ifdef BITCOUNT_VS_X86
#include <intrin.h>
#pragma intrinsic(_BitScanForward,_BitScanReverse,__popcnt)
#endif

#include <limits.h>
#include <stdint.h>
#define BITCOUNT_BITS (sizeof(uint64_t) * CHAR_BIT)

/* Returns the number of leading 0-bits in x, starting at the most significant
   bit position. If v is 0, the result is undefined. */
BITCOUNT_INLINE unsigned int bit_clz(uint64_t v) {
	#if defined(BITCOUNT_GCC)
	return __builtin_clzl(v);
	#elif defined(BITCOUNT_VS_X86)
	uint64_t result;
	_BitScanReverse(&result, v);
	return BITCOUNT_BITS - 1 - result;
	#else
	return bit_clz_general(v);
	#endif
}

/* Returns the number of trailing 0-bits in x, starting at the least significant
   bit position. If v is 0, the result is undefined. */
BITCOUNT_INLINE unsigned int bit_ctz(uint64_t v) {
	#if defined(BITCOUNT_GCC)
	return __builtin_ctzl(v);
	#elif defined(BITCOUNT_VS_X86)
	uint64_t result;
	_BitScanForward(&result, v);
	return result;
	#else
	return bit_ctz_general(v);
	#endif
}

/* Returns the number of 1-bits in v. */
BITCOUNT_INLINE unsigned int bit_popcount(uint64_t v) {
	#if defined(BITCOUNT_GCC)
	return __builtin_popcountl(v);
	#elif defined(BITCOUNT_VS_X86)
	return __popcnt(v);
	#else
	return bit_popcount_general(v);
	#endif
}

/* General implementations for systems without intrinsics */
BITCOUNT_INLINE unsigned int bit_clz_general(uint64_t v) {
	// From http://www.codeproject.com/Tips/784635/UInt-Bit-Operations
    uint64_t i;
    unsigned int c;

    i = ~v;
    c = ((i ^ (i + 1)) & i) >> 63;

    i = (v >> 32) + 0xffffffff;
    i = ((i & 0x100000000) ^ 0x100000000) >> 27;
    c += i;  v <<= i;

    i = (v >> 48) + 0xffff;
    i = ((i & 0x10000) ^ 0x10000) >> 12;
    c += i;  v <<= i;

    i = (v >> 56) + 0xff;
    i = ((i & 0x100) ^ 0x100) >> 5;
    c += i;  v <<= i;

    i = (v >> 60) + 0xf;
    i = ((i & 0x10) ^ 0x10) >> 2;
    c += i;  v <<= i;

    i = (v >> 62) + 3;
    i = ((i & 4) ^ 4) >> 1;
    c += i;  v <<= i;

    c += (v >> 63) ^ 1;

    return c;
}

BITCOUNT_INLINE unsigned int bit_ctz_general(uint64_t v) {
	// From http://www.codeproject.com/Tips/784635/UInt-Bit-Operations
    uint64_t i = ~v;
    unsigned int c = ((i ^ (i + 1)) & i) >> 63;

    i = (v & 0xffffffff) + 0xffffffff;
    i = ((i & 0x100000000) ^ 0x100000000) >> 27;
    c += i;  v >>= i;

    i = (v & 0xffff) + 0xffff;
    i = ((i & 0x10000) ^ 0x10000) >> 12;
    c += i;  v >>= i;

    i = (v & 0xff) + 0xff;
    i = ((i & 0x100) ^ 0x100) >> 5;
    c += i;  v >>= i;

    i = (v & 0xf) + 0xf;
    i = ((i & 0x10) ^ 0x10) >> 2;
    c += i;  v >>= i;

    i = (v & 3) + 3;
    i = ((i & 4) ^ 4) >> 1;
    c += i;  v >>= i;

    c += ((v & 1) ^ 1);

    return c;
}

BITCOUNT_INLINE unsigned int bit_popcount_general(uint64_t v) {
	/* see http://graphics.stanford.edu/~seander/bithacks.html#CountBitsSetParallel */
    v -= (v >> 1) & 0x5555555555555555ULL;
    v = (v & 0x3333333333333333ULL) + ((v >> 2) & 0x3333333333333333ULL);
    v = (v + (v >> 4)) & 0x0F0F0F0F0F0F0F0FULL;
    return (v * 0x0101010101010101ULL) >> 56;
}

#ifdef __cplusplus
}
#endif

#endif // BITCOUNT_H_


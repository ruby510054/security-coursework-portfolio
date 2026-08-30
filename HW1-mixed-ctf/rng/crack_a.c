#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

static unsigned char *read_hexfile(const char *fname, size_t *out_len) {
    FILE *f = fopen(fname, "rb");
    if (!f) {
        perror("fopen");
        return NULL;
    }

    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);

    char *buf = malloc(sz + 1);
    if (!buf) {
        fclose(f);
        return NULL;
    }

    size_t r = fread(buf, 1, sz, f);
    buf[r] = '\0';
    fclose(f);

    // Remove non-hex chars
    char *hex = malloc(r + 1);
    size_t hlen = 0;
    for (size_t i = 0; i < r; i++) {
        char c = buf[i];
        if ((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F')) {
            hex[hlen++] = c;
        }
    }
    hex[hlen] = '\0';
    free(buf);

    if (hlen % 2 != 0) {
        fprintf(stderr, "Error: hex length is odd\n");
        free(hex);
        return NULL;
    }

    size_t bytes = hlen / 2;
    unsigned char *out = malloc(bytes);
    for (size_t i = 0; i < bytes; i++) {
        unsigned int hi, lo;
        sscanf(&hex[i * 2], "%1x%1x", &hi, &lo);
        out[i] = (unsigned char)((hi << 4) | lo);
    }

    free(hex);
    *out_len = bytes;
    return out;
}

static uint8_t *bytes_to_bits(const unsigned char *bytes, size_t nbytes, size_t *out_bits) {
    size_t nbits = nbytes * 8;
    uint8_t *bits = malloc(nbits);
    if (!bits) return NULL;

    size_t idx = 0;
    for (size_t i = 0; i < nbytes; i++) {
        unsigned char b = bytes[i];
        for (int j = 7; j >= 0; j--) {
            bits[idx++] = (b >> j) & 1;
        }
    }

    *out_bits = nbits;
    return bits;
}

static unsigned char *bits_to_bytes(const uint8_t *bits, size_t nbits) {
    size_t nbytes = (nbits + 7) / 8;
    unsigned char *bytes = calloc(nbytes, 1);

    for (size_t i = 0; i < nbits; i++) {
        if (bits[i]) {
            bytes[i / 8] |= (1 << (7 - (i % 8)));
        }
    }

    return bytes;
}

typedef struct {
    uint8_t *C;
    size_t L;
} BM_Result;

BM_Result *berlekamp_massey(const uint8_t *bits, size_t nbits) {
    size_t Nmax = nbits + 1;
    uint8_t *C = calloc(Nmax, 1);
    uint8_t *B = calloc(Nmax, 1);
    uint8_t *T = calloc(Nmax, 1);

    if (!C || !B || !T) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(1);
    }

    C[0] = 1;
    B[0] = 1;
    size_t L = 0;
    size_t m = 1;

    for (size_t N = 0; N < nbits; N++) {
        uint8_t d = bits[N];
        for (size_t i = 1; i <= L; i++) {
            d ^= (C[i] & bits[N - i]);
        }

        if (d == 0) {
            m++;
        } else {
            memcpy(T, C, Nmax);
            for (size_t i = 0; i + m < Nmax; i++) {
                if (B[i]) C[i + m] ^= 1;
            }

            if (2 * L <= N) {
                memcpy(B, T, Nmax);
                L = N + 1 - L;
                m = 1;
            } else {
                m++;
            }
        }
    }

    free(B);
    free(T);

    BM_Result *result = malloc(sizeof(BM_Result));
    result->L = L;
    result->C = malloc(L + 1);
    memcpy(result->C, C, L + 1);
    free(C);

    return result;
}

void bm_result_free(BM_Result *result) {
    free(result->C);
    free(result);
}

void lfsr_predict(const uint8_t *observed, size_t obs_len,
                  const uint8_t *C, size_t L,
                  uint8_t *output, size_t output_len) {
    if (L == 0) {
        memset(output, 0, output_len);
        return;
    }

    // State = last L observed bits
    uint8_t *state = malloc(L);
    memcpy(state, observed + (obs_len - L), L);

    for (size_t k = 0; k < output_len; k++) {
        uint8_t nextb = 0;
        for (size_t i = 1; i <= L; i++) {
            if (C[i]) {
                nextb ^= state[L - i];
            }
        }

        output[k] = nextb;

        // Shift state
        memmove(state, state + 1, L - 1);
        state[L - 1] = nextb;
    }

    free(state);
}

void save_state(const char *filename, const uint8_t *observed, size_t obs_len,
                const BM_Result *result) {
    FILE *f = fopen(filename, "wb");
    if (!f) {
        perror("fopen for writing");
        return;
    }

    // Write format: obs_len (8 bytes) | L (8 bytes) | observed bits | C array
    fwrite(&obs_len, sizeof(size_t), 1, f);
    fwrite(&result->L, sizeof(size_t), 1, f);
    fwrite(observed, 1, obs_len, f);
    fwrite(result->C, 1, result->L + 1, f);

    fclose(f);
    printf("Saved state to %s\n", filename);
}

int main(int argc, char **argv) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <a_hex.txt> <output_state.bin> <predict_bytes>\n", argv[0]);
        fprintf(stderr, "Example: %s a_hex.txt rng1_state.bin 100\n", argv[0]);
        return 1;
    }

    const char *input_file = argv[1];
    const char *state_file = argv[2];
    size_t predict_bytes = (size_t)atoi(argv[3]);

    // Read input file
    size_t nbytes;
    unsigned char *data = read_hexfile(input_file, &nbytes);
    if (!data) {
        fprintf(stderr, "Failed to read input file\n");
        return 2;
    }
    printf("  Read %zu bytes\n", nbytes);

    // Convert to bits
    size_t nbits;
    uint8_t *bits = bytes_to_bits(data, nbytes, &nbits);
    free(data);
    if (!bits) {
        fprintf(stderr, "Bit conversion failed\n");
        return 3;
    }
    printf("  Converted to %zu bits\n", nbits);

    // Run Berlekamp-Massey
    clock_t t0 = clock();
    BM_Result *result = berlekamp_massey(bits, nbits);
    clock_t t1 = clock();
    double sec = (double)(t1 - t0) / CLOCKS_PER_SEC;

    printf("  Completed in %.3f seconds\n", sec);
    printf("  Recovered LFSR degree L = %zu\n", result->L);

    // Save state
    save_state(state_file, bits, nbits, result);

    // Predict next bytes
    if (predict_bytes > 0) {
        size_t predict_bits = predict_bytes * 8;
        uint8_t *predicted_bits = malloc(predict_bits);

        lfsr_predict(bits, nbits, result->C, result->L, predicted_bits, predict_bits);

        unsigned char *predicted_bytes = bits_to_bytes(predicted_bits, predict_bits);

        for (size_t i = 0; i < predict_bytes; i++) {
            printf("%02x", predicted_bytes[i]);
            if ((i + 1) % 32 == 0) printf("\n");
        }
        if (predict_bytes % 32 != 0) printf("\n");

        free(predicted_bits);
        free(predicted_bytes);
    }

    printf("✓ RNG1 cracked successfully!\n");

    free(bits);
    bm_result_free(result);
    return 0;
}

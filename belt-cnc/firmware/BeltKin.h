// Belt geometry for the four-corner belt CNC.
// Plain C++ with no FluidNC dependencies so it can be tested on a PC
// (see test/host_test.cpp). Port of tools/beltkin.py.
//
// Corners: 0 = SW, 1 = SE, 2 = NE, 3 = NW. Table frame: origin at the SW corner
// of the base sheet, +X along the south edge, +Y to the north.
//
// GPLv3, same licence as FluidNC, which this is built to plug into.

#pragma once

#include <cmath>

namespace BeltKin {
    constexpr int   N_BELTS = 4;
    constexpr float K_TWO_PI  = 6.28318530717958647692f;
    constexpr float K_HALF_PI = 1.57079632679489661923f;

    struct Corner {
        float px = 0, py = 0;  // drive pulley axis
        float fx = 0, fy = 0;  // belt end post
        float pinch = 0;       // angle of the pinch bearing round the pulley, radians, table frame
    };

    struct Geometry {
        Corner corner[N_BELTS];
        float  rp           = 6.366f;  // pitch radius of the 20 tooth drive pulley
        float  ri           = 6.376f;  // pitch radius of the belt on the smooth sled idler
        float  idler_offset = 32.0f;   // sled idlers sit at (+-offset, +-offset) from the bit
        float  dz           = 0.0f;    // sled idlers higher than the corner pulleys by this much
    };

    inline float wrap2pi(float a) {
        a = fmodf(a, K_TWO_PI);
        return a < 0 ? a + K_TWO_PI : a;
    }

    // Offset of the sled idler for corner i from the bit.
    inline void idler_offset(const Geometry& g, int i, float& bx, float& by) {
        static const float sx[N_BELTS] = { -1, 1, 1, -1 };
        static const float sy[N_BELTS] = { -1, -1, 1, 1 };
        bx                             = sx[i] * g.idler_offset;
        by                             = sy[i] * g.idler_offset;
    }

    // Belt length from the pinch point on the drive pulley, out round the sled
    // idler, and back to the end post. Optionally returns d(length)/d(x,y).
    // Returns false if the bit is so close to the corner that the geometry breaks down.
    inline bool metered(const Geometry& g, int i, float x, float y, float& len, float* dldx = nullptr, float* dldy = nullptr) {
        const Corner& c = g.corner[i];
        float         bx, by;
        idler_offset(g, i, bx, by);
        float ix = x + bx, iy = y + by;

        float dx = ix - c.px, dy = iy - c.py;
        float s     = g.rp + g.ri;
        float dist2 = dx * dx + dy * dy;
        if (dist2 <= (s + 1.0f) * (s + 1.0f)) {
            return false;
        }
        float t1    = sqrtf(dist2 - s * s);
        float alpha = atan2f(dy, dx) - atan2f(s, t1);  // direction of run 1, pulley -> idler
        float wrapP = wrap2pi(c.pinch - (alpha + K_HALF_PI));

        float ex = c.fx - ix, ey = c.fy - iy;
        float e2 = ex * ex + ey * ey - g.ri * g.ri;
        if (e2 <= 1.0f) {
            return false;
        }
        float t2    = sqrtf(e2);
        float angV  = atan2f(ey, ex) + atan2f(g.ri, t2);  // direction of run 2, idler -> post
        float wrapI = wrap2pi(angV - alpha);

        float h1 = hypotf(t1, g.dz), h2 = hypotf(t2, g.dz);
        len = g.rp * wrapP + h1 + g.ri * wrapI + h2;

        if (dldx && dldy) {
            // Moving the idler lengthens the belt along run 1 and against run 2.
            float k1 = t1 / h1, k2 = t2 / h2;
            *dldx = k1 * cosf(alpha) - k2 * cosf(angV);
            *dldy = k1 * sinf(alpha) - k2 * sinf(angV);
        }
        return true;
    }

    inline bool lengths(const Geometry& g, float x, float y, float* out) {
        for (int i = 0; i < N_BELTS; i++) {
            if (!metered(g, i, x, y, out[i])) {
                return false;
            }
        }
        return true;
    }

    // Least-squares bit position for four belt lengths. x, y come in as the
    // starting guess and go out as the answer. Returns false if it did not settle.
    inline bool forward(const Geometry& g, const float* target, float& x, float& y) {
        for (int iter = 0; iter < 20; iter++) {
            float a11 = 0, a12 = 0, a22 = 0, b1 = 0, b2 = 0;
            for (int i = 0; i < N_BELTS; i++) {
                float len, jx, jy;
                if (!metered(g, i, x, y, len, &jx, &jy)) {
                    return false;
                }
                float r = len - target[i];
                a11 += jx * jx;
                a12 += jx * jy;
                a22 += jy * jy;
                b1 -= jx * r;
                b2 -= jy * r;
            }
            float det = a11 * a22 - a12 * a12;
            if (fabsf(det) < 1e-9f) {
                return false;
            }
            float sx = (a22 * b1 - a12 * b2) / det;
            float sy = (a11 * b2 - a12 * b1) / det;
            x += sx;
            y += sy;
            if (fabsf(sx) < 2e-3f && fabsf(sy) < 2e-3f) {
                return true;
            }
        }
        return false;
    }
}

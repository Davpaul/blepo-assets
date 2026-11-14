// Checks the firmware belt maths against the Python reference model.
// Build and run on a PC:  see tools/gen_test_vectors.py
#include <cstdio>
#include <cmath>
#include "BeltKin.h"
#include "test_vectors.h"

int main() {
    float worst_len = 0, worst_fwd = 0, worst_jac = 0;
    int   n = sizeof(test_vecs) / sizeof(test_vecs[0]), fails = 0;
    for (int k = 0; k < n; k++) {
        const TestVec&   v = test_vecs[k];
        const TestTable& t = test_tables[v.table];
        BeltKin::Geometry g;
        for (int i = 0; i < 4; i++) {
            g.corner[i].px = t.p[i][0]; g.corner[i].py = t.p[i][1];
            g.corner[i].fx = t.f[i][0]; g.corner[i].fy = t.f[i][1];
            g.corner[i].pinch = t.pinch[i];
        }
        g.dz = v.dz;
        float len[4];
        if (!BeltKin::lengths(g, v.x, v.y, len)) { printf("vector %d: lengths() failed\n", k); fails++; continue; }
        for (int i = 0; i < 4; i++) {
            worst_len = fmaxf(worst_len, fabsf(len[i] - v.len[i]));
            // analytic slope against a finite difference
            float l0, l1, jx, jy, a, b;
            BeltKin::metered(g, i, v.x, v.y, l0, &jx, &jy);
            BeltKin::metered(g, i, v.x + 1.0f, v.y, l1); a = l1 - l0;
            BeltKin::metered(g, i, v.x, v.y + 1.0f, l1); b = l1 - l0;
            worst_jac = fmaxf(worst_jac, fmaxf(fabsf(a - jx), fabsf(b - jy)));
        }
        float x = v.x + 40.0f, y = v.y - 35.0f;   // start the solver well away from the answer
        if (!BeltKin::forward(g, v.len, x, y)) { printf("vector %d: forward() did not settle\n", k); fails++; continue; }
        worst_fwd = fmaxf(worst_fwd, fmaxf(fabsf(x - v.x), fabsf(y - v.y)));
    }
    printf("%d vectors\n", n);
    printf("belt length, worst difference from reference : %.4f mm\n", worst_len);
    printf("position recovered from lengths, worst error : %.4f mm\n", worst_fwd);
    printf("slope check, worst difference                : %.4f\n", worst_jac);
    bool ok = fails == 0 && worst_len < 0.01f && worst_fwd < 0.01f && worst_jac < 0.02f;
    printf(ok ? "PASS\n" : "FAIL\n");
    return ok ? 0 : 1;
}

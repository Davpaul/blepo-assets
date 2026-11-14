// Copyright (c) 2026 - belt-cnc project
// Use of this source code is governed by a GPLv3 license, the same as FluidNC.

#pragma once

/*
    BeltCNC.h

    Kinematics for a sled held by four belts, one from each corner of the table.
    Each belt runs corner pulley -> idler on the sled -> back to a post at the
    corner (a 2:1 tackle), and each corner has its own stepper.

    Motors:  X axis motor = SW belt, Y = SE belt, A = NE belt, B = NW belt, Z = Z.
    A positive motor move pays belt OUT.

    The machine assumes that when it boots (or when X and Y are "homed" with
    homing cycle -1) the bit is at home_x, home_y, normally the table centre.
*/

#include "Cartesian.h"
#include "BeltKin.h"

namespace Kinematics {
    class BeltCNC : public Cartesian {  // Cartesian supplies the limit-switch homing used for Z
    public:
        BeltCNC(const char* name) : Cartesian(name) {}

        BeltCNC(const BeltCNC&)            = delete;
        BeltCNC(BeltCNC&&)                 = delete;
        BeltCNC& operator=(const BeltCNC&) = delete;
        BeltCNC& operator=(BeltCNC&&)      = delete;

        // Kinematic interface
        void init() override;
        void init_position() override;
        void set_homed_mpos(float* mpos) override;
        bool cartesian_to_motors(float* target, plan_line_data_t* pl_data, float* position) override;
        void motors_to_cartesian(float* cartesian, float* motors, axis_t n_axis) override;
        bool transform_cartesian_to_motors(float* motors, float* cartesian) override;
        bool invalid_line(float* cartesian, plan_line_data_t* pl_data) override;
        void constrain_jog(float* cartesian, plan_line_data_t* pl_data, float* position) override;

        // Configuration handlers
        void validate() override;
        void group(Configuration::HandlerBase& handler) override;
        void afterParse() override {}

        ~BeltCNC() {}

    private:
        static const axis_t _belt_axis[BeltKin::N_BELTS];  // which motor drives which corner

        void load_geometry();
        bool belt_motors(float x, float y, float* motors);

        BeltKin::Geometry _geo;
        float             _zero[BeltKin::N_BELTS] = { 0 };  // belt lengths at the home position
        float             _last_x = 0, _last_y = 0;         // last forward solution, used as the next guess

        // Parameters (table frame, mm). Filled in by tools/table_config.py.
        float _px[BeltKin::N_BELTS]        = { -30, 2470, 2470, -30 };
        float _py[BeltKin::N_BELTS]        = { -30, -30, 1250, 1250 };
        float _fx[BeltKin::N_BELTS]        = { -52.63f, 2447.37f, 2492.63f, -7.37f };
        float _fy[BeltKin::N_BELTS]        = { -7.37f, -52.63f, 1227.37f, 1272.63f };
        float _pinch_deg[BeltKin::N_BELTS] = { 285, 15, 105, 195 };
        float _trim[BeltKin::N_BELTS]      = { 0, 0, 0, 0 };  // per-belt length trim, set at run time
        float _home_x                      = 1220;
        float _home_y                      = 610;
        float _min_x = 0, _max_x = 2440, _min_y = 0, _max_y = 1220;  // where the bit is allowed to go
        float _pulley_pitch_radius = 6.366f;
        float _idler_pitch_radius  = 6.376f;
        float _idler_offset        = 32.0f;
        float _belt_dz             = 0.0f;
        float _segment_length      = 2.0f;
    };
}  //  namespace Kinematics

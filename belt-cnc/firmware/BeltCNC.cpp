// Copyright (c) 2026 - belt-cnc project
// Use of this source code is governed by a GPLv3 license, the same as FluidNC.
//
// Modelled on FluidNC's WallPlotter kinematics (Copyright (c) 2020 Bart Dring).

#include "BeltCNC.h"

#include "Machine/MachineConfig.h"
#include "Limit.h"

#include <cmath>

namespace Kinematics {
    using BeltKin::N_BELTS;

    // corner 0 SW, 1 SE, 2 NE, 3 NW
    const axis_t BeltCNC::_belt_axis[N_BELTS] = { X_AXIS, Y_AXIS, A_AXIS, B_AXIS };

    static const char* const corner_name[N_BELTS] = { "sw", "se", "ne", "nw" };

    void BeltCNC::group(Configuration::HandlerBase& handler) {
        // Corner geometry. Do not type these by hand: tools/table_config.py works
        // them out from five tape measurements and prints this whole block.
        static char names[N_BELTS][6][16];
        for (int i = 0; i < N_BELTS; i++) {
            snprintf(names[i][0], 16, "%s_pulley_x", corner_name[i]);
            snprintf(names[i][1], 16, "%s_pulley_y", corner_name[i]);
            snprintf(names[i][2], 16, "%s_post_x", corner_name[i]);
            snprintf(names[i][3], 16, "%s_post_y", corner_name[i]);
            snprintf(names[i][4], 16, "%s_pinch_deg", corner_name[i]);
            snprintf(names[i][5], 16, "%s_trim", corner_name[i]);
            handler.item(names[i][0], _px[i]);
            handler.item(names[i][1], _py[i]);
            handler.item(names[i][2], _fx[i]);
            handler.item(names[i][3], _fy[i]);
            handler.item(names[i][4], _pinch_deg[i]);
            // Extra belt paid out (+) or taken in (-) at this corner, in mm of belt.
            // Changed at run time by tools/belt_setup.py to snug the belts; it takes
            // effect on the next move. Not meant to be saved in the config file.
            handler.item(names[i][5], _trim[i], -200.0f, 200.0f);
        }
        // Where the bit is when the controller boots, normally the table centre.
        handler.item("home_x", _home_x);
        handler.item("home_y", _home_y);
        // Rectangle the bit is allowed to move in.
        handler.item("min_x", _min_x);
        handler.item("max_x", _max_x);
        handler.item("min_y", _min_y);
        handler.item("max_y", _max_y);
        handler.item("pulley_pitch_radius", _pulley_pitch_radius, 2.0f, 30.0f);
        handler.item("idler_pitch_radius", _idler_pitch_radius, 2.0f, 30.0f);
        handler.item("idler_offset", _idler_offset, 5.0f, 300.0f);
        // How much higher the sled idlers are than the corner pulleys (the workpiece
        // thickness when the corner units sit on a base board under the workpiece).
        handler.item("belt_dz", _belt_dz, -50.0f, 100.0f);
        // Straight moves are chopped into pieces this long before conversion to belt lengths.
        handler.item("segment_length", _segment_length, 0.2f, 20.0f);
    }

    void BeltCNC::validate() {
        Assert(Axes::_numberAxis >= 5, "BeltCNC needs five axes: x y z a b");
        Assert(_max_x > _min_x && _max_y > _min_y, "BeltCNC: max_x/max_y must be greater than min_x/min_y");
    }

    void BeltCNC::load_geometry() {
        for (int i = 0; i < N_BELTS; i++) {
            _geo.corner[i].px    = _px[i];
            _geo.corner[i].py    = _py[i];
            _geo.corner[i].fx    = _fx[i];
            _geo.corner[i].fy    = _fy[i];
            _geo.corner[i].pinch = _pinch_deg[i] * (float)M_PI / 180.0f;
        }
        _geo.rp           = _pulley_pitch_radius;
        _geo.ri           = _idler_pitch_radius;
        _geo.idler_offset = _idler_offset;
        _geo.dz           = _belt_dz;
    }

    void BeltCNC::init() {
        log_info("Kinematic system: " << name());
        load_geometry();
        if (!BeltKin::lengths(_geo, _home_x, _home_y, _zero)) {
            log_error("BeltCNC: home position is not reachable with this table geometry");
        }
        _last_x = _home_x;
        _last_y = _home_y;
        init_position();
    }

    // Motors start at zero, which by definition is the home position.
    void BeltCNC::init_position() {
        auto n_axis = Axes::_numberAxis;
        for (axis_t axis = X_AXIS; axis < n_axis; axis++) {
            set_steps(axis, 0);
            _min_motor_pos[axis] = limitsMinPosition(axis);
            _max_motor_pos[axis] = limitsMaxPosition(axis);
        }
        for (int i = 0; i < N_BELTS; i++) {
            _min_motor_pos[_belt_axis[i]] = -100000.0f;
            _max_motor_pos[_belt_axis[i]] = 100000.0f;
        }
    }

    // Belt motor positions for a bit position. Motor value = belt paid out beyond
    // what it was at home, plus that corner's trim.
    bool BeltCNC::belt_motors(float x, float y, float* motors) {
        // the geometry items can be changed at run time ($/kinematics/BeltCNC/...), so reload
        load_geometry();
        float len[N_BELTS];
        if (!BeltKin::lengths(_geo, x, y, len)) {
            return false;
        }
        for (int i = 0; i < N_BELTS; i++) {
            motors[_belt_axis[i]] = len[i] - _zero[i] + _trim[i];
        }
        return true;
    }

    bool BeltCNC::transform_cartesian_to_motors(float* motors, float* cartesian) {
        auto n_axis = Axes::_numberAxis;
        for (axis_t axis = X_AXIS; axis < n_axis; axis++) {
            motors[axis] = cartesian[axis];  // Z and anything else passes straight through
        }
        return belt_motors(cartesian[X_AXIS], cartesian[Y_AXIS], motors);
    }

    bool BeltCNC::invalid_line(float* cartesian, plan_line_data_t* pl_data) {
        float x = cartesian[X_AXIS], y = cartesian[Y_AXIS];
        if (x < _min_x || x > _max_x) {
            limit_error(X_AXIS, x, cartesian, pl_data);
            return true;
        }
        if (y < _min_y || y > _max_y) {
            limit_error(Y_AXIS, y, cartesian, pl_data);
            return true;
        }
        float z = cartesian[Z_AXIS];
        if (config->_axes->_axis[Z_AXIS]->_softLimits && (z < limitsMinPosition(Z_AXIS) || z > limitsMaxPosition(Z_AXIS))) {
            limit_error(Z_AXIS, z, cartesian, pl_data);
            return true;
        }
        return false;
    }

    // Jogs are clipped to the allowed rectangle instead of being refused.
    void BeltCNC::constrain_jog(float* cartesian, plan_line_data_t* pl_data, float* position) {
        cartesian[X_AXIS] = fminf(fmaxf(cartesian[X_AXIS], _min_x), _max_x);
        cartesian[Y_AXIS] = fminf(fmaxf(cartesian[Y_AXIS], _min_y), _max_y);
        Cartesian::constrain_jog(cartesian, pl_data, position);
    }

    /*
      All straight moves come through here. The belt lengths are not linear in X
      and Y, so the move is chopped into short pieces and each end point is
      converted. The planner works in motor space, so the feed rate is scaled by
      (distance the motors travel) / (distance the bit travels) for each piece.
    */
    bool BeltCNC::cartesian_to_motors(float* target, plan_line_data_t* pl_data, float* position) {
        auto n_axis = Axes::_numberAxis;

        float motors[MAX_N_AXIS];
        float total = vector_distance(position, target, n_axis);
        if (total == 0) {
            // No cartesian movement, but still plan it: this is how a changed belt
            // trim gets applied, and how S and M words reach the planner.
            if (!transform_cartesian_to_motors(motors, target)) {
                return false;
            }
            return mc_move_motors(motors, pl_data);
        }

        float cartesian_feed = pl_data->feed_rate;
        float xydist         = vector_distance(target, position, 2);
        uint32_t segments    = (uint32_t)(xydist / _segment_length);
        if (segments < 1) {
            segments = 1;
        }
        float seg_len = total / segments;

        float step[MAX_N_AXIS];
        float seg_end[MAX_N_AXIS];
        float last_motors[MAX_N_AXIS];
        for (axis_t axis = X_AXIS; axis < n_axis; axis++) {
            step[axis]    = (target[axis] - position[axis]) / segments;
            seg_end[axis] = position[axis];
        }
        if (!transform_cartesian_to_motors(last_motors, position)) {
            return false;
        }

        for (uint32_t segment = 1; segment <= segments; segment++) {
            if (sys.abort()) {
                return true;
            }
            for (axis_t axis = X_AXIS; axis < n_axis; axis++) {
                seg_end[axis] = (segment == segments) ? target[axis] : seg_end[axis] + step[axis];
            }
            if (!transform_cartesian_to_motors(motors, seg_end)) {
                log_error("BeltCNC: move goes somewhere the belts cannot reach");
                return false;
            }
            if (!pl_data->motion.rapidMotion) {
                float motor_len    = vector_distance(last_motors, motors, n_axis);
                pl_data->feed_rate = cartesian_feed * motor_len / seg_len;
            }
            copyAxes(last_motors, motors);
            if (!mc_move_motors(motors, pl_data)) {
                return false;  // jog cancelled
            }
        }
        return true;
    }

    // Status reports use this. Four belts over-determine X and Y, so this is a
    // least-squares fit, started from the previous answer.
    void BeltCNC::motors_to_cartesian(float* cartesian, float* motors, axis_t n_axis) {
        for (axis_t axis = X_AXIS; axis < n_axis; axis++) {
            cartesian[axis] = motors[axis];
        }
        load_geometry();
        float len[N_BELTS];
        for (int i = 0; i < N_BELTS; i++) {
            len[i] = motors[_belt_axis[i]] + _zero[i] - _trim[i];
        }
        float x = _last_x, y = _last_y;
        if (!BeltKin::forward(_geo, len, x, y)) {
            x = _home_x;  // lost: retry from the middle of the table
            y = _home_y;
            if (!BeltKin::forward(_geo, len, x, y)) {
                x = _last_x;
                y = _last_y;
            }
        }
        _last_x           = x;
        _last_y           = y;
        cartesian[X_AXIS] = x;
        cartesian[Y_AXIS] = y;
        cartesian[A_AXIS] = 0;
        cartesian[B_AXIS] = 0;
    }

    // Called after homing. Z homes on its switch as usual. X and Y have no
    // switches: give them homing cycle -1 and "$HX" / "$HY" then mean "the bit is
    // at this X / Y now", which re-bases the belt motors without moving anything.
    void BeltCNC::set_homed_mpos(float* mpos) {
        auto  n_axis = Axes::_numberAxis;
        float motors[MAX_N_AXIS];
        float now[MAX_N_AXIS];
        motors_to_cartesian(now, get_motor_pos(), n_axis);

        bool xy_declared = fabsf(mpos[X_AXIS] - now[X_AXIS]) > 0.05f || fabsf(mpos[Y_AXIS] - now[Y_AXIS]) > 0.05f;
        if (!transform_cartesian_to_motors(motors, mpos)) {
            log_error("BeltCNC: cannot set that position");
            return;
        }
        for (axis_t axis = X_AXIS; axis < n_axis; axis++) {
            bool is_belt = false;
            for (int i = 0; i < N_BELTS; i++) {
                is_belt |= (_belt_axis[i] == axis);
            }
            if (is_belt && !xy_declared) {
                continue;  // leave the belts exactly as they are
            }
            set_steps(axis, motor_pos_to_steps(motors[axis], axis));
        }
        if (xy_declared) {
            _last_x = mpos[X_AXIS];
            _last_y = mpos[Y_AXIS];
        }
    }

    // Configuration registration
    namespace {
        KinematicsFactory::InstanceBuilder<BeltCNC> registration("BeltCNC");
    }
}

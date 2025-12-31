// Big Hex - Large Hexapod Leg Design
// For LX-16A Serial Bus Servos (45 x 25 x 36mm) - CORRECTED
// Body: 350mm across, Leg reach: ~250mm
// Torque margin: 55% with 80mm femur + 120mm tibia

/* [LX-16A Servo Dimensions] */
// CORRECTED dimensions from datasheet (was 40x20x40.5)
lx16a_length = 45;      // Along shaft axis (verified)
lx16a_width = 25;       // Side to side (verified)
lx16a_height = 36;      // Top to bottom (verified)
lx16a_shaft_offset = 9; // Shaft center from edge
lx16a_shaft_dia = 6;
lx16a_horn_dia = 25;    // Standard horn diameter
lx16a_mount_hole_spacing = 52;  // Between mounting tabs (updated)
lx16a_mount_hole_dia = 3.2;     // M3 clearance holes
lx16a_tab_width = 8;
lx16a_tab_thickness = 2.5;

/* [Leg Dimensions] */
coxa_length = 50;       // Hip segment
femur_length = 80;      // Upper leg (was 100, reduced for torque margin)
tibia_length = 120;     // Lower leg (was 150, reduced for torque margin)
wall_thickness = 4;     // Structural walls
clearance = 0.4;        // Printer tolerance (increased slightly)

/* [Body Dimensions] */
body_radius = 175;      // ~350mm across (was 200, reduced for weight)
body_thickness = 5;
standoff_height = 45;   // Between plates (slightly reduced)

/* [Tube Dimensions] */
leg_tube_od = 28;       // Outer diameter of leg tubes (was 25, increased for strength)
leg_tube_id = 22;       // Inner diameter (wire routing)

/* [Rendering] */
$fn = 48;

// ============================================
// LX-16A Servo Pocket (for embedding)
// UPDATED: Corrected dimensions and added mounting holes
// ============================================
module lx16a_pocket() {
    c = clearance;

    union() {
        // Main body - corrected size
        cube([lx16a_length + c*2, lx16a_width + c*2, lx16a_height + c*2], center=true);

        // Mounting tabs slot - wider for actual servo
        translate([0, 0, lx16a_height/2 - 5])
            cube([lx16a_mount_hole_spacing + 12, lx16a_width + c*2, lx16a_tab_thickness + c*2], center=true);

        // Mounting screw holes through bracket (M3 clearance)
        for (x = [-lx16a_mount_hole_spacing/2, lx16a_mount_hole_spacing/2]) {
            translate([x, 0, lx16a_height/2])
                cylinder(d=lx16a_mount_hole_dia, h=15, center=true);
        }

        // Cable exit - larger for daisy-chain connectors
        translate([0, -lx16a_width/2 - 5, -lx16a_height/4])
            cube([15, 15, 12], center=true);
    }
}

// LX-16A outline for visualization
module lx16a_servo() {
    color("DimGray") {
        // Main body
        cube([lx16a_length, lx16a_width, lx16a_height], center=true);

        // Mounting tabs
        translate([0, 0, lx16a_height/2 - 5])
            cube([lx16a_mount_hole_spacing + lx16a_tab_width, lx16a_width, lx16a_tab_thickness], center=true);

        // Output shaft
        translate([lx16a_length/2 - lx16a_shaft_offset, 0, lx16a_height/2])
            cylinder(d=lx16a_shaft_dia, h=8);
    }
}

// ============================================
// Coxa Bracket - Hip rotation mount
// ============================================
module coxa_bracket() {
    bracket_w = lx16a_width + wall_thickness*2;
    bracket_l = lx16a_length + wall_thickness*2;
    bracket_h = lx16a_height + wall_thickness*2;

    // Body mount flange dimensions
    flange_w = 50;
    flange_h = 40;
    flange_t = 5;

    difference() {
        union() {
            // Servo housing
            translate([0, 0, 0])
                cube([bracket_l, bracket_w, bracket_h], center=true);

            // Body mount flange
            translate([-bracket_l/2 - flange_t/2 + 1, 0, 0])
                cube([flange_t, flange_w, flange_h], center=true);

            // Output side reinforcement
            translate([bracket_l/2, 0, bracket_h/2])
                cylinder(d=bracket_w, h=wall_thickness);
        }

        // Servo pocket
        lx16a_pocket();

        // Shaft hole (top)
        translate([lx16a_length/2 - lx16a_shaft_offset, 0, bracket_h/2 - 2])
            cylinder(d=lx16a_horn_dia + 2, h=wall_thickness + 5);

        // Body mount holes
        translate([-bracket_l/2 - flange_t/2, 0, 0]) {
            for (dy = [-15, 15]) {
                for (dz = [-12, 12]) {
                    translate([0, dy, dz])
                        rotate([0, 90, 0])
                            cylinder(d=3.5, h=flange_t + 2, center=true);
                }
            }
        }

        // Wire channel
        translate([0, -bracket_w/2, -bracket_h/4])
            cube([12, wall_thickness*3, 10], center=true);
    }
}

// ============================================
// Femur Link - Upper leg (80mm)
// FIXED: Servo rotated 90° so shaft points horizontally (Y axis)
// ============================================
module femur_link() {
    // Servo box rotated: length along X, height along Y (for horizontal shaft)
    servo_box_l = lx16a_length + wall_thickness*2;  // Along leg (X)
    servo_box_w = lx16a_height + wall_thickness*2;  // Vertical (Z) - swapped
    servo_box_h = lx16a_width + wall_thickness*2;   // Toward body (Y) - swapped

    // Hub for coxa horn attachment
    hub_dia = 35;
    hub_height = 15;

    difference() {
        union() {
            // Coxa attachment hub
            translate([0, 0, 0])
                cylinder(d=hub_dia, h=hub_height, center=true);

            // Main tube section
            translate([femur_length/2 - 10, 0, 0])
                rotate([0, 90, 0])
                    cylinder(d=leg_tube_od, h=femur_length - 20);

            // Transition from hub to tube
            hull() {
                cylinder(d=hub_dia, h=hub_height, center=true);
                translate([20, 0, 0])
                    rotate([0, 90, 0])
                        cylinder(d=leg_tube_od, h=1);
            }

            // Servo mount at end (for tibia) - rotated orientation
            translate([femur_length - servo_box_l/2, 0, 0])
                cube([servo_box_l, servo_box_h, servo_box_w], center=true);
        }

        // Horn attachment hole (coxa side)
        cylinder(d=lx16a_shaft_dia + 1, h=hub_height + 2, center=true);

        // Horn screw holes (M2 = 2.2mm)
        for (a = [0:90:360]) {
            rotate([0, 0, a])
                translate([8, 0, 0])
                    cylinder(d=2.2, h=hub_height + 2, center=true);
        }

        // Wire channel through tube
        translate([femur_length/2, 0, 0])
            rotate([0, 90, 0])
                cylinder(d=leg_tube_id, h=femur_length + 10, center=true);

        // Servo pocket at end - ROTATED 90° around X axis
        translate([femur_length - servo_box_l/2, 0, 0])
            rotate([90, 0, 0])
                lx16a_pocket();

        // Shaft hole for tibia - now on SIDE (Y axis) not top
        translate([femur_length - lx16a_shaft_offset, servo_box_h/2, 0])
            rotate([90, 0, 0])
                cylinder(d=lx16a_horn_dia + 2, h=wall_thickness + 5);
    }
}

// ============================================
// Tibia Link - Lower leg (120mm)
// Hub attaches to femur servo (horizontal shaft)
// ============================================
module tibia_link() {
    hub_dia = 35;
    hub_height = 15;
    foot_dia = 20;

    difference() {
        union() {
            // Femur attachment hub - rotated to match horizontal servo shaft
            translate([0, 0, 0])
                rotate([90, 0, 0])
                    cylinder(d=hub_dia, h=hub_height, center=true);

            // Main leg tube - tapered
            hull() {
                translate([15, 0, 0])
                    rotate([0, 90, 0])
                        cylinder(d=leg_tube_od, h=1);
                translate([tibia_length - 15, 0, 0])
                    rotate([0, 90, 0])
                        cylinder(d=foot_dia, h=1);
            }

            // Transition from hub to tube
            hull() {
                rotate([90, 0, 0])
                    cylinder(d=hub_dia, h=hub_height, center=true);
                translate([15, 0, 0])
                    rotate([0, 90, 0])
                        cylinder(d=leg_tube_od, h=1);
            }

            // Foot mount
            translate([tibia_length, 0, 0])
                rotate([0, 90, 0])
                    cylinder(d=foot_dia, h=10);
        }

        // Horn attachment hole - horizontal (Y axis)
        rotate([90, 0, 0])
            cylinder(d=lx16a_shaft_dia + 1, h=hub_height + 2, center=true);

        // Horn screw holes (M2 = 2.2mm, 4 holes at 8mm radius)
        rotate([90, 0, 0])
            for (a = [0:90:360]) {
                rotate([0, 0, a])
                    translate([8, 0, 0])
                        cylinder(d=2.2, h=hub_height + 2, center=true);
            }

        // Wire channel
        translate([tibia_length/2, 0, 0])
            rotate([0, 90, 0])
                cylinder(d=8, h=tibia_length - 20, center=true);

        // Foot attachment hole
        translate([tibia_length + 5, 0, 0])
            rotate([0, 90, 0])
                cylinder(d=8, h=20, center=true);
    }
}

// ============================================
// Foot Tip - Rubber contact (print in TPU)
// ============================================
module foot_tip() {
    difference() {
        union() {
            // Mounting plug
            cylinder(d=8 - clearance*2, h=15);

            // Foot pad
            translate([0, 0, 15])
                cylinder(d1=20, d2=12, h=20);

            // Grip ridges
            translate([0, 0, 25])
                for (a = [0:45:360]) {
                    rotate([0, 0, a])
                        translate([5, 0, 0])
                            sphere(d=4);
                }
        }
    }
}

// ============================================
// Body Plate Segment - 1/6 of hexagon (printable on 220mm bed)
// Print 6 of these and bolt together
// ============================================
module body_plate_segment(top=true, segment=0) {
    plate_t = body_thickness;
    seg_angle = 60;

    // Bolt hole positions for joining segments
    join_r1 = 50;   // Inner join radius
    join_r2 = body_radius - 20;  // Outer join radius

    rotate([0, 0, segment * 60]) {
        difference() {
            // Wedge shape
            linear_extrude(height=plate_t)
                polygon([
                    [0, 0],
                    [body_radius * cos(-seg_angle/2), body_radius * sin(-seg_angle/2)],
                    [body_radius * cos(seg_angle/2), body_radius * sin(seg_angle/2)]
                ]);

            // Center cutout (partial)
            translate([0, 0, -1])
                cylinder(d=50, h=plate_t + 2);

            // Segment join holes (to bolt segments together)
            for (r = [join_r1, join_r2]) {
                for (a = [-25, 25]) {
                    rotate([0, 0, a])
                        translate([r, 0, -1])
                            cylinder(d=3.5, h=plate_t + 2);
                }
            }

            // Leg mount holes (one leg per segment)
            rotate([0, 0, 0]) {
                translate([body_radius - 30, 0, -1]) {
                    // Coxa bracket mount holes
                    for (dy = [-15, 15]) {
                        for (dx = [-12, 12]) {
                            translate([dx, dy, 0])
                                cylinder(d=3.5, h=plate_t + 2);
                        }
                    }
                    // Cable routing slot
                    hull() {
                        cylinder(d=15, h=plate_t + 2);
                        translate([-20, 0, 0])
                            cylinder(d=15, h=plate_t + 2);
                    }
                }
            }

            // Standoff holes for this segment
            translate([body_radius - 50, 0, -1])
                cylinder(d=3.5, h=plate_t + 2);
            translate([70, 0, -1])
                cylinder(d=3.5, h=plate_t + 2);

            // Ventilation slot (top plate only)
            if (top) {
                translate([90, 0, -1])
                    hull() {
                        cylinder(d=10, h=plate_t + 2);
                        translate([30, 0, 0])
                            cylinder(d=10, h=plate_t + 2);
                    }
            }
        }
    }
}

// ============================================
// Full Body Plate - Hexagonal (for preview only)
// For printing, use body_plate_segment() x6
// ============================================
module body_plate(top=true) {
    plate_t = body_thickness;

    difference() {
        // Hexagon plate
        linear_extrude(height=plate_t)
            circle(r=body_radius, $fn=6);

        // Center hole for wiring
        translate([0, 0, -1])
            cylinder(d=60, h=plate_t + 2);

        // Leg mount cutouts (6 positions)
        for (a = [0:60:300]) {
            rotate([0, 0, a + 30]) {
                translate([body_radius - 30, 0, -1]) {
                    // Coxa bracket mount holes
                    for (dy = [-15, 15]) {
                        for (dx = [-12, 12]) {
                            translate([dx, dy, 0])
                                cylinder(d=3.5, h=plate_t + 2);
                        }
                    }
                    // Cable routing slot
                    hull() {
                        cylinder(d=15, h=plate_t + 2);
                        translate([-20, 0, 0])
                            cylinder(d=15, h=plate_t + 2);
                    }
                }
            }
        }

        // Standoff holes
        for (a = [0:60:300]) {
            rotate([0, 0, a]) {
                translate([body_radius - 50, 0, -1])
                    cylinder(d=3.5, h=plate_t + 2);
                translate([70, 0, -1])
                    cylinder(d=3.5, h=plate_t + 2);
            }
        }

        // Electronics mount holes (bottom plate)
        if (!top) {
            // Pi Zero mount
            translate([-30, -30, -1]) {
                for (dx = [0, 58]) {
                    for (dy = [0, 23]) {
                        translate([dx, dy, 0])
                            cylinder(d=2.8, h=plate_t + 2);
                    }
                }
            }

            // Buck converter mount
            translate([40, 20, -1]) {
                for (dx = [0, 30]) {
                    for (dy = [0, 20]) {
                        translate([dx, dy, 0])
                            cylinder(d=3.5, h=plate_t + 2);
                    }
                }
            }
        }

        // Ventilation slots (top plate)
        if (top) {
            for (a = [30:60:360]) {
                rotate([0, 0, a])
                    translate([85, 0, -1])
                        hull() {
                            cylinder(d=10, h=plate_t + 2);
                            translate([35, 0, 0])
                                cylinder(d=10, h=plate_t + 2);
                        }
            }
        }
    }
}

// ============================================
// Standoff - Increased diameter for strength
// ============================================
module standoff() {
    difference() {
        union() {
            // Main column (thicker)
            cylinder(d=14, h=standoff_height);
            // Reinforced base
            cylinder(d=18, h=3);
            // Reinforced top
            translate([0, 0, standoff_height - 3])
                cylinder(d=18, h=3);
        }
        // Through hole for M3 bolt
        translate([0, 0, -1])
            cylinder(d=3.5, h=standoff_height + 2);
    }
}

// ============================================
// Complete Leg Assembly (for visualization)
// UPDATED: Servo orientations corrected
// ============================================
module leg_assembly() {
    // Coxa bracket (servo shaft points UP for horizontal leg rotation)
    color("DarkSlateGray") coxa_bracket();

    // Coxa servo (vertical shaft)
    translate([lx16a_length/2 - lx16a_shaft_offset, 0, 0])
        lx16a_servo();

    // Femur link
    color("SlateGray")
        translate([coxa_length + 20, 0, 0])
            femur_link();

    // Femur servo (horizontal shaft - rotated 90°)
    translate([coxa_length + 20 + femur_length - lx16a_shaft_offset, 0, 0])
        rotate([90, 0, 0])
            lx16a_servo();

    // Tibia link (hub rotated to match horizontal servo shaft)
    color("LightSlateGray")
        translate([coxa_length + 20 + femur_length + 20, 0, 0])
            tibia_link();

    // Foot
    color("Black")
        translate([coxa_length + femur_length + tibia_length + 55, 0, 0])
            rotate([0, 90, 0])
                foot_tip();
}

// ============================================
// Full Robot Preview
// ============================================
module full_robot() {
    // Bottom plate
    color("DarkBlue", 0.7)
        body_plate(top=false);

    // Top plate
    color("DarkBlue", 0.7)
        translate([0, 0, standoff_height + body_thickness])
            body_plate(top=true);

    // Standoffs (adjusted positions)
    color("Silver")
        for (a = [0:60:300]) {
            rotate([0, 0, a]) {
                translate([body_radius - 50, 0, body_thickness])
                    standoff();
                translate([70, 0, body_thickness])
                    standoff();
            }
        }

    // Legs
    for (a = [0:60:300]) {
        rotate([0, 0, a + 30])
            translate([body_radius - 10, 0, standoff_height/2 + body_thickness])
                rotate([0, 0, 0])
                    leg_assembly();
    }
}

// ============================================
// Render Selection
// ============================================

// Uncomment ONE to render for STL export:

// === Leg Parts (print qty in parentheses) ===
// coxa_bracket();           // (x6)
// femur_link();             // (x6)
// tibia_link();             // (x6)
// foot_tip();               // (x6, TPU)
// standoff();               // (x12)

// === Body Plate Segments (print 6 top + 6 bottom) ===
// body_plate_segment(top=true, segment=0);   // Top segment
// body_plate_segment(top=false, segment=0);  // Bottom segment

// === Full plates (only if printer is 300mm+) ===
// body_plate(top=true);
// body_plate(top=false);

// Preview full assembly (uncomment for OpenSCAD GUI preview):
// full_robot();

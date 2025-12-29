// Hexapod Leg - Parametric OpenSCAD Design
// Designed for SG90 (femur/tibia) and HS-82MG (coxa) servos

/* [Servo Dimensions] */
// SG90 micro servo
sg90_width = 12;
sg90_length = 23;
sg90_height = 29;
sg90_shaft_height = 4;
sg90_ear_width = 32;
sg90_ear_thickness = 2.5;
sg90_ear_offset = 15.5;  // from bottom

// HS-82MG servo (slightly larger)
hs82_width = 12;
hs82_length = 30;
hs82_height = 30;
hs82_shaft_height = 4;
hs82_ear_width = 40;
hs82_ear_thickness = 2.5;
hs82_ear_offset = 17;

/* [Leg Dimensions] */
coxa_length = 25;
femur_length = 55;
tibia_length = 75;
wall_thickness = 3;
clearance = 0.3;  // printer tolerance

/* [Rendering] */
$fn = 32;

// Servo pocket module (for embedding servo)
module servo_pocket(type="sg90") {
    w = (type == "sg90") ? sg90_width : hs82_width;
    l = (type == "sg90") ? sg90_length : hs82_length;
    h = (type == "sg90") ? sg90_height : hs82_height;
    ear_w = (type == "sg90") ? sg90_ear_width : hs82_ear_width;
    ear_t = (type == "sg90") ? sg90_ear_thickness : hs82_ear_thickness;
    ear_off = (type == "sg90") ? sg90_ear_offset : hs82_ear_offset;

    c = clearance;

    union() {
        // Main body
        cube([l + c*2, w + c*2, h + c], center=true);
        // Mounting ears
        translate([0, 0, h/2 - ear_off])
            cube([ear_w + c*2, w + c*2, ear_t + c], center=true);
    }
}

// Horn/shaft hole
module shaft_hole(d=7, h=10) {
    cylinder(d=d + clearance*2, h=h, center=true);
}

// Coxa bracket - mounts HS-82MG for hip rotation
module coxa_bracket() {
    bracket_h = hs82_height + wall_thickness * 2;
    bracket_w = hs82_width + wall_thickness * 2;
    bracket_l = hs82_length + wall_thickness * 2;

    difference() {
        // Outer shell
        cube([bracket_l, bracket_w, bracket_h], center=true);

        // Servo pocket
        translate([0, 0, wall_thickness])
            servo_pocket("hs82");

        // Shaft hole (top)
        translate([0, 0, bracket_h/2 - 2])
            shaft_hole();

        // Wire channel
        translate([bracket_l/2, 0, 0])
            cube([wall_thickness*2, 6, 8], center=true);
    }
}

// Femur link - connects coxa to tibia
module femur_link() {
    link_w = sg90_width + wall_thickness * 2;
    link_h = sg90_height/2 + wall_thickness;

    difference() {
        union() {
            // Main beam
            cube([femur_length, link_w, link_h], center=true);

            // Servo mount end
            translate([femur_length/2 - sg90_length/2, 0, 0])
                cube([sg90_length + wall_thickness*2, link_w, sg90_height + wall_thickness], center=true);
        }

        // Servo pocket at end
        translate([femur_length/2 - sg90_length/2, 0, 0])
            servo_pocket("sg90");

        // Horn attachment hole (other end)
        translate([-femur_length/2 + 8, 0, 0])
            shaft_hole();
    }
}

// Tibia link - lower leg segment
module tibia_link() {
    link_w = 15;
    link_h = 8;

    difference() {
        union() {
            // Main beam
            hull() {
                translate([-tibia_length/2 + 8, 0, 0])
                    cylinder(d=link_w, h=link_h, center=true);
                translate([tibia_length/2 - 5, 0, 0])
                    cylinder(d=10, h=link_h, center=true);
            }
        }

        // Horn attachment hole
        translate([-tibia_length/2 + 8, 0, 0])
            shaft_hole();
    }
}

// Foot tip (print in TPU for grip)
module foot_tip() {
    cylinder(d1=12, d2=6, h=15, center=true);
}

// Body mount plate (1/6 segment)
module body_segment() {
    seg_angle = 60;
    inner_r = 30;
    outer_r = 100;
    thickness = 4;

    difference() {
        // Wedge shape
        linear_extrude(height=thickness)
            polygon([
                [0, 0],
                [outer_r * cos(seg_angle/2), outer_r * sin(seg_angle/2)],
                [outer_r * cos(-seg_angle/2), outer_r * sin(-seg_angle/2)]
            ]);

        // Inner cutout
        translate([0, 0, -1])
            cylinder(r=inner_r, h=thickness+2);

        // Coxa mount holes
        translate([70, 0, -1]) {
            cylinder(d=3.2, h=thickness+2);
            translate([15, 0, 0])
                cylinder(d=3.2, h=thickness+2);
        }
    }
}

// Preview all parts
module preview() {
    color("DarkGray") coxa_bracket();
    color("Gray") translate([50, 0, 0]) femur_link();
    color("LightGray") translate([120, 0, 0]) tibia_link();
    color("Black") translate([180, 0, 0]) foot_tip();
    color("Blue", 0.5) translate([0, 60, 0]) body_segment();
}

// Uncomment to render individual parts for printing:
// coxa_bracket();
// femur_link();
// tibia_link();
// foot_tip();
// body_segment();

preview();

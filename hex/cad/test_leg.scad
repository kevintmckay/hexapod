// Test Leg Print - One complete leg for fit testing
// Print this first before committing to all 6 legs
//
// PRINT SETTINGS:
//   Material: PLA or PETG
//   Layer height: 0.2mm
//   Infill: 20-30%
//   Supports: YES (for coxa bracket and femur)
//   Bed: 150x150mm minimum
//
// AFTER PRINTING:
//   1. Test fit servos (should slide in snugly)
//   2. Check horn shaft holes (7mm diameter)
//   3. Verify wall thickness is adequate
//   4. Adjust 'clearance' variable if too tight/loose

include <leg.scad>

// Arrange parts for printing on bed
module test_leg_plate() {
    // Coxa bracket - needs supports, print upright
    translate([0, 0, 0])
        coxa_bracket();

    // Femur link - print on side for strength
    translate([50, 0, sg90_height/2 + wall_thickness/2])
        rotate([90, 0, 0])
            femur_link();

    // Tibia link - simple, flat print
    translate([0, 50, 4])
        tibia_link();

    // Foot tip - optional, can print in TPU later
    translate([60, 50, 7.5])
        foot_tip();
}

// Alternative: Parts laid flat (less supports needed)
module test_leg_flat() {
    // Coxa bracket on its side
    translate([0, 0, (hs82_width + wall_thickness*2)/2])
        rotate([90, 0, 0])
            coxa_bracket();

    // Femur link flat
    translate([60, 0, (sg90_height + wall_thickness)/2])
        femur_link();

    // Tibia link
    translate([0, 40, 4])
        tibia_link();

    // Foot
    translate([60, 40, 7.5])
        foot_tip();
}

// CHOOSE ONE:
// test_leg_plate();   // Standard orientation with supports
test_leg_flat();       // Flat orientation, minimal supports

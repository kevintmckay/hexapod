// Export individual parts for 3D printing
// Usage: openscad -o stl/part.stl -D 'PART="coxa_bracket"' export_parts.scad

include <leg.scad>

PART = "preview";  // Options: coxa_bracket, femur_link, tibia_link, foot_tip, body_segment

if (PART == "coxa_bracket") {
    coxa_bracket();
} else if (PART == "femur_link") {
    femur_link();
} else if (PART == "tibia_link") {
    tibia_link();
} else if (PART == "foot_tip") {
    foot_tip();
} else if (PART == "body_segment") {
    body_segment();
} else {
    // Preview all parts
    preview();
}

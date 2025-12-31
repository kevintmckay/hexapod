#!/bin/bash
# Export all Big Hex STL files from OpenSCAD

SCAD_FILE="leg.scad"
OUTPUT_DIR="stl"

mkdir -p "$OUTPUT_DIR"

echo "Exporting Big Hex STL files..."

# Leg parts (need 6 of each except foot which is TPU)
echo "  coxa_bracket.stl..."
openscad -o "$OUTPUT_DIR/coxa_bracket.stl" \
    -D 'coxa_bracket();' \
    "$SCAD_FILE" 2>/dev/null

echo "  femur_link.stl..."
openscad -o "$OUTPUT_DIR/femur_link.stl" \
    -D 'femur_link();' \
    "$SCAD_FILE" 2>/dev/null

echo "  tibia_link.stl..."
openscad -o "$OUTPUT_DIR/tibia_link.stl" \
    -D 'tibia_link();' \
    "$SCAD_FILE" 2>/dev/null

echo "  foot_tip.stl (print in TPU)..."
openscad -o "$OUTPUT_DIR/foot_tip.stl" \
    -D 'foot_tip();' \
    "$SCAD_FILE" 2>/dev/null

echo "  standoff.stl..."
openscad -o "$OUTPUT_DIR/standoff.stl" \
    -D 'standoff();' \
    "$SCAD_FILE" 2>/dev/null

# Body plates - segmented (for standard ~220mm printers)
echo "  body_plate_segment_top.stl (for standard printers)..."
openscad -o "$OUTPUT_DIR/body_plate_segment_top.stl" \
    -D 'body_plate_segment(top=true, segment=0);' \
    "$SCAD_FILE" 2>/dev/null

echo "  body_plate_segment_bottom.stl (for standard printers)..."
openscad -o "$OUTPUT_DIR/body_plate_segment_bottom.stl" \
    -D 'body_plate_segment(top=false, segment=0);' \
    "$SCAD_FILE" 2>/dev/null

# Body plates - full (for large ~300mm+ printers)
echo "  body_plate_top_full.stl (for large printers)..."
openscad -o "$OUTPUT_DIR/body_plate_top_full.stl" \
    -D 'body_plate(top=true);' \
    "$SCAD_FILE" 2>/dev/null

echo "  body_plate_bottom_full.stl (for large printers)..."
openscad -o "$OUTPUT_DIR/body_plate_bottom_full.stl" \
    -D 'body_plate(top=false);' \
    "$SCAD_FILE" 2>/dev/null

echo ""
echo "Done! STL files in $OUTPUT_DIR/"
echo ""
echo "Print quantities:"
echo ""
echo "  OPTION A - Segmented body (standard ~220mm bed printers):"
echo "    body_plate_segment_top.stl     x6  (PETG)"
echo "    body_plate_segment_bottom.stl  x6  (PETG)"
echo ""
echo "  OPTION B - Full body (large ~300mm+ bed printers):"
echo "    body_plate_top_full.stl        x1  (PETG)"
echo "    body_plate_bottom_full.stl     x1  (PETG)"
echo ""
echo "  LEG PARTS (same for both options):"
echo "    coxa_bracket.stl               x6  (PETG)"
echo "    femur_link.stl                 x6  (PETG)"
echo "    tibia_link.stl                 x6  (PETG)"
echo "    foot_tip.stl                   x6  (TPU)"
echo "    standoff.stl                   x12 (PETG)"

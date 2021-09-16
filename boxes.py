#!/usr/bin/python3

import argparse
import csv

PREAMBLE = """
wall_thickness = 10;
floor_thickness = 10;

module box(x, y, z, width, depth, height, opacity, label) {
    color([.5, .5, .5, .5]) {
        translate([x, y, z]) {
            // make this hollow by subtracting an inner cube
            difference() {
                cube([width, depth, height]);
                translate([wall_thickness, wall_thickness, floor_thickness]) {
                    cube([width-2*wall_thickness, depth-2*wall_thickness, height]);
                }
            }
        }
    }
}
"""
POSTAMBLE = """"""

class Box(object):

    pass

    def __init__(self, data):
        self.location = data.get('location')
        self.width = float(data.get('width'))
        self.depth = float(data.get('depth'))
        self.height = float(data.get('height'))
        self.adjacent = data.get('adjacent')
        self.direction = data.get('direction')
        self.alignment = data.get('alignment')
        self.opacity = 1.0
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

    def __str__(self):
        return "<box %s of size [%g, %g, %g] at (%g, %g, %g) to %s of %s, %s-aligned>" % (
            self.location,
            self.width, self.depth, self.height,
            self.x, self.y, self.z,
            self.direction, self.adjacent, self.alignment)

    def write_scad(self, stream):
        stream.write("""box(%g, %g, %g, %g, %g, %g, %g, "%s");\n""" % (
            self.x, self.y, self.z,
            self.width, self.depth, self.height,
            self.opacity, self.location))

def process_with_dependents(boxes, dependents, box, level):
    if box.location in dependents:
        for dependent_name in dependents[box.location]:
            dependent = boxes[dependent_name]
            if dependent.direction == 'left':
                dependent.x = box.x - dependent.width
            elif dependent.direction == 'right':
                dependent.x = box.x + box.width
            elif dependent.direction == 'behind':
                dependent.y = box.y + box.depth
            elif dependent.direction == 'front':
                dependent.y = box.y - dependent.depth
            if dependent.alignment == 'left':
                dependent.x = box.x
            elif dependent.alignment == 'right':
                dependent.x = box.x + box.width - dependent.width
            elif dependent.alignment == 'front':
                dependent.y = box.y
            elif dependent.alignment == 'back':
                dependent.y = box.y + box.depth - dependent.depth
            process_with_dependents(boxes, dependents, dependent, level)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()

    with open(args.inputfile) as instream:
        boxes = {row['location']: Box(row)
                       for row in csv.DictReader(instream)}

    dependents = {}
    for box in boxes.values():
        adjacent = box.adjacent
        if adjacent == 'start':
            dependents['start'] = [box.location]
            first_box = box
        else:
            if adjacent not in dependents:
                dependents[adjacent] = []
            dependents[adjacent].append(box.location)
    if 'start' not in dependents:
        print("No starting point given")

    first_box.x = 0.0
    first_box.y = 0.0
    first_box.z = 0.0
    process_with_dependents(boxes, dependents, first_box, 1)

    with open(args.output, 'w') as outstream:
        outstream.write(PREAMBLE)
        for box in boxes.values():
            box.write_scad(outstream)
        outstream.write(POSTAMBLE)

if __name__ == '__main__':
    main()

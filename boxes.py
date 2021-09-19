#!/usr/bin/python3

import argparse
import csv

PREAMBLE = """
wall_thickness = %g;
floor_thickness = %g;
ceiling_thickness = %g;

module box(position, dimensions, opacity, label) {
    color([.5, .5, .5, .5]) {
        translate(position) {
            // make this hollow by subtracting an inner cuboid
            difference() {
                cube(dimensions);
                translate([wall_thickness/2, wall_thickness/2, floor_thickness]) {
                    cube([dimensions[0]-wall_thickness, dimensions[1]-wall_thickness, dimensions[2]-floor_thickness]);
                }
            }
        }
    }
}
"""
POSTAMBLE = """"""

class Box(object):

    """A cuboid positive space, such as a room, box, or shelf and the space it supports.
    Not a hole such as a door or window."""

    pass

    def __init__(self, data):
        self.box_type = data.get('type', 'room')
        self.location = data.get('location')
        self.dimensions = [float(data.get('width')),
                           float(data.get('depth')),
                           float(data.get('height'))]
        self.position = [0.0, 0.0, 0.0]
        self.adjacent = data.get('adjacent')
        self.direction = data.get('direction')
        self.alignment = data.get('alignment')
        self.offset = data.get('offset', 0.0)
        self.opacity = 1.0

    def __str__(self):
        return "<box %s of size %s at %s to %s of %s, %s-aligned>" % (
            self.location,
            self.dimensions,
            self.position,
            self.direction, self.adjacent, self.alignment)

    def write_scad(self, stream):
        stream.write("""box(%s, %s, %g, "%s");\n""" % (
            self.position,
            self.dimensions,
            self.opacity, self.location))

class Hole(object):

    """A cuboid negative space to punch out of the wall of a box such as room.
    This represents doors and windows."""

    pass

    def __init__(self, data):
        self.dimensions = [float(data.get('width')),
                           float(data.get('depth')), # from bottom to top of the hole
                           float(data.get('height'))] # from the floor to the bottom of the hole
        self.cut_out_from = data.get('adjacent')      # the room that this hole is in one of the walls of
        self.direction = data.get('direction')        # which wall the hole is in (front, left, back, right)
        self.offset = data.get('offset', 0.0)

class Constant(object):

    """A constant definition."""

    pass

    def __init__(self, data):
        self.name = data['location']
        self.value = data['width']
        self.all_data = data

# Define all the names for each of the functions to make an object
# from a spreadsheet row (since there are multiple names for each
# function, it is neater to write them this way, then invert the
# table):
names_for_makers = {
    lambda row: Box(row): ('room', 'shelf', 'shelves', 'box'),
    lambda row: Hole(row): ('door', 'window'),
    lambda row: Constant(row): ('constant',)}

# Invert the table, so we can look up row types in it:
makers = {
    name: maker
    for maker, names in names_for_makers.items()
    for name in names}

def process_with_dependents(boxes, dependents, box, level):
    if box.location in dependents:
        for dependent_name in dependents[box.location]:
            dependent = boxes[dependent_name]

            if isinstance(dependent, Box):

                for index, direction in enumerate(['right', 'behind', 'above']):
                    if dependent.direction == direction:
                        dependent.position[index] = box.position[index] + box.dimensions[index]

                for index, direction in enumerate(['left', 'front', 'below']):
                    if dependent.direction == direction:
                        dependent.position[index] = box.position[index] - dependent.dimensions[index]

                for index, direction in enumerate(['left', 'front', 'bottom']):
                    if direction in dependent.alignment:
                        dependent.position[index] = box.position[index] + dependent.offset

                for index, direction in enumerate(['right', 'back', 'top']):
                    if direction in dependent.alignment:
                        dependent.position[index] = box.position[index] + box.dimensions[index] - dependent.dimensions[index] + dependent.offset

            elif isinstance(dependent, Hole):
                box.holes.append(dependent)

            process_with_dependents(boxes, dependents, dependent, level)

DEFAULT_CONSTANTS = {
    'wall_thickness': 10,
    'floor_thickness': 10,
    'ceiling_thickness': -1     # so we can see into rooms from above
}

def add_default_constants(boxes):
    for default_name, default_value in DEFAULT_CONSTANTS.items():
        if default_name not in boxes:
            boxes[default_name] = Constant({'location': default_name, 'width': default_value})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()

    with open(args.inputfile) as instream:
        boxes = {row['location']: makers[row.get('type', 'room')](row)
                       for row in csv.DictReader(instream)}

    # Work out the tree structure of what depends on what:
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

    add_default_constants(boxes)

    wall_thickness = boxes['wall_thickness'].value
    floor_thickness = boxes['floor_thickness'].value
    ceiling_thickness = boxes['ceiling_thickness'].value

    # The dimensions of rooms are presumed to be given as internal:
    for box in boxes.values():
        if isinstance(box, Box) and box.box_type == 'room':
            box.dimensions[0] += wall_thickness # one half-thickness at each side
            box.dimensions[1] += wall_thickness # one half-thickness at each end
            box.dimensions[2] += floor_thickness + ceiling_thickness

    # Now process the tree
    first_box.position = [0.0, 0.0, 0.0]
    process_with_dependents(boxes, dependents, first_box, 1)

    with open(args.output, 'w') as outstream:
        outstream.write(PREAMBLE % (wall_thickness, floor_thickness, ceiling_thickness))
        for box in boxes.values():
            if isinstance(box, Box):
                box.write_scad(outstream)
        outstream.write(POSTAMBLE)

if __name__ == '__main__':
    main()

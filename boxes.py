#!/usr/bin/python3

import argparse
import csv

PREAMBLE = """
wall_thickness = %g;
floor_thickness = %g;
ceiling_thickness = %g;

module hole(preshift, rot, postshift, dimensions, label) {
    translate(preshift) rotate(rot) translate(postshift) cube(dimensions);
}

module box(position, dimensions, colour, label) {
    color(colour) {
        translate(position) {
            // make this hollow by subtracting an inner cuboid
            difference() {
                cube(dimensions);
                translate([wall_thickness/2, wall_thickness/2, floor_thickness]) {
                    cube([dimensions[0]-wall_thickness, dimensions[1]-wall_thickness, dimensions[2]-floor_thickness]);
                }
                children();
            }
        }
    }
}
"""
POSTAMBLE = """"""

# scratch = """
# box([0.0, 0.0, 0.0], [435.0, 385.0, 253.0], 1, "Living room") {
#      wallrotate = 90;
#      fromwall = 90;
#      fromfloor = 70;
#      width = 245;
#      height = 135;
#      rotate([0, 0, wallrotate]) {
#           translate([fromwall, -10, fromfloor]) {
#           cube([width, 20, height]);
#           }
#      }
# };
# """

class Box(object):

    """A cuboid positive space, such as a room, box, or shelf and the space it supports.
    Not a hole such as a door or window."""

    pass

    def __init__(self, data):
        self.box_type = data.get('type', 'room')
        self.name = data.get('name')
        self.dimensions = [float(data.get('width')),
                           float(data.get('depth')),
                           float(data.get('height'))]
        self.position = [0.0, 0.0, 0.0]
        self.adjacent = data.get('adjacent')
        self.direction = data.get('direction')
        self.alignment = data.get('alignment')
        self.offset = data.get('offset', 0.0) or 0.0
        self.holes = []
        self.colour = data.get('colour', [.5, .5, .5, .5])
        if self.colour == "":
            self.colour = [.5, .5, .5, .5]
        print(self.name, "has colour", self.colour)

    def __str__(self):
        return "<box %s of size %s at %s to %s of %s, %s-aligned>" % (
            self.name,
            self.dimensions,
            self.position,
            self.direction, self.adjacent, self.alignment)

    def write_scad(self, stream):
        stream.write("""box(%s, %s, %s, "%s") {\n""" % (
            self.position,
            self.dimensions,
            ('"%s"' % self.colour) if isinstance(self.colour, str) else self.colour,
            self.name))
        for hole in self.holes:
            hole.write_scad(stream)
        stream.write("""};\n""")

def cell_as_float(row, name):
    value = row.get(name)
    return 0 if value in (None, "") else float(value)

class Hole(object):

    """A cuboid negative space to punch out of the wall of a box such as room.
    This represents doors and windows."""

    pass

    def __init__(self, data):
        self.name = data['name']
        self.dimensions = [float(data.get('width')),  # from one side of the hole to the other
                           float(data.get('depth')),  # from bottom to top of the hole
                           0]                         # fill in the thickness of the hole later
        self.adjacent = data.get('adjacent')          # the room that this hole is in one of the walls of
        self.direction = data.get('direction')        # which wall the hole is in (front, left, back, right)
        self.height = cell_as_float(data, 'height')   # from the floor to the bottom of the hole
        self.offset = cell_as_float(data, 'offset')   # how far from the start of the wall the hole starts
        self.preshift = [0, 0, 0]                     # translate to the start of the wall the hole is in
        self.rotate = 0                               # rotate to match the wall
        self.postshift = [0, 0, 0]                    # translate to the right place on the wall

    def write_scad(self, stream):
        stream.write("""    hole(%s, %s, %s, %s, "%s");\n""" % (
            self.preshift,
            self.rotate,
            self.postshift,
            self.dimensions,
            self.name))

class Constant(object):

    """A constant definition."""

    pass

    def __init__(self, data):
        self.name = data['name']
        self.value = data['width']
        self.all_data = data

class Type(object):

    """A type definition.

    Not implemented yet."""

    pass

    def __init__(self, data):
        self.data = data
        self.name = data['name']
        makers[self.name] = makers['__custom__']

class Custom(object):

    """A custom type, as defined by the Type type of row."""

    pass

    def __init__(self, data):
        self.data = data

# Define all the names for each of the functions to make an object
# from a spreadsheet row (since there are multiple names for each
# function, it is neater to write them this way, then invert the
# table):
names_for_makers = {
    lambda row: Box(row): ('room', 'shelf', 'shelves', 'box'),
    lambda row: Hole(row): ('door', 'window'),
    lambda row: Constant(row): ('constant',),
    lambda row: Type(row): ('type',),
    lambda row: Custom(row): ('__custom__',)}

# Invert the table, so we can look up row types in it:
makers = {
    name: maker
    for maker, names in names_for_makers.items()
    for name in names}

def process_with_dependents(boxes, dependents, box, level):
    if box.name in dependents:
        for dependent_name in dependents[box.name]:
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
            boxes[default_name] = Constant({'name': default_name, 'width': default_value})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()

    with open(args.inputfile) as instream:
        boxes = {row['name']: makers[row.get('type', 'room')](row)
                       for row in csv.DictReader(instream)}

    # Work out the tree structure of what depends on what:
    dependents = {}
    for box in boxes.values():
        if not (isinstance(box, Box) or isinstance(box, Hole)):
            continue
        adjacent = box.adjacent
        if adjacent == 'start':
            dependents['start'] = [box.name]
            first_box = box
        else:
            if adjacent not in dependents:
                dependents[adjacent] = []
            dependents[adjacent].append(box.name)
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
        elif isinstance(box, Hole):
            box.dimensions[2] = wall_thickness * 2

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

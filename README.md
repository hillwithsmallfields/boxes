# boxes

A program that takes a CSV file giving the dimensions and relative
positions of rooms, and outputs an OpenSCAD file showing the building.

Rooms can be placed relative to other rooms (left, right, behind,
front) in one dimension, and which edge lines up with the room they're
relative to to locate them in the other dimension.

I'm working on getting doors and windows drawn --- ones going through
to the outside work OK, I think (although on a temporary hack with
some inline constants) but those between rooms need to be part of both
rooms, to make them cut all the way through.

Later versions should allow things (boxes, cupboards etc) to be placed
inside the rooms, using transparency to make the nesting visible.

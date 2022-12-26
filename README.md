# Boxes

A program that takes a CSV file giving the dimensions and relative
positions of rooms, doors and windows in a building, and outputs an
OpenSCAD file showing the building.

Rooms can be placed relative to other rooms (left, right, behind,
front) in one dimension, and which edge lines up with the room they're
relative to to locate them in the other dimension.

The features form a tree structure, with an implicit starting element called
'start', which is located at [0, 0, 0].

There are two general types of features, positive and negative.  The
negative features combine to form a shape which is punched out of the
combined positive features.  It's done this way so that a door or
window betwen rooms will punch through the wall elements of both the
rooms it connects, rather than just cutting it out of the room it's
defined relative to.

Positive feature types are `room`, `shelves`, `shelf`, and `box`, of
which you should expect only `room` to work at the moment.

Negative feature types are `door`, `window`, and `join`.  `door` and
`window` are identical in effect; `join` is to put where two room
cuboids are to join together into one room, for example a corridor
that goes round a corner; `join` adjusts the size of the whole so that
you can give the same size as the room it joins, and the wall
thickness will be taken off it.

# Input columns

## type

The type may be any of the positive or negative types mentioned above.

## name

An arbitrary name, for the users' convenience.  It is not currently
visible in the resulting picture, although it is passed on in the SCAD
model and could potentially be rendered.

## width

For a positive feature, this is how far it extends in the direction
parallel to the front wall of the building.

For a negative feature, this is how far it extends along the wall it
is placed in.

## depth

For a positive feature, this is how far the feature extends in the
direction going back into the building from the front.

For a negative feature, this is how tall the feature is.

## height

For a positive feature, this is how tall the feature is.

For a negative feature, this is how high above the floor the feature
starts.

## adjacent

For a positive feature, this is the `name` field value of the
already-defined positive feature this one is placed relative too.  For
example, if the kitchen is behind the dining room, the row with the
`name` field set to `kitchen` has the `adjacent` field set to `dining
room`.

For a negative feature, this defines which positive feature this
feature defines a hole in.

## direction

For a positive feature, this is used with the `adjacent` field to
place a room.  It may take the values `front`, `behind`, `left`,
`right`, `above`, or `below`.

The current feature is placed after the feature it is adjacent to, in
the appropriate direction.

For a negative feature, this defines which wall of the `adjacent`
positive feature it is a hole in.

## alignment

This sets how the feature is placed relative to its `adjacent` feature
in the other horizontal direction.  In the example above, if the
right-hand ends of the kitchen and dining room line up, the `kitchen`
row would have an `alignment` of `right`.

## offset

For a positive feature, if neither end of a room is aligned with the
corresponding end of its `adjacent` room, the `offset` field can be
used with the `alignment` field to get the necessary positioning.

For a negative feature, this is how far along the relevant wall this
hole starts.

## colour

The colour the room is rendered in in OpenSCAD.

# Future work

Later versions should allow things (boxes, cupboards etc) to be placed
inside the rooms, using transparency to make the nesting visible.

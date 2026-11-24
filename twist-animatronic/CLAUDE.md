# Notes for working on the Twist animatronic

Written from the user's earlier chats. Update it when something changes. Anything marked "unknown" has not been told to me.

## Printer and materials

- Printer: Artillery Sidewinder X1, 300 x 300 mm bed, direct drive, running Klipper.
- Hot end tops out at 240 C (stock). Bed is glass, so use glue stick with PETG and let it cool before removing parts.
- Material: PETG. Slicer used so far: PrusaSlicer, profile at `print/scad/artillery_x1_PETG.ini`.
- G-code for Klipper: use `gcode_flavor = klipper`. The user's own start macro name (for example `PRINT_START`) is unknown, so the profile uses plain G-code that Klipper accepts. Ask before assuming macro names.
- The user prefers everything on one plate where it fits.

## Where they are

- UK. Use pounds and UK retailers (Cool Components, The Pi Hut, Pimoroni, Kunkune, Amazon UK, eBay UK). Do not assume US sizes: 26.7 mm pipe is hard to find in the UK, so default to the 25 mm pipe parts.
- AliExpress prices I quoted were from memory and were unverified. The user says they are not seeing them. Ask what they see before relying on any.

## The project

- Twist is a hand puppet. The rig replaces the hand and goes in through the hole in his back. Puppet measurements are unknown (head width and depth, neck opening, back-hole size and height).
- Current design is version 2 (cable-driven head, 13 servo axes). Version 1 is at commit `ba3692b`.
- User wants it cheap: scrap motors and parts welcome (noise is fine), timber and pipe over printing, and printed replacements for cheap hardware (M5 washers, knobs, standoffs, sheath clips, GT2 pulleys). No speaker mount in the small-parts set.
- Scrap source being considered: a lot of three stage moving heads (two Equinox Fusion 100 Spot style, one Chauvet Intimidator), a Chauvet Funfetti Shot and an ADJ Entour Faze fog machine for about 60 to 80 pounds. Unknown whether it was bought, whether it works, and what motors are inside. Ask for motor photos and labels (size, shaft, wire count) before designing a stepper version.
- Servo stack so far: 11 MG996R 180 degree and 2 DS3218 for the body lean. A stepper version was discussed but not drawn. If drawn, keep the two DS3218 on the lean.
- Power: a salvaged supply was mentioned but its type and voltage are unknown. The barrel jack is only needed for a matching brick.

## How the user likes answers

- Short and plain. Tables for lists. Say what was and wasn't verified. Mark guesses as guesses.

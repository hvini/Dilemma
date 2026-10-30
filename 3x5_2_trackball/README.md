# Dilemma DIY V2 - trackball

The `3x5_2` DIY board with its unused trackball connector (J7) placed and routed. Everything else, including the outline, is unchanged.

**Order:** upload `dilemma_3x5_2_trackball_gerber.zip`. The board is reversible, so one design makes both halves. On the left half, leave J7 empty.

KiCad files need KiCad 8 or newer.

Build guide with BOM, for OLED left and trackball right (Brazilian Portuguese): [guia_de_montagem.md](guia_de_montagem.md)

## J7 pinout

J7 is a 2x3, 2.54mm header with through-hole pads, so you can solder from either face. Each pin is labelled on the silkscreen.

| Pin | Silk | Signal   | Controller pin (RP2040) |
| --- | ---- | -------- | ----------------------- |
| 1   | V+   | Vcc      | VCC (3.3V)              |
| 2   | CK   | SPI SCK  | GP22                    |
| 3   | MI   | SPI MISO | GP20                    |
| 4   | MO   | SPI MOSI | GP23                    |
| 5   | CS   | SPI CS   | GP21                    |
| 6   | G    | GND      | GND                     |

These are the same GPIOs as the PCBA trackball schematic (`3x5_3_trackball/schematic.pdf`). The pin order differs from the J7 in the `3x5_2` schematic, because a 2x3 header needs this order to route without crossings.

Check that your sensor board accepts 3.3V on V+.

## Mechanical notes

- `mechanical/trackball` parts screw into H6-H9, the four Cirque mod holes. The hole pattern is the same as on the PCBA board.
- On the right half, the B.Cu face points up, so the holder goes on that face.
- The ball sits over the controller, so the holder can't be bolted flat. Raise it on M3x10 female-female standoffs. The 10mm is an estimate, so dry-fit the controller and sensor before final assembly.
- J7 sits under the holder plate. Solder wires directly, or use a low-profile header.
- Use `mechanical/cases/3x5_2/thin` as the case. The `3x5_3_trackball` case matches the switches, H2 and the USB opening, but its contour wall has no opening for the TRRS jack, and its bottom plate sits against the solder joints.
- J7 is close to the J3 battery connector: their courtyards overlap by 0.5mm, but the parts themselves should clear by about 0.45mm.

## Firmware

Trackball only: enable the PMW33xx driver on SPI0 with the pins above, and set the right half as the pointing side.

Cirque on the left and trackball on the right: QMK allows one `POINTING_DEVICE_DRIVER` per build, so this needs `POINTING_DEVICE_DRIVER = custom` with your own code calling both sensors. No firmware is included here, and this combination has not been tested.

## Trackball parts

Sizes are measured from the STLs; the repo has no parts list.

| Part                                   | Qty | Notes                                 |
| -------------------------------------- | --- | ------------------------------------- |
| PMW3360 board with LM19-LSI lens       | 1   | Must fit under the holder's 19x24mm window |
| 34mm trackball                         | 1   | Holder cavity fits a 34mm ball        |
| MR63ZZ bearing (3x6x2.5mm)             | 3   | Size inferred from the 2.6mm wide slots |
| 3mm pin, 8mm long                      | 3   | Bearing axles                         |
| M3 screws, nuts and standoffs          | 4   | Length depends on the standoff height |

The holder has no screw posts for the sensor board. The board has to be fixed under the plate with the lens in the window, about 2.4mm from the ball (datasheet figure, from memory).

To reuse a Charybdis sensor PCB with the unmodified `mechanical/trackball` parts:

- The board is about 42mm across, so it overlaps H7 and H8. Use only three standoffs, at H6, H7 and H9, and leave H8 empty.
- Place the lens in the holder window with the board's 6-pin header on the J7 side.
- Mark H7 on the board's rim through the holder's hole, then file a notch about 3mm deep there. This spot has no copper within about 6mm of the hole centre, but dry-fit before cutting.
- Fix the board under the plate with double-sided tape about 0.5mm thick. This also sets the lens height to match the Charybdis.
- Wire 3.3V to V+, GND to G, SCK to CK, MISO to MI, MOSI to MO and SS to CS.

## Assembly warnings

- Jumpers JP1-JP8: solder one face only, on the left half only. Each header pin has two jumpers, one per face, so soldering both shorts signals to power or GND.
- OLED on the left half: with the F-face jumpers (JP1, JP3, JP5, JP7) and the F face up, the O2 pins read SDA, SCL, VCC, GND from left to right, with the controller above O2. Check this against the labels on your module, because VCC and GND positions vary between modules.
- Fit the right half's reset button on the bottom face (F side). The top is covered by the holder.
- Never plug or unplug the TRRS cable with USB connected. It carries 3.3V.
- Under the PCB, use low-head M3 screws at H6, H7 and H9. The `3x5_2/thin` case has about 3.4mm of room there.

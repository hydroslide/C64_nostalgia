# Pi1541 case (3D printing)

3D-printable case models for [Pi1541](https://cbm-pi1541.firebaseapp.com/), the
cycle-exact Commodore 1541 floppy emulator, styled after the original C64/1541
hardware. Starts from two donor designs and converts them to fit a Raspberry Pi
Zero:

- **`real_files/source/`** — [DeeKay64's full-size Pi1541 case](https://www.thingiverse.com/thing:4892996)
  (Raspberry Pi 3B, C64/1541 styling). This is the shell being adapted.
- **`real_files/target/`** — the "PI1541 Zero Case", used as the donor for
  Pi Zero board geometry (mounting posts, port/button cutouts).
- **`output/`** — print-ready STLs: the converted case (bottom/top, in slotted
  and non-slotted variants) plus bezel and button-nub parts. The nubs have a
  side-entry cup, so the board drops straight into the top rather than having to
  be wiggled onto the switches; fit them with the open side facing the case floor.
- **`tools/`** — the Python build pipeline that does the conversion (fills the
  Pi 3B's holes, cuts the Zero's holes, transfers mounting posts). See
  [`tools/README.md`](tools/README.md) for the full workflow.
- **`docs/renders/`** — render images used to check each revision.
- **`files/`** — the original compact Pi 3A remix (3mf + label PDFs) this
  project also drew reference from.
- **`images/`** — reference photos of the real printed case.

See [`tools/README.md`](tools/README.md) for build instructions and the layout
of intermediate/output folders.

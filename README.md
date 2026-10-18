# STAMPER

A simple Windows program that prints the date and time a photo was taken onto the photo itself. Made for phones (like the Galaxy S9) whose camera can't add date stamps.

The stamp is white text with a black outline, so it reads on any picture. The date comes from the photo's hidden EXIF data.

## For users

1. Download `STAMPER.exe` (see the Releases page).
2. Put it in its own folder. On first launch it creates three folders next to itself:
   - `1 - Pictures That Need Stamps`
   - `2 - Stamped Pictures`
   - `3 - Originals Already Stamped`
3. Follow the four steps in the window:
   1. Put your pictures in Folder 1.
   2. Press GO. (Use "Stamp position and size..." first if you want to move or resize the date.)
   3. Check Folder 2 for the stamped pictures.
   4. Check Folder 3 for the originals.

Notes:
- Windows may show "Windows protected your PC" because the program is not code-signed. Click "More info", then "Run anyway".
- Only `.jpg` / `.jpeg` files are handled. Photos with no date saved in them stay in Folder 1.
- The original moves to Folder 3 only after the stamped copy is saved. Nothing is overwritten.

## Building from source

Needs Python 3.13 on Windows. Run `build.bat`. The program appears at `dist\STAMPER.exe`.

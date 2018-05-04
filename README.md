# DsStoreParser.py
macOS .DS_Store Parser

## Usage
```
usage: DsStoreParser.py [-h] -s SOURCE

.DS_Store Parser CLI tool.

optional arguments:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        The source file to parse.
```

## Example Output
Tab delimited output:
```
M1-Test-Shared_Folder_Desktop	PlistCodec	bwsp	{'ShowStatusBar': False, 'WindowBounds': '{{233, 313}, {770, 437}}', 'ContainerShowSidebar': True, 'SidebarWidth': 192, 'ShowTabView': False, 'PreviewPaneVisibility': False, 'ShowToolbar': True, 'ShowSidebar': True, 'ShowPathbar': False}
M1-Test-Shared_Folder_Desktop	blob	dilc	0000000000010000ffffffc50000011f00016f7c00008bf6ffffffffffff0000
M1-Test-Shared_Folder_Desktop	comp	lg1S	12300
M1-Test-Shared_Folder_Desktop	dutc	moDD	2017-09-12 22:03:23
```

# DSStore Record Types
MacOS DSStore Record Types from http://search.cpan.org/~wiml/Mac-Finder-DSStore/DSStoreFormat.pod.


BKGD:	 12-byte blob, directories only. Indicates the background of the Finder window viewing this directory (in icon mode). The format depends on the kind of background: Default background FourCharCode DefB, followed by eight unknown bytes, probably garbage. Solid color FourCharCode ClrB, followed by an RGB value in six bytes, followed by two unknown bytes. Picture FourCharCode PctB, followed by the the length of the blob stored in the 'pict' record, followed by four unknown bytes. The 'pict' record points to the actual background image.


ICVO:	 bool, directories only. Unknown meaning. Always seems to be 1, so presumably 0 is the default value.


Iloc:	 16-byte blob, attached to files and directories. The file's icon location. Two 4-byte values representing the horizontal and vertical positions of the icon's center (not top-left). (Then, 6 bytes 0xff and 2 bytes 0?) For the purposes of the center, the icon only is taken into account, not any label. The icon's size comes from the icvo blob.


LSVO:	 bool, attached to directories. Purpose unknown.


bwsp:	 A blob containing a binary plist. This contains the size and layout of the window (including whether optional parts like the sidebar or path bar are visible). This appeared in Snow Leopard (10.6). The plist contains the keys WindowBounds (a string in the same format in which AppKit saves window frames); SidebarWidth (a float), and booleans ShowSidebar, ShowToolbar, ShowStatusBar, and ShowPathbar. Sometimes contains ViewStyle (a string), TargetURL (a string), and TargetPath (an array of strings).


cmmt:	 ustr, containing a file's "Spotlight Comments". (The comment is also stored in the com.apple.metadata:kMDItemFinderComment xattr; this copy may be historical.)


dilc:	 32-byte blob, attached to files and directories. Unknown, may indicate the icon location when files are displayed on the desktop.


dscl:	 bool, attached to subdirectories. Indicates that the subdirectory is open (disclosed) in list view.


extn:	 ustr. Often contains the file extension of the file, but sometimes contains a different extension. Purpose unknown.


fwi0:	 16-byte blob, directories only. Finder window information. The data is first four two-byte values representing the top, left, bottom, and right edges of the rect defining the content area of the window. The next four bytes represent the view of the window: icnv is icon view, other values are clmv and Nlsv. The next four bytes are unknown, and are either zeroes or 00 01 00 00. On Leopard (10.5), the view-type information seems to be ignored, but see vstl. On Snow Leopard (10.6), some more of this record's function seems to have been taken over by the plist records bwsp, lsvp, and and lsvP.


fwsw:	 long, directories only. Finder window sidebar width, in pixels/points. Zero if collapsed.


fwvh:	 shor, directories only. Finder window vertical height. If present, it overrides the height defined by the rect in fwi0. The Finder seems to create these (at least on 10.4) even though it will do the right thing for window height with only an fwi0 around, perhaps this is because the stored height is weird when accounting for toolbars and status bars.


GRP0:	 ustr. Unknown; I've only seen this once.


icgo:	 8-byte blob, directories (and files?). Unknown. Probably two integers, and often the value 00 00 00 00 00 00 00 04.


icsp:	 8-byte blob, directories only. Unknown, usually all but the last two bytes are zeroes.


icvo:	 18- or 26-byte blob, directories only. Icon view options. There seem to be two formats for this blob. If the first 4 bytes are "icvo", then 8 unknown bytes (flags?), then 2 bytes corresponding to the selected icon view size, then 4 unknown bytes 6e 6f 6e 65 (the text "none", guess that this is the "keep arranged by" setting?). If the first 4 bytes are "icv4", then: two bytes indicating the icon size in pixels, typically 48; a 4CC indicating the "keep arranged by" setting (or none for none or grid for align to grid); another 4CC, either botm or rght, indicating the label position w.r.t. the icon; and then 12 unknown bytes (flags?). Of the flag bytes, the low-order bit of the second byte is 1 if "Show item info" is checked, and the low-order bit of the 12th (last) byte is 1 if the "Show icon preview" checkbox is checked. The tenth byte usually has the value 4, and the remainder are zero.


icvp:	 A blob containing a plist, giving settings for the icon view. Appeared in Snow Leopard (10.6), probably supplanting 'icvo'. The plist holds a dictionary with several key-value pairs: booleans showIconPreview, showItemInfo, and labelOnBottom; numbers scrollPositionX, scrollPositionY, gridOffsetX, gridOffsetY, textSize, iconSize, gridSpacing, and viewOptionsVersion; string arrangeBy. The value of the backgroundType key (an integer) presumably controls the presence of further optional keys such as backgroundColorRed/backgroundColorGreen/backgroundColorBlue.


icvt:	 shor, directories only. Icon view text label (filename) size, in points.


info:	 40- or 48-byte blob, attached to directories and files. Unknown. The first 8 bytes look like a timestamp as in dutc.


logS or lg1S:	 comp, directories only. Appears to contain the logical size in bytes of the directory's contents, perhaps as a cache to speed up display in the Finder. I think that 'logS' appeared in 10.7 and was supplanted by 'lg1S' in 10.8. See also 'ph1S'.


lssp:	 8-byte blob, directories only. Unknown. Possibly the scroll position in list view mode?


lsvo:	 76-byte blob, directories only. List view options. Seems to contain the columns displayed in list view, their widths, and their sort ordering if any. Presumably supplanted by lsvp and/or lsvP. These list view settings are shared between list view and the list portion of coverflow view.


lsvt:	 shor, directories only. List view text (filename) size, in points.


lsvp:	 A blob containing a binary plist. List view settings, perhaps supplanting the 'lsvo' record. Appeared in Snow Leopard (10.6). The plist contains boolean values for the keys showIconPreview, useRelativeDates, and calculateAllSizes; numbers for scrollPositionX, scrollPositionY, textSize, iconSize, and viewOptionsVersion (typically 1); and a string, sortColumn. There is also a columns key containing the set of columns, their widths, visibility, column ordering, sort ordering. The only difference between lsvp and lsvP appears to be the format of the columns specification: an array or a dictionary.


lsvP:	 A blob containing a binary plist. Often occurs with lsvp, but may have appeared in 10.7 or 10.8.


modD and moDD:	 dutc timestamps; directories only. One or both may appear. Typically the same as the directory's modification date. Unknown purpose; appeared in 10.7 or 10.8. Possibly used to detect when logS needs to be recalculated?


phyS or ph1S:	 comp, directories only. This number is always a multiple of 8192 and slightly larger than 'logS' / 'lg1S', which always seems to be present if this is (though the reverse is not always true). Presumably it is the corresponding physical size (an integer number of 8k-byte disk blocks).


pict:	 Variable-length blob, directories only. Despite the name, this contains not a PICT image but an Alias record (see Inside Macintosh: Files) which resolves to the file containing the actual background image. See also 'BKGD'.


vSrn:	 long, attached to directories. Always appears to contain the value 1. Appeared in 10.7 or 10.8.


vstl:	 type, directories only. Indicates the style of the view (one of icnv, clmv, Nlsv, or Flwv, indicating respectively: icon view, column/browser view, list view, and coverflow view) selected by the Finder's "Always open in icon [or other style] view" checkbox. This appears to be a new addition to the Leopard (10.5) Finder.






# ArcGIS STAC Browser

ArcGIS STAC Browser is a starter implementation for an ArcGIS Pro extension workflow that:

- reads a STAC catalog URL from an ArcGIS Cloud Store connection file (.acs)
- lists STAC collections and items
- lets a user select an item in a dialog
- adds supported raster assets from the selected item to the active map

## Current Scope

This repository currently provides the Python logic and a DAML UI definition scaffold.

- Python modules are in src/
- UI definition is in Config.daml
- button icons are in images/

If you want a production ArcGIS Pro installable add-in package, you still need the ArcGIS Pro SDK add-in project shell that compiles to .esriAddInX and hosts this logic.

## Prerequisites

- ArcGIS Pro 3.x
- Access to an ArcGIS Pro Python environment
- Network access to your STAC endpoint
- A valid .acs file that contains or resolves to a STAC catalog URL

## Install Python Dependencies

Install dependencies into the same Python environment ArcGIS Pro will use.

From this repository root:

```powershell
python -m pip install -e .
```

Or, if using ArcGIS Pro's conda environment explicitly:

```powershell
"C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat" -m pip install -e .
```

## How To Run In ArcGIS Pro (Developer Workflow)

Use these steps to validate behavior now:

1. Open ArcGIS Pro and open or create a project.
2. Open a map so there is an active map pane.
3. Open the Python window in ArcGIS Pro.
4. Add this repo's src folder to sys.path in the Python window.
5. Run the button click handler logic directly.

Example:

```python
import sys
sys.path.insert(0, r"C:\Data\repos\arcgis-stac\src")

from read_stac import OpenSTACBrowserButton
OpenSTACBrowserButton().onClick()
```

The STAC browser dialog should open.

## Using The Dialog

1. Click Browse... and select your .acs file.
2. Click Load Catalog.
3. Select a collection on the left.
4. Select an item on the right.
5. Click OK to add recognized raster assets to the active map.

Supported raster formats are identified by media type or extension, including tiff, jp2, png, and jpeg assets.

## Where The Button Will Appear (When Hosted As Add-in)

Per Config.daml, the command is configured as:

- Button caption: Browse STAC
- Group caption: STAC
- Ribbon tab: Map (tab id esri_mapping_homeTab)

So when the add-in host is in place, you will find the command in the Map tab under a STAC group.

## File Map

- Config.daml: add-in UI command and ribbon placement
- src/acs_reader.py: extracts catalog URL from .acs (JSON or XML)
- src/stac_reader.py: opens catalog and fetches collections/items
- src/stac_dialog.py: PyQt5 dialog for browsing collections and items
- src/read_stac.py: command entry point and add-to-map logic

## Troubleshooting

- Dialog does not open:
	- Ensure ArcGIS Pro Python has PyQt5 available (bundled in Pro environments).
- No items listed:
	- Verify your .acs resolves to a reachable STAC URL.
	- Confirm the selected collection actually has items.
- Nothing added to map:
	- Confirm an active map pane is open.
	- Check that selected item has raster-compatible assets.

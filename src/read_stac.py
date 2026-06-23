"""
read_stac.py
------------
ArcGIS Pro Python Add-in entry point.

The ``OpenSTACBrowserButton`` class is referenced by ``Config.daml`` via:

    className="read_stac.OpenSTACBrowserButton"

When the user clicks the ribbon button ArcGIS Pro calls ``onClick``, which
opens the :class:`~stac_dialog.STACBrowserDialog`.  If the user confirms a
selection the chosen STAC item's raster assets are added to the active map.
"""
from __future__ import annotations

import os
import sys

# Ensure the src/ directory is on sys.path when loaded by ArcGIS Pro so that
# sibling modules (stac_reader, acs_reader, stac_dialog) are importable.
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)


class OpenSTACBrowserButton:
    """Ribbon button that launches the STAC Catalog Browser dialog."""

    # ArcGIS Pro calls these lifecycle methods; they must exist even if empty.
    def __init__(self) -> None:  # noqa: D107
        pass

    def onClick(self) -> None:  # noqa: N802
        """Open the STAC browser and add selected assets to the active map."""
        import arcpy

        from stac_dialog import STACBrowserDialog

        dlg = STACBrowserDialog()
        if dlg.exec_() != STACBrowserDialog.Accepted:
            return

        item = dlg.selected_item
        if item is None:
            return

        _add_item_to_map(item)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _add_item_to_map(item) -> None:  # item: pystac.Item
    """Add raster/imagery assets from a STAC item to the current Pro map."""
    import arcpy

    aprx = arcpy.mp.ArcGISProject("CURRENT")
    active_map = aprx.activeMap
    if active_map is None:
        arcpy.AddError(
            "No active map found. Open or activate a map before using STAC Browser."
        )
        return

    _RASTER_EXTENSIONS = {".tif", ".tiff", ".img", ".jp2", ".png", ".jpg", ".jpeg"}
    _RASTER_MEDIA_TYPES = {"image/tiff", "image/jpeg", "image/png", "image/jp2"}

    added = 0
    for asset_key, asset in item.assets.items():
        href: str = asset.href
        media_type: str = (getattr(asset, "media_type", "") or "").lower()
        ext = os.path.splitext(href.split("?")[0])[1].lower()

        if media_type in _RASTER_MEDIA_TYPES or ext in _RASTER_EXTENSIONS:
            try:
                active_map.addDataFromPath(href)
                arcpy.AddMessage(f"Added asset '{asset_key}': {href}")
                added += 1
            except Exception as exc:
                arcpy.AddWarning(f"Could not add asset '{asset_key}': {exc}")

    if added == 0:
        arcpy.AddMessage(
            f"No recognised raster assets found in STAC item '{item.id}'."
        )

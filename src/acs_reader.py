"""
acs_reader.py
-------------
Parse an ArcGIS Cloud Store connection file (.acs) and extract the STAC
catalog URL.

ACS files are either JSON or XML.  For a STAC endpoint the URL is stored in
a field such as ``serviceUrl``, ``url``, ``endpoint``, or ``connectionString``.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path


# Field names that may hold the catalog URL, in priority order.
_URL_KEYS = ("serviceUrl", "catalogUrl", "url", "endpoint", "connectionString")


def read_catalog_url(acs_path: str | Path) -> str:
    """Return the STAC catalog URL embedded in *acs_path*.

    Parameters
    ----------
    acs_path:
        Absolute or relative path to an ``.acs`` file.

    Returns
    -------
    str
        The HTTP(S) URL of the STAC catalog.

    Raises
    ------
    FileNotFoundError
        If *acs_path* does not exist.
    ValueError
        If the file cannot be parsed or no URL is found.
    """
    path = Path(acs_path)
    if not path.exists():
        raise FileNotFoundError(f"ACS file not found: {path}")

    content = path.read_text(encoding="utf-8").strip()

    # --- Try JSON ---------------------------------------------------------
    if content.startswith("{"):
        try:
            return _url_from_json(json.loads(content))
        except (json.JSONDecodeError, ValueError):
            pass

    # --- Try XML ----------------------------------------------------------
    if content.startswith("<"):
        try:
            return _url_from_xml(ET.fromstring(content))
        except (ET.ParseError, ValueError):
            pass

    raise ValueError(
        f"Could not extract a STAC catalog URL from '{path}'. "
        "Ensure the file is a valid ACS JSON or XML connection file."
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _url_from_json(data: dict, _depth: int = 0) -> str:
    """Recursively search a JSON dict for an HTTP URL."""
    if _depth > 5:
        raise ValueError("URL not found (max recursion depth reached)")

    for key in _URL_KEYS:
        value = data.get(key)
        if isinstance(value, str) and value.lower().startswith("http"):
            return value

    # Recurse into nested objects
    for value in data.values():
        if isinstance(value, dict):
            try:
                return _url_from_json(value, _depth + 1)
            except ValueError:
                pass

    raise ValueError("No HTTP URL found in ACS JSON data")


def _url_from_xml(root: ET.Element) -> str:
    """Search XML elements and attributes for an HTTP URL."""
    url_attrs = {"url", "serviceurl", "endpoint", "href", "catalogurl"}

    for elem in root.iter():
        # Check element text
        text = (elem.text or "").strip()
        if text.lower().startswith("http"):
            return text

        # Check attributes (case-insensitive key match)
        for attr, val in elem.attrib.items():
            if attr.lower() in url_attrs and val.lower().startswith("http"):
                return val

    raise ValueError("No HTTP URL found in ACS XML data")

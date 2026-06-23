"""
stac_reader.py
--------------
Thin wrapper around pystac-client for opening a STAC catalog, listing
collections, and fetching items from a collection.
"""
from __future__ import annotations

from typing import Any

import pystac
from pystac_client import Client


def open_catalog(url: str) -> Client:
    """Open a STAC catalog or API endpoint.

    Parameters
    ----------
    url:
        Root URL of the STAC catalog or STAC API (``/`` endpoint).

    Returns
    -------
    pystac_client.Client
    """
    return Client.open(url)


def get_collections(catalog: Client) -> list[dict[str, str]]:
    """Return a summary list of all collections in *catalog*.

    Each entry contains:
    - ``id``          – collection identifier
    - ``title``       – human-readable title (falls back to id)
    - ``description`` – short description
    """
    result: list[dict[str, str]] = []
    for col in catalog.get_collections():
        result.append(
            {
                "id": col.id,
                "title": col.title or col.id,
                "description": col.description or "",
            }
        )
    return result


def get_collection_items(
    catalog: Client,
    collection_id: str,
    max_items: int = 100,
) -> list[dict[str, Any]]:
    """Return a summary list of items from *collection_id*.

    Uses the STAC API ``/search`` endpoint when available so that large
    collections are paged efficiently.

    Each entry contains:
    - ``id``       – item identifier
    - ``datetime`` – acquisition datetime (string)
    - ``bbox``     – bounding box [west, south, east, north] or ``None``
    - ``assets``   – list of asset key names
    - ``item``     – the underlying :class:`pystac.Item` (for later use)
    """
    search = catalog.search(collections=[collection_id], max_items=max_items)

    result: list[dict[str, Any]] = []
    for item in search.items():
        result.append(
            {
                "id": item.id,
                "datetime": str(item.datetime) if item.datetime else "",
                "bbox": item.bbox,
                "assets": list(item.assets.keys()),
                "item": item,
            }
        )
    return result

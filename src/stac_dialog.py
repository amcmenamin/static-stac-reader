"""
stac_dialog.py
--------------
PyQt5 dialog for the STAC Catalog Browser.

ArcGIS Pro ships PyQt5, so no separate install is needed inside the Pro
Python environment.

Layout
------
  [ACS file path ________________] [Browse…] [Load Catalog]

  +-- Collections --------+  +-- Items ----------------------------+
  |  <list of collections>|  |  <list of items in selected coll.> |
  +-----------------------+  +-------------------------------------+

  Item detail (id, datetime, bbox, assets)

  [OK]  [Close]

Selecting OK will close the dialog; ``selected_item`` exposes the chosen
``pystac.Item`` to the caller.
"""
from __future__ import annotations

from typing import Any

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFileDialog,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QSplitter,
        QVBoxLayout,
    )
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "PyQt5 is required. It is bundled with ArcGIS Pro; ensure this "
        "script runs inside the ArcGIS Pro Python environment."
    ) from exc

import pystac

from acs_reader import read_catalog_url
from stac_reader import get_collection_items, get_collections, open_catalog


class STACBrowserDialog(QDialog):
    """Two-pane dialog: left = collections, right = items."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("STAC Catalog Browser")
        self.setMinimumSize(800, 520)

        self._catalog = None
        self._collections: list[dict[str, str]] = []

        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def selected_item(self) -> pystac.Item | None:
        """The :class:`pystac.Item` the user highlighted, or ``None``."""
        current = self._item_list.currentItem()
        if current is not None:
            data: dict[str, Any] = current.data(Qt.UserRole)
            return data.get("item")
        return None

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        # ── ACS file row ──────────────────────────────────────────────
        acs_row = QHBoxLayout()
        acs_row.addWidget(QLabel("Cloud Store (.acs):"))

        self._acs_edit = QLineEdit()
        self._acs_edit.setPlaceholderText(
            "Select an ArcGIS Cloud Store connection file…"
        )
        acs_row.addWidget(self._acs_edit, stretch=1)

        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_acs)
        acs_row.addWidget(browse_btn)

        load_btn = QPushButton("Load Catalog")
        load_btn.setDefault(False)
        load_btn.clicked.connect(self._load_catalog)
        acs_row.addWidget(load_btn)

        root.addLayout(acs_row)

        # ── Collections | Items splitter ──────────────────────────────
        splitter = QSplitter(Qt.Horizontal)

        col_group = QGroupBox("Collections")
        col_layout = QVBoxLayout(col_group)
        self._col_list = QListWidget()
        self._col_list.currentItemChanged.connect(self._on_collection_selected)
        col_layout.addWidget(self._col_list)
        splitter.addWidget(col_group)

        item_group = QGroupBox("Items")
        item_layout = QVBoxLayout(item_group)
        self._item_list = QListWidget()
        self._item_list.currentItemChanged.connect(self._on_item_selected)
        item_layout.addWidget(self._item_list)
        splitter.addWidget(item_group)

        splitter.setSizes([240, 540])
        root.addWidget(splitter, stretch=1)

        # ── Item detail ───────────────────────────────────────────────
        self._detail_label = QLabel("Select a collection, then choose an item.")
        self._detail_label.setWordWrap(True)
        root.addWidget(self._detail_label)

        # ── Status ────────────────────────────────────────────────────
        self._status_label = QLabel("")
        root.addWidget(self._status_label)

        # ── Dialog buttons ────────────────────────────────────────────
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Close)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        # Disable OK until the user has picked an item
        self._ok_btn = btn_box.button(QDialogButtonBox.Ok)
        self._ok_btn.setEnabled(False)
        root.addWidget(btn_box)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _browse_acs(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Cloud Store Connection File",
            "",
            "ArcGIS Cloud Store (*.acs);;All Files (*)",
        )
        if path:
            self._acs_edit.setText(path)

    def _load_catalog(self) -> None:
        acs_path = self._acs_edit.text().strip()
        if not acs_path:
            QMessageBox.warning(self, "No File", "Please select an .acs file first.")
            return

        self._set_status("Reading connection file…")
        try:
            url = read_catalog_url(acs_path)
        except Exception as exc:
            QMessageBox.critical(self, "ACS Error", str(exc))
            self._set_status("")
            return

        self._set_status(f"Connecting to {url}…")
        try:
            self._catalog = open_catalog(url)
            self._collections = get_collections(self._catalog)
        except Exception as exc:
            QMessageBox.critical(
                self, "STAC Error", f"Failed to open catalog:\n{exc}"
            )
            self._set_status("")
            return

        self._col_list.clear()
        self._item_list.clear()
        self._ok_btn.setEnabled(False)

        for col in self._collections:
            lw = QListWidgetItem(col["title"])
            lw.setData(Qt.UserRole, col["id"])
            lw.setToolTip(col["description"])
            self._col_list.addItem(lw)

        catalog_title = getattr(self._catalog, "title", None) or url
        self._set_status(
            f"Loaded {len(self._collections)} collection(s) from "{catalog_title}""
        )

    def _on_collection_selected(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        if current is None or self._catalog is None:
            return

        collection_id: str = current.data(Qt.UserRole)
        self._set_status(f"Loading items for '{collection_id}'…")
        self._item_list.clear()
        self._ok_btn.setEnabled(False)

        try:
            items = get_collection_items(self._catalog, collection_id)
        except Exception as exc:
            QMessageBox.warning(self, "Items Error", str(exc))
            self._set_status("")
            return

        for it in items:
            lw = QListWidgetItem(it["id"])
            lw.setData(Qt.UserRole, it)
            lw.setToolTip(f"Date: {it['datetime']}\nAssets: {', '.join(it['assets'])}")
            self._item_list.addItem(lw)

        self._set_status(f"{len(items)} item(s) in '{collection_id}'")

    def _on_item_selected(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            self._detail_label.setText("")
            self._ok_btn.setEnabled(False)
            return

        data: dict[str, Any] = current.data(Qt.UserRole)
        self._detail_label.setText(
            f"<b>ID:</b> {data['id']}&nbsp;&nbsp;"
            f"<b>Date:</b> {data['datetime']}&nbsp;&nbsp;"
            f"<b>BBox:</b> {data['bbox']}&nbsp;&nbsp;"
            f"<b>Assets:</b> {', '.join(data['assets'])}"
        )
        self._ok_btn.setEnabled(True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_status(self, message: str) -> None:
        self._status_label.setText(message)
        # Force immediate repaint so the user sees the message
        self._status_label.repaint()

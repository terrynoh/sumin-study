from __future__ import annotations

import threading
from pathlib import Path

from backend.item_bank import ItemBank


class ItemBankHolder:
    def __init__(self, initial: ItemBank) -> None:
        self._lock = threading.Lock()
        self._bank = initial

    def current(self) -> ItemBank:
        return self._bank

    def reload(self, root: Path) -> ItemBank:
        with self._lock:
            self._bank = ItemBank.from_directory_tree(root)
            return self._bank

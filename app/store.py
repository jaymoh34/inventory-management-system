"""In-memory storage that simulates a database using a list ("array")."""
from copy import deepcopy

from app.data import SEED_ITEMS


class InventoryStore:
    """A list of inventory items with simple CRUD helpers.

    Each Flask app instance owns its own store, which keeps tests isolated.
    """

    def __init__(self, items=None):
        source = SEED_ITEMS if items is None else items
        self._items = deepcopy(source)
        self._next_id = max((i["id"] for i in self._items), default=0) + 1

    def all(self):
        return deepcopy(self._items)

    def get(self, item_id):
        for item in self._items:
            if item["id"] == item_id:
                return deepcopy(item)
        return None

    def find_by_barcode(self, barcode):
        if not barcode:
            return None
        for item in self._items:
            if item.get("barcode") == barcode:
                return deepcopy(item)
        return None

    def search(self, text):
        """Case-insensitive match on name, brand or categories."""
        needle = text.strip().lower()
        results = []
        for item in self._items:
            p = item["product"]
            haystack = " ".join(
                [p.get("product_name", ""), p.get("brands", ""), p.get("categories", "")]
            ).lower()
            if needle in haystack:
                results.append(deepcopy(item))
        return results

    def add(self, data):
        item = {"id": self._next_id, **deepcopy(data)}
        self._items.append(item)
        self._next_id += 1
        return deepcopy(item)

    def update(self, item_id, changes):
        """Apply flat changes (price, stock, barcode, product fields)."""
        for item in self._items:
            if item["id"] == item_id:
                for key, value in changes.items():
                    if key in ("price", "stock", "barcode"):
                        item[key] = value
                    else:
                        item["product"][key] = value
                return deepcopy(item)
        return None

    def delete(self, item_id):
        for index, item in enumerate(self._items):
            if item["id"] == item_id:
                return self._items.pop(index)
        return None

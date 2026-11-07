from app.store import InventoryStore


def test_seed_data_loaded_with_ids():
    store = InventoryStore()
    items = store.all()
    assert len(items) == 8
    assert all("id" in i and i["status"] == 1 and "product_name" in i["product"] for i in items)


def test_add_assigns_incrementing_id():
    store = InventoryStore()
    first = store.add({"barcode": "", "product": {"product_name": "A"}, "price": 1, "stock": 1})
    second = store.add({"barcode": "", "product": {"product_name": "B"}, "price": 1, "stock": 1})
    assert first["id"] == 9 and second["id"] == 10


def test_ids_are_not_reused_after_delete():
    store = InventoryStore()
    store.delete(8)
    assert store.add({"barcode": "", "product": {"product_name": "X"}, "price": 0, "stock": 0})["id"] == 9


def test_update_changes_top_level_and_product_fields():
    store = InventoryStore()
    item = store.update(1, {"price": 9.99, "product_name": "New Name"})
    assert item["price"] == 9.99
    assert item["product"]["product_name"] == "New Name"


def test_update_and_delete_missing_return_none():
    store = InventoryStore()
    assert store.update(999, {"price": 1}) is None
    assert store.delete(999) is None


def test_search_is_case_insensitive():
    store = InventoryStore()
    assert [i["id"] for i in store.search("NUTELLA")] == [2]
    assert [i["id"] for i in store.search("silk")] == [1]


def test_returned_items_are_copies():
    store = InventoryStore()
    item = store.get(1)
    item["price"] = 0
    assert store.get(1)["price"] == 3.99


def test_find_by_barcode():
    store = InventoryStore()
    assert store.find_by_barcode("3017620422003")["id"] == 2
    assert store.find_by_barcode("") is None

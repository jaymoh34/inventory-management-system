"""Flask routes: inventory CRUD plus helper routes for OpenFoodFacts."""
from flask import Blueprint, current_app, jsonify, request

from app import openfoodfacts as off
from app.errors import ConflictError, NotFoundError, ValidationError
from app.validators import (
    validate_new_item, validate_price, validate_stock, validate_update,
)

bp = Blueprint("inventory", __name__)


def _store():
    return current_app.config["STORE"]


def _json_body():
    """Return the request JSON as a dict, or raise a 400 error."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a valid JSON object")
    return payload


def _get_or_404(item_id):
    item = _store().get(item_id)
    if item is None:
        raise NotFoundError(f"Item {item_id} not found")
    return item


def _ensure_barcode_free(barcode, ignore_id=None):
    existing = _store().find_by_barcode(barcode)
    if existing and existing["id"] != ignore_id:
        raise ConflictError(
            f"Barcode {barcode} already exists (item {existing['id']}). "
            "Use PATCH to update its price or stock."
        )


# ---------------------------------------------------------------- helpers
@bp.get("/health")
def health():
    return jsonify({"status": "ok"})


# ------------------------------------------------------------------ CRUD
@bp.get("/inventory")
def list_items():
    """Fetch all items. Optional ?search=<text> filters by name/brand/category."""
    search = request.args.get("search")
    items = _store().search(search) if search else _store().all()
    return jsonify({"count": len(items), "items": items})


@bp.get("/inventory/low-stock")
def low_stock():
    """Helper: items at or below ?threshold=<n> (default 10)."""
    raw = request.args.get("threshold", "10")
    try:
        threshold = int(raw)
    except ValueError:
        raise ValidationError("threshold must be a whole number")
    if threshold < 0:
        raise ValidationError("threshold must be zero or greater")
    items = [i for i in _store().all() if i["stock"] <= threshold]
    return jsonify({"threshold": threshold, "count": len(items), "items": items})


@bp.get("/inventory/<int:item_id>")
def get_item(item_id):
    return jsonify(_get_or_404(item_id))


@bp.post("/inventory")
def create_item():
    data = validate_new_item(_json_body())
    if data["barcode"]:
        _ensure_barcode_free(data["barcode"])
    return jsonify(_store().add(data)), 201


@bp.patch("/inventory/<int:item_id>")
def update_item(item_id):
    _get_or_404(item_id)
    changes = validate_update(_json_body())
    if "barcode" in changes:
        _ensure_barcode_free(changes["barcode"], ignore_id=item_id)
    return jsonify(_store().update(item_id, changes))


@bp.delete("/inventory/<int:item_id>")
def delete_item(item_id):
    _get_or_404(item_id)
    removed = _store().delete(item_id)
    return jsonify({"message": f"Item {item_id} deleted", "item": removed})


# -------------------------------------------------- OpenFoodFacts helpers
@bp.get("/external/barcode/<barcode>")
def external_by_barcode(barcode):
    """Look up a product on OpenFoodFacts by barcode (nothing is stored)."""
    return jsonify(off.get_product_by_barcode(barcode))


@bp.get("/external/search")
def external_search():
    """Search OpenFoodFacts by ?name=<text>&limit=<1-20> (nothing is stored)."""
    name = request.args.get("name", "")
    if not name.strip():
        raise ValidationError("Query parameter 'name' is required")
    try:
        limit = int(request.args.get("limit", "5"))
    except ValueError:
        raise ValidationError("limit must be a whole number")
    if not 1 <= limit <= 20:
        raise ValidationError("limit must be between 1 and 20")
    results = off.search_products_by_name(name, limit=limit)
    return jsonify({"count": len(results), "results": results})


@bp.post("/inventory/import")
def import_from_external():
    """Fetch a product from OpenFoodFacts (by barcode or name) and add it to inventory."""
    payload = _json_body()
    barcode, name = payload.get("barcode"), payload.get("name")
    if bool(barcode) == bool(name):
        raise ValidationError("Provide exactly one of 'barcode' or 'name'")
    unknown = set(payload) - {"barcode", "name", "price", "stock"}
    if unknown:
        raise ValidationError(f"Unknown field(s): {', '.join(sorted(unknown))}")

    price = validate_price(payload.get("price", 0))
    stock = validate_stock(payload.get("stock", 0))

    if barcode:
        result = off.get_product_by_barcode(barcode)
    else:
        result = off.search_products_by_name(name, limit=1)[0]

    if result["barcode"]:
        _ensure_barcode_free(result["barcode"])
    item = _store().add({
        "barcode": result["barcode"],
        "status": 1,
        "source": "openfoodfacts",
        "product": result["product"],
        "price": price,
        "stock": stock,
    })
    return jsonify(item), 201


@bp.patch("/inventory/<int:item_id>/enrich")
def enrich_item(item_id):
    """Fill empty product fields of an item using OpenFoodFacts (matched by barcode)."""
    item = _get_or_404(item_id)
    if not item.get("barcode"):
        raise ValidationError("Item has no barcode, so it cannot be matched on OpenFoodFacts")

    external = off.get_product_by_barcode(item["barcode"])["product"]
    changes = {
        field: value for field, value in external.items()
        if value and not item["product"].get(field)
    }
    # image_url is not user-editable via PATCH, so apply it directly through the store
    updated = _store().update(item_id, changes) if changes else item
    return jsonify(updated)

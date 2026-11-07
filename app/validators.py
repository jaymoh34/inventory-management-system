"""Input validation for request payloads."""
import math

from app.errors import ValidationError

PRODUCT_TEXT_FIELDS = (
    "product_name", "brands", "ingredients_text",
    "categories", "quantity", "nutriscore_grade",
)
UPDATABLE_FIELDS = set(PRODUCT_TEXT_FIELDS) | {"price", "stock", "barcode"}


def validate_price(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError("price must be a number")
    if not math.isfinite(value) or value < 0:
        raise ValidationError("price must be zero or greater")
    return round(float(value), 2)


def validate_stock(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError("stock must be a whole number")
    if value < 0:
        raise ValidationError("stock must be zero or greater")
    return value


def validate_barcode(value):
    if not isinstance(value, str):
        raise ValidationError("barcode must be a string of digits")
    value = value.strip()
    if not value.isdigit() or not 8 <= len(value) <= 14:
        raise ValidationError("barcode must be 8-14 digits")
    return value


def _validate_text(field, value, required=False):
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string")
    value = value.strip()
    if required and not value:
        raise ValidationError(f"{field} is required and cannot be empty")
    return value


def validate_new_item(payload):
    """Validate a POST /inventory body and return item data (without id)."""
    if "product_name" not in payload:
        raise ValidationError("product_name is required")
    unknown = set(payload) - UPDATABLE_FIELDS
    if unknown:
        raise ValidationError(f"Unknown field(s): {', '.join(sorted(unknown))}")

    product = {field: "" for field in PRODUCT_TEXT_FIELDS}
    product["image_url"] = ""
    for field in PRODUCT_TEXT_FIELDS:
        if field in payload:
            product[field] = _validate_text(field, payload[field], required=(field == "product_name"))

    barcode = validate_barcode(payload["barcode"]) if payload.get("barcode") not in (None, "") else ""
    return {
        "barcode": barcode,
        "status": 1,
        "source": "manual",
        "product": product,
        "price": validate_price(payload.get("price", 0)),
        "stock": validate_stock(payload.get("stock", 0)),
    }


def validate_update(payload):
    """Validate a PATCH body and return a flat dict of changes."""
    if not payload:
        raise ValidationError("Provide at least one field to update")
    unknown = set(payload) - UPDATABLE_FIELDS
    if unknown:
        raise ValidationError(f"Unknown field(s): {', '.join(sorted(unknown))}")

    changes = {}
    for key, value in payload.items():
        if key == "price":
            changes[key] = validate_price(value)
        elif key == "stock":
            changes[key] = validate_stock(value)
        elif key == "barcode":
            changes[key] = validate_barcode(value)
        else:
            changes[key] = _validate_text(key, value, required=(key == "product_name"))
    return changes

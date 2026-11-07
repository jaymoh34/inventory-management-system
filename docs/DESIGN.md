# Task 2 – Design

## Mock database (array)

`app/data.py` holds `SEED_ITEMS`, a list of dictionaries that resemble an OpenFoodFacts
response (`status` + `product`) plus retail fields. `app/store.py` (`InventoryStore`) wraps the
list and is the only code that mutates it.

```json
{
  "id": 1,
  "barcode": "025293002029",
  "status": 1,
  "source": "mock",
  "product": {
    "product_name": "Organic Almond Milk",
    "brands": "Silk",
    "ingredients_text": "Filtered water, almonds, cane sugar, ...",
    "categories": "Beverages, Plant-based milks",
    "quantity": "1.89 L",
    "nutriscore_grade": "b",
    "image_url": ""
  },
  "price": 3.99,
  "stock": 25
}
```

| Field | Why it is stored |
|---|---|
| `id` | Unique integer used by every route (auto-incremented, never reused) |
| `barcode` | Links the item to OpenFoodFacts; unique when present |
| `status`, `product.*` | Same shape as OpenFoodFacts so imported data drops straight in |
| `price`, `stock` | Retail data OpenFoodFacts does not provide |
| `source` | `mock`, `manual` or `openfoodfacts` – where the item came from |

## Routes: inputs, outputs, data changes, CLI trigger

| Route | Input | Success output | Change to data | Triggered by CLI |
|---|---|---|---|---|
| `GET /inventory` | optional `?search=` | `200 {count, items[]}` | none (read) | `python cli.py list [--search X]` |
| `GET /inventory/<id>` | id in path | `200 item` | none | `python cli.py view <id>` |
| `POST /inventory` | JSON: `product_name` (required), `brands`, `ingredients_text`, `categories`, `quantity`, `nutriscore_grade`, `barcode`, `price`, `stock` | `201 item` | **appends** a new item with next id | `python cli.py add --name ...` |
| `PATCH /inventory/<id>` | id + JSON with any of the fields above | `200 item` | **modifies** only the given fields | `python cli.py update <id> --price/--stock ...` |
| `DELETE /inventory/<id>` | id in path | `200 {message, item}` | **removes** the item | `python cli.py delete <id> [--yes]` |
| `GET /inventory/low-stock` | optional `?threshold=` (default 10) | `200 {threshold, count, items[]}` | none | `python cli.py low-stock` |
| `GET /external/barcode/<barcode>` | barcode in path | `200 {status, barcode, product}` | none (OpenFoodFacts lookup only) | `python cli.py find --barcode X` |
| `GET /external/search` | `?name=` (required), `?limit=` 1-20 | `200 {count, results[]}` | none | `python cli.py find --name X` |
| `POST /inventory/import` | JSON: exactly one of `barcode` / `name`, optional `price`, `stock` | `201 item` | **appends** item built from OpenFoodFacts data | `python cli.py import --barcode X --price 2 --stock 10` |
| `PATCH /inventory/<id>/enrich` | id in path | `200 item` | **fills empty** product fields from OpenFoodFacts | `python cli.py enrich <id>` |
| `GET /health` | – | `200 {status: ok}` | none | – |

## Error responses

All errors are JSON: `{"error": "message"}`.

| Status | When |
|---|---|
| 400 | Invalid input: missing name, negative/non-numeric price, non-integer stock, bad barcode, invalid JSON, unknown field, empty PATCH |
| 404 | Item id not found, unknown route, or product not found on OpenFoodFacts |
| 405 | Wrong HTTP method |
| 409 | Barcode already exists in inventory |
| 502 | OpenFoodFacts unreachable / returned an error / invalid response |
| 504 | OpenFoodFacts timed out |

The CLI prints these as `Error: <message>` and exits with code 1. It also reports a friendly
message if the Flask server itself is not running.

## CLI mock-up

```
$ python cli.py list
ID   Name                         Brand             Price  Stock
----------------------------------------------------------------
1    Organic Almond Milk          Silk               3.99     25
2    Nutella Hazelnut Spread      Ferrero            5.49     40
...
8 item(s)

$ python cli.py import --barcode 3017620422003 --price 5.99 --stock 12
Imported from OpenFoodFacts as item 9:
ID:           9
Name:         Nutella
...
```

## Code layout

```
app/
  __init__.py       create_app() factory
  routes.py         Flask blueprint (all endpoints)
  store.py          array-backed storage
  data.py           mock OpenFoodFacts-style seed data
  validators.py     input validation
  openfoodfacts.py  external API client (barcode + name search)
  errors.py         exceptions + JSON error handlers
cli.py              argparse CLI that calls the API with requests
run.py              starts the dev server in debug mode
tests/              pytest + unittest.mock
```

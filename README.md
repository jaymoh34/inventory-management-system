# Inventory Management System (Flask REST API + CLI)

An administrator portal backend for a small retail company. Employees can add, view,
edit and delete inventory items through a **Flask REST API** and a **command-line
interface**. Product details can be fetched from the
[OpenFoodFacts API](https://world.openfoodfacts.org) by barcode or name and added to the
inventory.

Data is stored in an in-memory Python list (a simulated database), so it resets whenever
the server restarts.

## Features

- RESTful CRUD: `GET`, `POST`, `PATCH`, `DELETE` on `/inventory`
- Helper routes: low-stock report, OpenFoodFacts lookup/search, import, enrich
- CLI to list, view, add, update price/stock, delete, find on the API, and import
- Validation and JSON error handling (bad input, duplicates, API failures/timeouts)
- 100+ automated tests using `pytest` and `unittest.mock`

## Installation

```bash
git clone <your-repo-url>
cd inventory-management-system
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running

Terminal 1 – start the API (debug mode on, http://127.0.0.1:5000):

```bash
python run.py
```

Terminal 2 – use the CLI:

```bash
python cli.py list
```

To point the CLI at a different server: `export INVENTORY_API_URL=http://host:port`.

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/inventory` | All items (`?search=text` to filter) |
| GET | `/inventory/<id>` | One item |
| POST | `/inventory` | Create an item |
| PATCH | `/inventory/<id>` | Update price, stock or product details |
| DELETE | `/inventory/<id>` | Delete an item |
| GET | `/inventory/low-stock?threshold=10` | Items at or below a stock level |
| GET | `/external/barcode/<barcode>` | Look up a product on OpenFoodFacts |
| GET | `/external/search?name=<text>&limit=5` | Search OpenFoodFacts by name |
| POST | `/inventory/import` | Fetch from OpenFoodFacts and add to inventory |
| PATCH | `/inventory/<id>/enrich` | Fill an item's missing details from OpenFoodFacts |
| GET | `/health` | Health check |

Full inputs/outputs for every route: [docs/DESIGN.md](docs/DESIGN.md).

### Example requests

```bash
# Create
curl -X POST http://127.0.0.1:5000/inventory -H "Content-Type: application/json" \
  -d '{"product_name": "Green Tea", "brands": "Lipton", "price": 4.5, "stock": 20}'

# Update price and stock
curl -X PATCH http://127.0.0.1:5000/inventory/1 -H "Content-Type: application/json" \
  -d '{"price": 4.25, "stock": 10}'

# Import from OpenFoodFacts by barcode
curl -X POST http://127.0.0.1:5000/inventory/import -H "Content-Type: application/json" \
  -d '{"barcode": "3017620422003", "price": 5.99, "stock": 12}'

# Delete
curl -X DELETE http://127.0.0.1:5000/inventory/1
```

### Item format

```json
{
  "id": 1, "barcode": "025293002029", "status": 1, "source": "mock",
  "product": {"product_name": "Organic Almond Milk", "brands": "Silk",
              "ingredients_text": "Filtered water, almonds, ...",
              "categories": "...", "quantity": "1.89 L", "nutriscore_grade": "b"},
  "price": 3.99, "stock": 25
}
```

### Errors

Errors are JSON `{"error": "..."}` with status 400 (invalid input), 404 (not found),
405, 409 (duplicate barcode), 502 / 504 (OpenFoodFacts failure / timeout).

## CLI usage

```bash
python cli.py list                                  # all items
python cli.py list --search milk                    # filter
python cli.py view 1                                # item details
python cli.py add --name "Green Tea" --brand Lipton --price 4.5 --stock 20
python cli.py update 1 --price 4.25                 # update price
python cli.py update 1 --stock 50                   # update stock
python cli.py delete 1                              # asks for confirmation
python cli.py delete 1 --yes                        # no prompt
python cli.py find --barcode 3017620422003          # look up on OpenFoodFacts
python cli.py find --name "almond milk" --limit 3   # search OpenFoodFacts
python cli.py import --barcode 3017620422003 --price 5.99 --stock 12
python cli.py import --name "almond milk" --price 3.5 --stock 10
python cli.py enrich 1                              # fill missing details from the API
python cli.py low-stock --threshold 10
python cli.py --help
```

## Testing

```bash
pytest            # run everything
pytest -v         # verbose
pytest tests/test_api.py
```

| File | Covers |
|---|---|
| `tests/test_store.py` | array storage (add, update, delete, search) |
| `tests/test_validators.py` | input validation rules |
| `tests/test_api.py` | every endpoint: success and error paths (external API mocked) |
| `tests/test_openfoodfacts.py` | external client: success, not found, timeout, bad JSON, HTTP errors |
| `tests/test_cli.py` | every CLI command, confirmation prompt, error output |

All OpenFoodFacts and HTTP calls are mocked with `unittest.mock`, so tests run offline.

### Debugging

- `python run.py` starts Flask in debug mode (auto-reload + debugger). Set `FLASK_DEBUG=0` to disable.
- Import `docs/postman_collection.json` into Postman to try every endpoint
  (set the `base_url` variable to `http://127.0.0.1:5000`).

## Git workflow

Each feature was developed on its own branch and merged into `main` with a merge commit
(the equivalent of a pull request), then the branch was deleted:

```
feature/data-store -> feature/openfoodfacts-client -> feature/flask-api
  -> feature/cli -> docs/readme-and-design
```

When pushing to GitHub, open each branch as a pull request, merge it, and delete the branch.

## Project structure

See [docs/DESIGN.md](docs/DESIGN.md#code-layout).


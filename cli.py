"""Command-line interface for the Inventory Management API.

Start the server first (python run.py), then e.g.:
    python cli.py list
    python cli.py add --name "Green Tea" --price 4.5 --stock 20
"""
import argparse
import os
import sys

import requests

DEFAULT_API_URL = "http://127.0.0.1:5000"
TIMEOUT = 15


class CLIError(Exception):
    """A problem to report to the user (bad input, server error, API down)."""


def api_url():
    return os.environ.get("INVENTORY_API_URL", DEFAULT_API_URL).rstrip("/")


def call_api(method, path, **kwargs):
    """Send a request to the Flask API and return the parsed JSON body."""
    url = api_url() + path
    try:
        response = requests.request(method, url, timeout=TIMEOUT, **kwargs)
    except requests.exceptions.ConnectionError:
        raise CLIError(f"Cannot connect to the API at {api_url()}. Is the server running? (python run.py)")
    except requests.exceptions.Timeout:
        raise CLIError("The API took too long to respond. Please try again.")
    except requests.exceptions.RequestException as exc:
        raise CLIError(f"Request failed: {exc}")

    try:
        data = response.json()
    except ValueError:
        raise CLIError(f"Unexpected response from the server (HTTP {response.status_code}).")
    if response.status_code >= 400:
        message = data.get("error") if isinstance(data, dict) else None
        raise CLIError(message or f"Request failed with HTTP {response.status_code}")
    return data


# ------------------------------------------------------------- formatting
def format_item(item):
    p = item["product"]
    lines = [
        f"ID:           {item['id']}",
        f"Name:         {p.get('product_name', '')}",
        f"Brand:        {p.get('brands', '')}",
        f"Barcode:      {item.get('barcode') or '-'}",
        f"Price:        {item['price']:.2f}",
        f"Stock:        {item['stock']}",
        f"Categories:   {p.get('categories') or '-'}",
        f"Quantity:     {p.get('quantity') or '-'}",
        f"Nutri-Score:  {(p.get('nutriscore_grade') or '-').upper()}",
        f"Ingredients:  {p.get('ingredients_text') or '-'}",
        f"Source:       {item.get('source', '-')}",
    ]
    return "\n".join(lines)


def format_table(items):
    if not items:
        return "No items found."
    header = f"{'ID':<4} {'Name':<28} {'Brand':<14} {'Price':>8} {'Stock':>6}"
    rows = [header, "-" * len(header)]
    for i in items:
        p = i["product"]
        rows.append(
            f"{i['id']:<4} {p.get('product_name', '')[:27]:<28} "
            f"{p.get('brands', '')[:13]:<14} {i['price']:>8.2f} {i['stock']:>6}"
        )
    return "\n".join(rows)


def format_external(result):
    p = result["product"]
    return (
        f"Name:         {p.get('product_name') or '-'}\n"
        f"Brand:        {p.get('brands') or '-'}\n"
        f"Barcode:      {result.get('barcode') or '-'}\n"
        f"Categories:   {p.get('categories') or '-'}\n"
        f"Nutri-Score:  {(p.get('nutriscore_grade') or '-').upper()}\n"
        f"Ingredients:  {p.get('ingredients_text') or '-'}"
    )


# --------------------------------------------------------------- commands
def cmd_list(args):
    path = "/inventory"
    params = {"search": args.search} if args.search else None
    data = call_api("GET", path, params=params)
    print(format_table(data["items"]))
    print(f"\n{data['count']} item(s)")


def cmd_view(args):
    print(format_item(call_api("GET", f"/inventory/{args.id}")))


def cmd_add(args):
    payload = {
        "product_name": args.name, "brands": args.brand,
        "ingredients_text": args.ingredients, "categories": args.categories,
        "barcode": args.barcode, "price": args.price, "stock": args.stock,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    item = call_api("POST", "/inventory", json=payload)
    print(f"Added item {item['id']}:\n{format_item(item)}")


def cmd_update(args):
    payload = {
        "price": args.price, "stock": args.stock, "product_name": args.name,
        "brands": args.brand, "barcode": args.barcode,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    if not payload:
        raise CLIError("Nothing to update. Use --price, --stock, --name, --brand or --barcode.")
    item = call_api("PATCH", f"/inventory/{args.id}", json=payload)
    print(f"Updated item {item['id']}:\n{format_item(item)}")


def cmd_delete(args):
    if not args.yes:
        answer = input(f"Delete item {args.id}? [y/N]: ").strip().lower()
        if answer not in ("y", "yes"):
            print("Cancelled.")
            return
    data = call_api("DELETE", f"/inventory/{args.id}")
    print(data["message"])


def cmd_find(args):
    if args.barcode:
        print(format_external(call_api("GET", f"/external/barcode/{args.barcode}")))
    else:
        data = call_api("GET", "/external/search", params={"name": args.name, "limit": args.limit})
        for n, result in enumerate(data["results"], start=1):
            print(f"--- Result {n} ---\n{format_external(result)}\n")


def cmd_import(args):
    payload = {"price": args.price, "stock": args.stock}
    if args.barcode:
        payload["barcode"] = args.barcode
    else:
        payload["name"] = args.name
    item = call_api("POST", "/inventory/import", json=payload)
    print(f"Imported from OpenFoodFacts as item {item['id']}:\n{format_item(item)}")


def cmd_enrich(args):
    item = call_api("PATCH", f"/inventory/{args.id}/enrich")
    print(f"Enriched item {item['id']}:\n{format_item(item)}")


def cmd_low_stock(args):
    data = call_api("GET", "/inventory/low-stock", params={"threshold": args.threshold})
    print(format_table(data["items"]))
    print(f"\n{data['count']} item(s) at or below {data['threshold']} in stock")


# ---------------------------------------------------------------- parsing
def build_parser():
    parser = argparse.ArgumentParser(prog="cli.py", description="Inventory Management CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list", help="List all inventory items")
    p.add_argument("--search", help="Filter by name, brand or category")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("view", help="View one item in detail")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_view)

    p = sub.add_parser("add", help="Add a new item manually")
    p.add_argument("--name", required=True)
    p.add_argument("--brand")
    p.add_argument("--ingredients")
    p.add_argument("--categories")
    p.add_argument("--barcode")
    p.add_argument("--price", type=float)
    p.add_argument("--stock", type=int)
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("update", help="Update an item's price, stock or details")
    p.add_argument("id", type=int)
    p.add_argument("--price", type=float)
    p.add_argument("--stock", type=int)
    p.add_argument("--name")
    p.add_argument("--brand")
    p.add_argument("--barcode")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("delete", help="Delete an item")
    p.add_argument("id", type=int)
    p.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("find", help="Find a product on OpenFoodFacts")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--barcode")
    group.add_argument("--name")
    p.add_argument("--limit", type=int, default=5, help="Max results for --name (default 5)")
    p.set_defaults(func=cmd_find)

    p = sub.add_parser("import", help="Find a product on OpenFoodFacts and add it to inventory")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--barcode")
    group.add_argument("--name")
    p.add_argument("--price", type=float, default=0)
    p.add_argument("--stock", type=int, default=0)
    p.set_defaults(func=cmd_import)

    p = sub.add_parser("enrich", help="Fill missing details of an item from OpenFoodFacts")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_enrich)

    p = sub.add_parser("low-stock", help="List items running low")
    p.add_argument("--threshold", type=int, default=10)
    p.set_defaults(func=cmd_low_stock)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except CLIError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

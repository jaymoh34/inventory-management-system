"""Mock database.

Each item mirrors the OpenFoodFacts response shape ("status" + "product")
and adds the fields a retailer needs: id, barcode, price, stock, source.
The data is only a mock - barcodes are illustrative.
"""

SEED_ITEMS = [
    {
        "id": 1, "barcode": "025293002029", "status": 1, "source": "mock",
        "product": {
            "product_name": "Organic Almond Milk", "brands": "Silk",
            "ingredients_text": "Filtered water, almonds, cane sugar, sea salt, sunflower lecithin",
            "categories": "Beverages, Plant-based milks", "quantity": "1.89 L",
            "nutriscore_grade": "b", "image_url": "",
        },
        "price": 3.99, "stock": 25,
    },
    {
        "id": 2, "barcode": "3017620422003", "status": 1, "source": "mock",
        "product": {
            "product_name": "Nutella Hazelnut Spread", "brands": "Ferrero",
            "ingredients_text": "Sugar, palm oil, hazelnuts, skimmed milk powder, cocoa, lecithin, vanillin",
            "categories": "Spreads, Sweet spreads", "quantity": "400 g",
            "nutriscore_grade": "e", "image_url": "",
        },
        "price": 5.49, "stock": 40,
    },
    {
        "id": 3, "barcode": "5449000000996", "status": 1, "source": "mock",
        "product": {
            "product_name": "Coca-Cola Classic", "brands": "Coca-Cola",
            "ingredients_text": "Carbonated water, sugar, colour caramel E150d, phosphoric acid, natural flavourings, caffeine",
            "categories": "Beverages, Sodas", "quantity": "500 ml",
            "nutriscore_grade": "e", "image_url": "",
        },
        "price": 1.50, "stock": 120,
    },
    {
        "id": 4, "barcode": "7622210449283", "status": 1, "source": "mock",
        "product": {
            "product_name": "Oreo Original", "brands": "Oreo",
            "ingredients_text": "Wheat flour, sugar, palm oil, cocoa powder, glucose-fructose syrup, raising agents",
            "categories": "Snacks, Biscuits", "quantity": "154 g",
            "nutriscore_grade": "d", "image_url": "",
        },
        "price": 2.99, "stock": 60,
    },
    {
        "id": 5, "barcode": "5000157024671", "status": 1, "source": "mock",
        "product": {
            "product_name": "Tomato Ketchup", "brands": "Heinz",
            "ingredients_text": "Tomatoes, spirit vinegar, sugar, salt, spice and herb extracts",
            "categories": "Condiments, Sauces", "quantity": "700 g",
            "nutriscore_grade": "d", "image_url": "",
        },
        "price": 3.25, "stock": 8,
    },
    {
        "id": 6, "barcode": "5010477348630", "status": 1, "source": "mock",
        "product": {
            "product_name": "Corn Flakes", "brands": "Kellogg's",
            "ingredients_text": "Maize, sugar, malt flavouring, salt, vitamins and iron",
            "categories": "Breakfast cereals", "quantity": "500 g",
            "nutriscore_grade": "c", "image_url": "",
        },
        "price": 4.20, "stock": 35,
    },
    {
        "id": 7, "barcode": "8076800195057", "status": 1, "source": "mock",
        "product": {
            "product_name": "Spaghetti No. 5", "brands": "Barilla",
            "ingredients_text": "Durum wheat semolina, water",
            "categories": "Pasta, Cereals and potatoes", "quantity": "500 g",
            "nutriscore_grade": "a", "image_url": "",
        },
        "price": 1.89, "stock": 3,
    },
    {
        "id": 8, "barcode": "3068320115733", "status": 1, "source": "mock",
        "product": {
            "product_name": "Natural Mineral Water", "brands": "Evian",
            "ingredients_text": "Natural mineral water",
            "categories": "Beverages, Waters", "quantity": "1.5 L",
            "nutriscore_grade": "a", "image_url": "",
        },
        "price": 1.10, "stock": 200,
    },
]

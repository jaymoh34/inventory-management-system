"""Start the Flask development server: python run.py"""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Flask debug mode gives auto-reload and an interactive debugger.
    app.run(debug=os.environ.get("FLASK_DEBUG", "1") == "1", port=5000)

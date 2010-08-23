"""Run this file to test the blog locally on http://localhost:5000/"""
from simblin import create_app

if __name__ == "__main__":
    app = create_app()
    app.run()

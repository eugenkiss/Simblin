"""Run this file to test the blog locally on http://localhost:5000/"""
from simblin import create_app

try:
    import disqus_settings
except:
    disqus_settings = None

if __name__ == "__main__":
    app = create_app(disqus_settings) if disqus_settings else create_app()
    app.run()

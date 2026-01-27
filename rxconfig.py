import reflex as rx
import os

config = rx.Config(
    app_name="app",
    disable_plugins=["reflex.plugins.sitemap.SitemapPlugin"],
    api_url=os.getenv("REFLEX_API_URL", "http://localhost:8000"),
)

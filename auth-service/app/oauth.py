from authlib.integrations.starlette_client import OAuth
import os

oauth = OAuth()

oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET", "GOOGLE_CLIENT_SECRET"),
    server_metadata_url=os.getenv(
        "GOOGLE_METADATA_URL",
        "https://accounts.google.com/.well-known/openid-configuration",
    ),
    client_kwargs={"scope": "openid email profile"},
)
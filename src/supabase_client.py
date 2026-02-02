import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

secret: str = os.getenv("sb_secret")
url:str = os.getenv("sb_url")

supabase: Client = create_client(
    url,
    secret
)
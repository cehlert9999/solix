import asyncio
from aiohttp import ClientSession
from api.api import AnkerSolixApi
import os
from dotenv import load_dotenv
import json

load_dotenv()
USER = os.getenv("ANKERUSER")
PASSWORD = os.getenv("ANKERPASSWORD")
COUNTRY = os.getenv("ANKERCOUNTRY", "DE")

async def main():
    async with ClientSession() as session:
        api = AnkerSolixApi(USER, PASSWORD, COUNTRY, session, None)
        await api.update_sites()
        await api.update_site_details()
        await api.update_device_energy()
        await api.update_device_details()
        safe_data = {
            "sites": json.loads(json.dumps(api.sites, default=str)),
            "devices": json.loads(json.dumps(api.devices, default=str))
        }
        with open("debug_data.json", "w", encoding="utf-8") as f:
            json.dump(safe_data, f, indent=2)

asyncio.run(main())

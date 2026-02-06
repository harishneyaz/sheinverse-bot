VERSE_API = "https://www.sheinindia.in/api/product/list?cat_id=37961&page=1&limit=60"

async def get_verse_men(session):
    async with session.get(VERSE_API, timeout=10) as r:
        data = await r.json()

    men = []
    for p in data["data"]["products"]:
        if "men" in (p.get("gender","").lower()):
            men.append({
                "id": str(p["id"]),
                "name": p["name"],
                "price": p["price"],
                "image": p["image"],
                "url": f"https://www.sheinindia.in/p/{p['id']}"
            })
    return men

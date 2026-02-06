async def get_sizes(session, pid):
    url = f"https://www.sheinindia.in/api/product/info?id={pid}"
    async with session.get(url, timeout=8) as r:
        data = await r.json()

    sizes = {}
    for sku in data["data"]["sku_list"]:
        sizes[sku["size"]] = sku["stock"]
    return sizes

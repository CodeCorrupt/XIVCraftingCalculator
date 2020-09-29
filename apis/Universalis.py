from utils.Throttle import Throttler


class Universalis():
    def __init__(self, session, world="Diabolos"):
        self.session = session
        self.base_url = 'https://universalis.app'
        self.world = str(world)

        self.throttle = Throttler(20)

    async def get_items(self, item_ids):
        ids = ','.join([str(i) for i in item_ids])
        full_url = f'{self.base_url}/api/{self.world}/{ids}'
        async with self.throttle, self.session.get(full_url) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_avg_prices(self, item_ids, nq=False, hq=False):
        if len(item_ids) == 0:
            raise Exception("len(item_ids) must be > 0")

        # If both are tue or both are false (not nq XOR hq)
        if not nq ^ hq:
            name = 'averagePrice'
        elif nq:
            name = 'averagePriceNQ'
        elif hq:
            name = 'averagePriceHQ'
        else:
            raise Exception('How did you get here???')

        all_items = {}
        n = 100
        for g in [item_ids[i * n:(i + 1) * n] for i in range((len(item_ids) + n - 1) // n)]:
            stats = await self.get_items(g)
            if len(g) > 1:
                items = {}
                for item in stats.get('items', []):
                    if item.get(name):
                        items[item.get('itemID')] = item.get(name)
                all_items.update(items)
            else:
                all_items.update({stats.get('itemID'): stats.get(name)})
        return all_items

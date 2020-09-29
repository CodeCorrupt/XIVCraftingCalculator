import asyncio
import aiohttp
from pprint import pprint

from utils.Throttle import Throttler

from apis.Universalis import Universalis
from apis.XIVapi import XIVapi


class Scanner():
    def __init__(self, xivapi, universalis):
        self.xapi = xivapi
        self.uni = universalis

    def is_all_tradable(self, recipe):
        if recipe.get('tradable', False):
            tradable = True
            for i in recipe.get('ingredients', []):
                tradable = tradable and i.get('tradable', False)
            return tradable
        else:
            return False

    async def get_bulk_costs_and_profit(self, recipes):
        items = set()
        for r in recipes:
            items.add(r.get('id'))
            for i in r.get('ingredients', []):
                items.add(i.get('id'))
        prices = await self.uni.get_avg_prices(list(items))
        for r in recipes:
            result_cost = prices.get(r.get('id'), 0)
            result_amount = r.get('amount')
            r['cost'] = result_cost
            ingredient_total_cost = 0
            for i in r.get('ingredients', []):
                ingredient_cost = prices.get(i.get('id'), 9_999_999_999)
                ingredient_amount = i.get('amount')
                ingredient_total_cost += ingredient_cost * ingredient_amount
                i['cost'] = ingredient_cost
            r['profit'] = result_cost * result_amount - ingredient_total_cost

    async def main(self, craft_class, craft_lvl):
        recipe_list = await self.xapi.get_recipes(craft_class, craft_lvl)
        tradable_recipes = [x for x in recipe_list if self.is_all_tradable(x)]
        await self.get_bulk_costs_and_profit(tradable_recipes)

        most_profitable = {}
        for r in tradable_recipes:
            r_profit = r.get('profit', 0)
            max_profit = most_profitable.get('profit', 0)
            if r_profit > max_profit:
                most_profitable = r

        pprint(most_profitable)
        # costs = await self.uni.get_avg_prices([8129])
        # pprint(costs)


async def main():
    async with aiohttp.ClientSession() as session:
        xivapi = XIVapi(session)
        universalis = Universalis(session)
        scanner = Scanner(xivapi, universalis)
        await scanner.main("GSM", 40)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

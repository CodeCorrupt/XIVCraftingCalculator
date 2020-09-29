import json
from utils.Throttle import Throttler


class XIVapi():
    def __init__(self, session):
        self.session = session
        self.base_url = 'https://xivapi.com'
        self.throttle = Throttler(12)

    def _get_dot_path(self, path, data):
        d = data
        for p in path.split('.'):
            d = d.get(p, {})
        return d

    def _format_ingredients(self, data):
        ingredients = []
        for n in range(10):
            if self._get_dot_path(f'AmountIngredient{n}', data) > 0:
                ingredients.append({
                    'id': self._get_dot_path(f'ItemIngredient{n}.ID', data),
                    'name': self._get_dot_path(f'ItemIngredient{n}.Name_en', data),
                    'amount': self._get_dot_path(f'AmountIngredient{n}', data),
                    'tradable': self._get_dot_path(f'ItemIngredient{n}.IsUntradable', data) == 0,
                })
        return ingredients

    def _format_recipes(self, data):
        formatted = []
        for r in data:
            formatted.append({
                'id': self._get_dot_path('ItemResultTargetID', r),
                'name': self._get_dot_path('Name_en', r),
                'lvl': self._get_dot_path('RecipeLevelTable.ClassJobLevel', r),
                'amount': self._get_dot_path('AmountResult', r),
                'tradable': self._get_dot_path('ItemResult.IsUntradable', r) == 0,
                'ingredients': self._format_ingredients(r)
            })
        return formatted

    async def get_recipes(self, class_abv, class_lvl):
        indexes = ["recipe"]
        columns = [
            "Name_en",
            "RecipeLevelTable.ClassJobLevel",
            "ClassJob.Abbreviation",
            "ItemResultTargetID",
            "ItemResult.IsUntradable",
            "AmountResult"
        ]
        columns.extend([f'AmountIngredient{n}' for n in range(10)])
        columns.extend([f'ItemIngredient{n}.ID' for n in range(10)])
        columns.extend([f'ItemIngredient{n}.Name_en' for n in range(10)])
        columns.extend([f'ItemIngredient{n}.IsUntradable' for n in range(10)])
        query = {
            "indexes": ','.join(indexes),
            "columns": ','.join(columns),
            "body": {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "ClassJob.Abbreviation_en": class_abv
                                }
                            }
                        ],
                        "filter": [
                            {
                                "range": {
                                    "RecipeLevelTable.ClassJobLevel": {
                                        "lte": str(class_lvl)
                                    }
                                }
                            }
                        ]
                    }
                },
                "from": 0,
                "size": 100,
                "sort": [
                    {
                        "RecipeLevelTable.ClassJobLevel": "desc"
                    }
                ]
            }
        }

        full_url = f'{self.base_url}/search'
        page = 1
        cont = True
        results = []
        while cont:
            async with self.throttle, self.session.post(
                full_url,
                data=json.dumps(query),
                params={'page': page}
            ) as resp:
                resp.raise_for_status()
                result = await resp.json()
                results.extend(result.get('Results', []))
                if not result.get('Pagination', {}).get('PageNext', None):
                    cont = False
                else:
                    page = page + 1
        return self._format_recipes(results)

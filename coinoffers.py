from decimal import Decimal
import json
import re
import lxml.html
import requests


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


get_float_in_parens = re.compile(r'\((\d+)(?:,(\d+))?\)').search


def get_min_amount(offer_tr):
    return Decimal(offer_tr.xpath('@data-amount')[0])


def get_bitcoinde_buy_link(offer_tr):
    path = offer_tr.xpath('td/a/@href')[0]
    return 'https://www.bitcoin.de{}'.format(path)


def get_bitcoinde_seller(offer_tr):
    path = offer_tr.xpath('@data-trade-id')[0]
    return path.split('=')[-1]


def bitcoinde():
    offer_trs = []
    for page in range(1, 4):
        response = requests.get('https://www.bitcoin.de/de/offerSearch?page={}'
                                .format(page))
        doc = lxml.html.fromstring(response.text)
        offer_trs.extend(doc.xpath('//tr[@data-trade-id]'))
    return [{'exchange': 'bitcoinde',
             'price': Decimal('1.005') * Decimal(offer.xpath('@data-critical-price')[0]),
             'max_amount': Decimal('0.995') * Decimal(offer.xpath('@data-amount')[0]),
             'min_amount': Decimal('0.995') * get_min_amount(offer),
             'link': get_bitcoinde_buy_link(offer),
             'seller': get_bitcoinde_seller(offer)}
            for offer in offer_trs]


# def localbitcoins_convert_offer(offer_json):
#     price = Decimal(offer_json['data']['temp_price'])

#     def calc_limit(name):
#         eur_limit = Decimal(offer_json['data'][name])
#         return (eur_limit / price).quantize(Decimal('1.000'))

#     return {'exchange': 'localbitcoins',
#             'price': price,
#             'max_amount': calc_limit('max_amount_available'),
#             'min_amount': calc_limit('min_amount'),
#             'link': offer_json['actions']['public_view'],
#             'seller': offer_json['data']['profile']['name']}


# def localbitcoins():
#     response = requests.get(
#         'https://localbitcoins.com'
#         '/buy-bitcoins-online/EUR/sepa-eu-bank-transfer/.json')
#     offers = response.json()['data']['ad_list']
#     return [localbitcoins_convert_offer(offer) for offer in offers]


def localbitcoins_convert_offer(tr):
    price = Decimal(tr.xpath('td[@class="column-price"]/text()')[0].split()[0])
    min_str, max_str = (tr.xpath('td[@class="column-limit"]/text()')[0]
                        .split('-'))

    def calc_limit(limit_str):
        eur_limit = Decimal(limit_str)
        return (eur_limit / price).quantize(Decimal('1.000'))

    return {'exchange': 'localbitcoins',
            'price': price,
            'max_amount': calc_limit(max_str.split()[0]),
            'min_amount': calc_limit(min_str),
            'link': tr.xpath('.//a[@class="btn megabutton"]/@href')[0],
            'seller': tr.xpath('td[@class="column-user"]/a/text()')[0]}


def localbitcoins():
    response = requests.get(
        'https://localbitcoins.com'
        '/buy-bitcoins-online/eur/sepa-eu-bank-transfer/')
    doc = lxml.html.fromstring(response.text)
    offer_trs = doc.xpath('//table[contains(@class, "table-bitcoins")]'
                          '//tr[@class="clickable"]')
    return [localbitcoins_convert_offer(tr) for tr in offer_trs]


def bitalo():
    response = requests.post('https://bitalo.com/stream',
                             data={'currency': 'EUR'})
    offers = response.json()['sell_offers']
    return [{'exchange': 'bitalo',
             'price': Decimal(offer['price']),
             'max_amount': Decimal(offer['amount']),
             'min_amount': Decimal('0.05'),
             'link': ('https://www.bitalo.com/exchange/buy/{}'
                      .format(offer['id'])),
             'seller': offer['username']}
            for offer in offers]


def main():
    # print localbitcoins()
    # import sys
    # sys.exit()
    # from pprint import pprint
    # pprint(bitalo())
    unsorted_offers = bitcoinde() + localbitcoins() + bitalo()
    offers = sorted(unsorted_offers, key=lambda offer: offer['price'])
    print(json.dumps(offers, indent=4, cls=DecimalEncoder))


if __name__ == '__main__':
    main()

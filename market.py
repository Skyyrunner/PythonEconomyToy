import agentactors
from marketrequest import average, Receipt
from decimal import Decimal

class Market:
    def __init__(self):
        self.buys = {}
        self.sells = {}
        self.agents = {}
        self.transactions = [] # list of dictionaries of arrays
        self.marketprices = {} # dict of 'market price' for previous round

    def recordtransaction(self, item, price):
        thing = self.transactions[-1].setdefault(item, [])
        thing.append(price)

    def getmarketprice(self, item):
        if item in self.marketprices:
            return self.marketprices[item]
        return None

    def updateprices(self):
        self.thismarketprice = {}
        if len(self.transactions) == 0:
            return
        for item in self.transactions[-1]:
            history = self.transactions[-1][item]
            self.marketprices[item] = average(history)

    def cleartrades(self):
        receipts = {}
        self.updateprices()
        self.transactions.append({})
        for item in self.buys:
            receipts[item] = []
            buys = self.buys[item]
            if item not in self.sells:
                # no-one to sell, reject all trades
                for buy in buys:
                    # "buy price" is set to 0 because money refunding is 
                    # done by subtracting offer from actual price.
                    receipt = Receipt(buy.who, None, item, buy.num, 0, buy.price)
                    receipts[item].append(receipt)
                continue
            sells = self.sells[item]
            buys  = sorted(buys, key=lambda r: r.price)
            sells = sorted(sells, key=lambda r: r.price, reverse=True)
            while len(buys) != 0 and len(sells) != 0:
                buy = buys[-1]
                sell = sells[-1]
                if buy.price < sell.price:
                    break # no more trades possible
                num = min(buy.num, sell.num)
                price = (buy.price + sell.price) // 2 # meet in the middle
                receipt = Receipt(buy.who, sell.who, item, num, price, buy.price)
                receipts[item].append(receipt)
                self.recordtransaction(item, receipt.price)
                # remove if the amount left to buy/sell is zero
                if buy.num > sell.num:
                    buy.num -= num
                    sells.pop()
                elif sell.num > buy.num:
                    sell.num -= num
                    buys.pop()
                else: # if equal, pop both
                    sells.pop()
                    buys.pop()
            # The leftovers should all get rejected.
            if len(sells) == 0:
                for buy in buys:
                    receipt = Receipt(buy.who, None, item, buy.num, 0, buy.price)
                    receipts[item].append(receipt)
            elif len(buys) == 0:
                for sell in sells:
                    receipt = Receipt(None, sell.who, item, sell.num, sell.price, None)
                    receipts[item].append(receipt)
        return receipts

    def processreceipts(self, receiptsdict):
        self.updateprices()
        for item in receiptsdict:
            marketprice = self.getmarketprice(item)
            receipts = receiptsdict[item]
            for receipt in receipts:
                # ones that have both buyer and seller:
                if receipt.buyer:
                    self.agents[receipt.buyer].applyreceipt(receipt, marketprice)
                if receipt.seller:
                    self.agents[receipt.seller].applyreceipt(receipt, marketprice)

    def clearAndProcess(self):
        self.processreceipts(self.cleartrades())

    def addagent(self, agent):
        if agent.name in self.agents:
            raise ValueError('The agent %s is already registered' % repr(agent.name))
        self.agents[agent.name] = agent

    def removeagent(self, agent):
        if agent.name in self.agents:
            del self.agents[agent.name] 

    def addbuy(self, request):
        arr = self.buys.setdefault(request.item, [])
        arr.append(request)

    def addsell(self, request):
        arr = self.sells.setdefault(request.item, [])
        arr.append(request)

if __name__ == '__main__':
    import unittest
    import agentactors
    from marketrequest import Request
    from pprint import pprint
    Verbose = True
    class MarketTest(unittest.TestCase):
        def test_clearrequests_simple(self):
            market = Market()
            agentactors.initbaseprices(market.marketprices)
            market.addbuy(Request('buy', 'Buyer 1', 'tools', Decimal('2'), 55))
            market.addsell(Request('sell', 'Seller 1', 'tools', Decimal('2'), 45))
            market.addsell(Request('sell', 'Seller 2', 'tools', Decimal('2'), 30))
            # first test that things are matched
            receipts = market.cleartrades()
            self.assertTrue(receipts)
            buy1receipt, sell1receipt, sell2receipt = None, None, None
            for receipt in receipts["tools"]:
                if receipt.seller == "Seller 1":
                    sell1receipt = receipt
                if receipt.seller == "Seller 2":
                    sell2receipt = receipt
                if receipt.buyer == "Buyer 1":
                    buy1receipt = receipt
            if Verbose:
                print("<test_clearrequests_simple>")
                pprint([buy1receipt, sell1receipt, sell2receipt])
            self.assertEqual(buy1receipt, sell2receipt)
            self.assertEqual(buy1receipt.num, 2)
            self.assertEqual(buy1receipt.price, 42)

        def test_clearrequests_combine(self):
            market = Market()
            agentactors.initbaseprices(market.marketprices)
            market.addbuy(Request('buy', 'Buyer 1', 'tools', Decimal('2'), 55))
            market.addsell(Request('sell', 'Seller 1', 'tools', Decimal('2'), 45))
            market.addsell(Request('sell', 'Seller 2', 'tools', Decimal('1'), 30))
            market.addsell(Request('sell', 'Seller 3', 'tools', Decimal('3'), 60))
            # first test that things are matched
            receipts = market.cleartrades()
            self.assertTrue(receipts)
            self.assertEqual(len(receipts['tools']), 4)
            buy1receipts = []
            sell1receipts = []
            sell2receipts = []
            for receipt in receipts["tools"]:
                if receipt.seller == "Seller 1":
                    sell1receipts.append(receipt)
                if receipt.seller == "Seller 2":
                    sell2receipts.append(receipt)
                if receipt.buyer == "Buyer 1":
                    buy1receipts.append(receipt)
            if Verbose:
                print("<test_clearrequests_combine>")
                pprint([buy1receipts, sell1receipts, sell2receipts])
            self.assertEqual(len(buy1receipts), 2)
            self.assertEqual(len(sell1receipts), 2)
            self.assertEqual(len(sell2receipts), 1)
            # sum has to be equal to original
            for thing in [(buy1receipts, 2), (sell1receipts, 2), (sell2receipts, 1)]:
                total = 0
                for r in thing[0]:
                    total += r.num
                self.assertEqual(total, thing[1])

        def test_process_requests(self):
            market = Market()
            agentactors.initbaseprices(market.marketprices)
            actors = [
                agentactors.Agent(),
                agentactors.Agent(),
                agentactors.Agent(),
                agentactors.Agent()
            ]
            actors[0].name = "Buyer 1"
            actors[1].name = "Seller 1"
            actors[1].additem('tools', Decimal('2'))
            actors[2].name = "Seller 2"
            actors[2].additem('tools', Decimal('1'))
            actors[3].name = "Seller 3"
            actors[3].additem('tools', Decimal('3'))
            for agent in actors:
                market.agents[agent.name] = agent
            market.addbuy(Request('buy', 'Buyer 1', 'tools', Decimal('2'), 60))
            market.addsell(Request('sell', 'Seller 1', 'tools', Decimal('2'), 45))
            market.addsell(Request('sell', 'Seller 2', 'tools', Decimal('1'), 30))
            market.addsell(Request('sell', 'Seller 3', 'tools', Decimal('3'), 60))
            receipts = market.cleartrades()
            print(receipts)
            market.processreceipts(receipts)
            self.assertEqual(actors[0].getitem('tools'), Decimal('2'))
            self.assertEqual(actors[0].money, 123)
            self.assertEqual(actors[1].getitem('tools'), Decimal('1'))
            self.assertEqual(actors[1].money, 152)
            self.assertEqual(actors[2].getitem('tools'), Decimal('0'))
            self.assertEqual(actors[2].money, 145)
            self.assertEqual(actors[3].getitem('tools'), Decimal('3'))
            self.assertEqual(actors[3].money, 100)
            market.updateprices()
            self.assertEqual(market.getmarketprice('tools'), Decimal('48.5'))

    unittest.main()
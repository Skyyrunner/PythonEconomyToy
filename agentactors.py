from marketrequest import Request, average
import random
from decimal import Decimal
import decimal
# initial prices for each good
# basic goods cost the least,
# and derived goods cost more
def initbaseprices(base):
    base['wood'] = 10
    base['food'] = 10
    base['ore']  = 10
    base['fuel'] = 10 # because 1 wood produces 2
    base['tools']= 40 # because needs 3 ingredients plus labor

class PriceBelief:
    def __init__(self, name, price):
        self.name = name
        self.mean = price
        self.range = price/2
        self.k = 0.2 # the % to change beliefs by

    def getPrice(self):
        m = self.mean - self.range
        m = 0 if m < 0 else m
        M = self.mean + self.range
        m, M = int(m), int(M)
        return random.randint(m, M)

    # if success, price==successprice.
    # if fail, price==marketprice
    def adjust(self, success, price):
        if success:
            self.range *= 1.0 - self.k
            self.range -= 1
            if self.range < 1:
                self.range = 1
        else:
            self.range *= 1.0 + self.k
            self.range += 1
        self.mean += (price - self.mean) * self.k

    def __str__(self):
        return "<%s Belief: %d <= %d <= %d>" % (
            repr(self.name),
            self.mean-self.range,
            self.mean,
            self.mean+self.range)

class Agent:
    def __init__(self):
        self.name = None
        self.job = None
        self.needs = {}
        self.produces = []
        self.inventory = {}
        self.money = 100
        self.pricebeliefs = {}
        self.margin = 2 # eg, if "needs" 10 will aim to buy 20 for safety.
        self.receipts = []

    def __repr__(self):
        return "<Agent: %s, %s>" % (repr(self.name), repr(self.job))

    def additem(self, item, number):
        if number <= 0:
            raise ValueError("%d is not a valid number of items" % number)
        if item in self.inventory:
            self.inventory[item] += number
        else:
            self.inventory[item] = number

    # if ignoreLack is true, don't raise an error when trying to remove too many.
    # mostly for the Food item.
    def removeitem(self, item, number, ignoreLack=False):
        if number <= 0:
            raise ValueError("%d is not a valid number of items" % number)
        if item not in self.inventory:
            if not ignoreLack:
                raise ValueError("%s does not have any %s but tried to remove %d"
                 % (repr(self), repr(item), number))
            return
        if self.inventory[item] < number:
            if not ignoreLack:
                raise ValueError("Agent only has %d %s, tried to remove %d" %
                (self.inventory[item], item, number))
            return
        self.inventory[item] -= number
        if self.inventory[item] <= 0:
            del self.inventory[item]

    def getitem(self, item):
        if item in self.inventory:
            return self.inventory[item]
        return Decimal(0)

    # select a random price in a range
    def makeoffer(self, item):
        return self.pricebeliefs[item].getPrice()

    def initialproduce(self):
        for thing in self.produces:
            for product, number in thing['produces']:
                self.additem(product, number)

    def produce(self):
        self.removeitem('food', 1, ignoreLack=True)
        # attempt to do job.
        # can only do 1 reaction per turn
        for reaction in self.produces:
            canmake = True
            for req in reaction['needs']:
                if self.getitem(req[0]) < req[1]:
                    canmake = False
                    break
            if canmake:
                for req in reaction['needs']:
                    self.removeitem(req[0], req[1])
                for result in reaction['produces']:
                    self.additem(result[0], result[1])

    def setbeliefs(self, marketprices):
        for thing in marketprices:
            price = marketprices[thing]
            self.pricebeliefs[thing] = PriceBelief(thing,price) 

    def shiftbelief(self, item, success, price):
        if item in self.pricebeliefs: # if it exists!
            self.pricebeliefs[item].adjust(success, price)
        else:
            self.pricebeliefs[item] = PriceBelief(item, price)
                
    def makerequests(self, market):
        # buys
        for item in self.needs:
            # compare market price with own belief of price
            belief = self.makeoffer(item)
            favor =  belief / market.getmarketprice(item)
            # if favor is over  1, buy more
            # if favor is under 1, buy less
            # also needs to cast from Decimal to float
            ordersize = round(favor * float(self.needs[item] - self.getitem(item)))
            ordersize = int(ordersize)
            if belief == 0: # not willing to buy
                continue 
            ordersize = min(ordersize, round(self.money / belief))
            if ordersize > 0:
                # can only place orders in multiples of 10
                req = Request(kind="buy", who=self.name,
                 item=item, num=ordersize, price=belief)
                market.addbuy(req)
                self.money -= ordersize * belief
        # sells
        for item in self.inventory:
            amount = self.getitem(item)
            if item in self.needs:
                amount -= self.needs[item]
            if amount > 0: # have more than amount of unneeded items
                belief = self.makeoffer(item)
                favor = belief / market.getmarketprice(item)
                ordersize = int(round(favor * float(amount))) # cast decimal to float
                if ordersize > amount:
                    ordersize = amount
                if ordersize > 0:
                    req = Request(kind="sell", who=self.name,
                        item=item, num=ordersize, price=belief)
                    market.addsell(req)

    def applyreceipt(self, receipt, marketprice):
        if receipt.buyer == self.name:                
            # refund extra money
            self.money += receipt.num * (receipt.offer - receipt.price)
            self.additem(receipt.item, receipt.num)
            # shift price beliefs
            if not receipt.seller: # failed to buy
                self.shiftbelief(receipt.item, False, marketprice)
            else:
                self.shiftbelief(receipt.item, True, receipt.price)
        elif receipt.seller == self.name:
            if not receipt.buyer:
                self.shiftbelief(receipt.item, False, marketprice)
            else:
                # give returns from sale
                self.money += receipt.num * receipt.price
                self.removeitem(receipt.item, receipt.num)
                self.shiftbelief(receipt.item, True, receipt.price)

agentcounter = 0
def makeagent(kind, market):
    global agentcounter
    newagent = Agent()
    if kind == 'wood burner':
        newagent.needs = {
            'wood': Decimal(1),
            'food': Decimal(1)
        }
        newagent.produces = [
            {
                'needs': [('wood', Decimal(1))], # 1 wood to 2 fuel
                'produces': [('fuel', Decimal(2))]
            }
        ]
    elif kind == 'wood cutter':
        newagent.needs = {
            'food': Decimal(1),
            'tools': Decimal(1)
        }
        newagent.produces = [
            {
                'needs': [('tools', Decimal('0.1'))],
                'produces': [('wood', Decimal(2))]
            }
        ]
    elif kind == 'miner':
        newagent.needs = {
            'food': Decimal(1),
            'tools': Decimal(1)
        }
        newagent.produces = [
            {
                'needs': [('tools', Decimal('0.1'))],
                'produces': [('ore', Decimal(2))]
            }
        ]
    elif kind == 'blacksmith':
        newagent.needs = {
            'food': Decimal(1),
            'fuel': Decimal(1),
            'ore' : Decimal(1)
        }
        newagent.produces = [
            {
                'needs': [('fuel', Decimal(1)), ('ore', Decimal(1))],
                'produces': [('tools', Decimal(1))]
            }
        ]
    elif kind == 'farmer':
        newagent.needs = {
            'food': Decimal(1),
            'tools': Decimal(1)
        }
        newagent.produces = [
            {
                'needs': [('tools', Decimal('0.1'))],
                'produces': [('food', Decimal(3))]
            }
        ]
    else:
        raise KeyError("No such agent type named %s" % repr(kind))
    newagent.initialproduce()
    newagent.name = 'Agent ' + str(agentcounter)
    newagent.job = kind
    newagent.additem('tools', Decimal('0.2'))
    newagent.setbeliefs(market.marketprices)
    agentcounter += 1
    return newagent


agenttypes = ["farmer", "wood burner", "wood cutter", "miner", "blacksmith"]
def makerandomagent(market):
    kind = random.choice(agenttypes)
    return makeagent(kind, market)

if __name__=='__main__':
    Verbose = True
    import unittest
    from pprint import pprint
    from marketrequest import Receipt
    class DummyMarket:
        def __init__(self):
            self.buys = []
            self.sells = []
            self.marketprices = {}
            initbaseprices(self.marketprices)

        def getmarketprice(self, item):
            return self.marketprices[item]

        def addbuy(self, request):
            self.buys.append(request)

        def addsell(self, request):
            self.sells.append(request)

    class BeliefTest(unittest.TestCase):
        def test_belief(self):
            belief = PriceBelief('banana', 10)
            for x in range(100):
                self.assertTrue(5 <= belief.getPrice() <= 15)
            # test adjusting beliefs
            tests = [(True, 10, 10), (True, 20, 12), (True, 100, 29.6)]
            for x in range(len(tests)):
                with self.subTest(i=x):
                    belief.adjust(tests[x][0], tests[x][1])
                    self.assertEqual(belief.mean, tests[x][2])
            belief = PriceBelief('banana', 10)
            tests = [(False, 10), (False, 20), (False, 100)]
            prevM = belief.mean
            prevRange = belief.range
            for x in range(len(tests)):
                with self.subTest(i=x):
                    belief.adjust(tests[x][0], tests[x][1])
                    self.assertTrue(prevM <= belief.mean)
                    self.assertTrue(prevRange < belief.range)
                    prevM, prevRange = belief.mean, belief.range

    class AgentTest(unittest.TestCase):
        def test_initialization(self):
            agent = makeagent('miner', DummyMarket())
            self.assertEqual(agent.inventory["ore"], 2)
            # also test averages
            test = [0, 1, 2, 3]
            self.assertEqual(average(test), 1.5)
            test = [-1, 0, 2, -1]
            self.assertEqual(average(test), 0)
            test = []
            with self.assertRaises(ValueError) as cm:
                average(test)

        def test_reaction(self):
            agent = makeagent('blacksmith', DummyMarket())
            self.assertEqual(agent.getitem('tools'), Decimal('1.2'))
            agent.produce() # doesn't have the ingredients
            # so should have the same amount afterwards
            self.assertEqual(agent.getitem('tools'), Decimal('1.2'))
            agent.additem('ore', Decimal('0.5'))
            agent.additem('fuel', 1)
            agent.produce() # still not enough ore
            self.assertEqual(agent.getitem('tools'), Decimal('1.2'))
            agent.additem('ore', Decimal('0.5'))
            agent.produce()
            self.assertEqual(agent.getitem('tools'), Decimal('2.2'))
            # check for foodness
            for item in agent.inventory:
                self.assertTrue(agent.inventory[item] > 0)

        def test_placeorder(self):
            market = DummyMarket()
            agents = []
            agents.append(makeagent('miner', market))
            agents.append(makeagent('blacksmith', market))
            agents.append(makeagent('farmer', market))
            agents.append(makeagent('wood cutter', market))
            agents.append(makeagent('wood burner', market))
            for agent in agents:
                agent.makerequests(market)
            self.assertTrue(len(market.buys) != 0)
            if Verbose:
                pprint(market.buys)
            self.assertTrue(len(market.sells) != 0)
            if Verbose:
                pprint(market.sells)
                for req in market.buys:
                    self.assertTrue(req.num >= 1)
                    self.assertIsInstance(req.num, int)
                    self.assertEqual((req.num * 10) % 10, 0)
                print("Monies: "+str([x for x in map(lambda x: x.money, agents)]))
            for agent in agents:
                self.assertTrue(0 <= agent.money <= 100)

        def test_processreceipt(self):
            d = {}
            initbaseprices(d)
            agent = Agent()
            agent.setbeliefs(d)
            agent.name = "Wang Peng"
            agent.applyreceipt(Receipt("Wang Peng", "Li You", "tools", 2, 40, 60)
                , 45)
            self.assertEqual(agent.money, Decimal('140'))
            self.assertEqual(agent.getitem('tools'), 2)

        def test_processnewitemtype(self):
            d = {}
            initbaseprices(d)
            agent = Agent()
            agent.setbeliefs(d)
            agent.name = "Wang Peng"
            agent.applyreceipt(Receipt("Wang Peng", "Li You", "apples", 1, 10, 15)
                , 45)

    unittest.main()
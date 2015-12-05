from marketrequest import Request
import random

# initial prices for each good
# basic goods cost the least,
# and derived goods cost more
def initbaseprices(base):
    base['wood'] = [10]
    base['food'] = [10]
    base['ore']  = [10]
    base['fuel'] = [10] # because 1 wood produces 2
    base['tools']= [40] # because needs 3 ingredients plus labor

def average(L):
    if len(L) == 0:
        raise ValueError('Cannot compute average on empty list')
    l = len(L)
    s = sum(L)
    return s/l

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
        return random.randint(m, M)

    def adjust(self, success, average):
        if success:
            self.range *= 1.0 - self.k
            self.range -= 1
            if self.range < 0:
                self.range = 1
        else:
            self.range *= 1.0 + self.k
            self.range += 1
            self.mean += (average - self.mean) * self.k
        self.range = int(self.range)
        self.mean  = int(self.mean)

    def __str__(self):
        return "<Belief: %d <= %d <= %d>" % (self.mean-self.range,
            self.mean,
            self.mean+self.range)

class Agent:
    def __init__(self):
        self.name = None
        self.needs = {}
        self.produces = []
        self.inventory = {}
        self.money = 0
        self.pricebeliefs = {}

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
                raise ValueError("Agent does not have any %s" % repr(item))
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
        return 0

    def initialproduce(self):
        for thing in self.produces:
            for product, number in thing['produces']:
                self.additem(product, number)

    def produce(self):
        self.removeitem('food', 10, ignoreLack=True)
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

    def setbeliefs(self, market):
        for thing in market.pricehistories:
            price = market.pricehistories[thing]
            price = int(average(price))
            self.pricebeliefs[thing] = PriceBelief(thing,price) 
                

    def makerequests(self, market):
        pass


agentcounter = 0
def makeagent(kind, market):
    global agentcounter
    newagent = Agent()
    if kind == 'wood burner':
        newagent.needs = {
            'wood': 10,
            'food': 10
        }
        newagent.produces = [
            {
                'needs': [('wood', 10)], # 1 wood to 2 fuel
                'produces': [('fuel', 20)]
            }
        ]
    elif kind == 'lumberjack':
        newagent.needs = {
            'food': 10,
            'tools': 1
        }
        newagent.produces = [
            {
                'needs': [('tools', 1)],
                'produces': [('wood', 20)]
            }
        ]
    elif kind == 'miner':
        newagent.needs = {
            'food': 10,
            'tools': 1
        }
        newagent.produces = [
            {
                'needs': [('tools', 1)],
                'produces': [('ore', 20)]
            }
        ]
    elif kind == 'blacksmith':
        newagent.needs = {
            'food': 10,
            'fuel': 10,
            'ore' : 10
        }
        newagent.produces = [
            {
                'needs': [('fuel', 10), ('ore', 10)],
                'produces': [('tools', 10)]
            }
        ]
    elif kind == 'farmer':
        newagent.needs = {
            'food': 10,
            'tools': 1
        }
        newagent.produces = [
            {
                'needs': [('tools', 1)],
                'produces': [('food', 30)]
            }
        ]
    else:
        raise KeyError("No such agent type named %s" % repr(kind))
    newagent.initialproduce()
    newagent.name = 'Agent ' + str(agentcounter)
    newagent.setbeliefs(market)
    agentcounter += 1
    return newagent

if __name__=='__main__':
    import unittest
    class DummyMarket:
        def __init__(self):
            self.buys = []
            self.sells = []
            self.pricehistories = {}
            initbaseprices(self.pricehistories)

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
            tests = [(True, 10), (True, 20), (True, 100)]
            for x in range(len(tests)):
                with self.subTest(i=x):
                    belief.adjust(tests[x][0], tests[x][1])
                    self.assertEqual(belief.mean, 10)
            tests = [(False, 10), (False, 20), (False, 100), (False, 5)]
            results = [10, 12, 20, 25]
            for x in range(len(tests)):
                with self.subTest(i=x):
                    belief.adjust(tests[x][0], tests[x][1])
                    self.assertTrue(belief.range >= 2)
                    if x==3:
                        self.assertTrue(belief.mean <= results[x])    
                    else:
                        self.assertTrue(belief.mean >= results[x])

    class AgentTest(unittest.TestCase):
        def test_initialization(self):
            agent = makeagent('miner', DummyMarket())
            self.assertEqual(agent.inventory["ore"], 20)
            # also test averages
            test = [0, 1, 2, 3]
            self.assertEqual(average(test), 1.5)
            test = [-1, 0, 2, -1]
            self.assertEqual(average(test), 0)
        
        def test_reaction(self):
            agent = makeagent('blacksmith', DummyMarket())
            self.assertEqual(agent.getitem('tools'), 10)
            agent.produce() # doesn't have the ingredients
            # so should have the same amount afterwards
            self.assertEqual(agent.getitem('tools'), 10)
            agent.additem('ore', 5)
            agent.additem('fuel', 10)
            agent.produce() # still not enough ore
            self.assertEqual(agent.getitem('tools'), 10)
            agent.additem('ore', 5)
            agent.produce()
            self.assertEqual(agent.getitem('tools'), 20)
            # check for foodness
            for item in agent.inventory:
                self.assertTrue(agent.inventory[item] > 0)

        def test_placeorder(self):
            market = DummyMarket()
            miner= makeagent('miner', market)
            blacksmith = makeagent('blacksmith', market)
            farmer = makeagent('farmer', market)
            miner.makerequests(market)
            blacksmith.makerequests(market)
            farmer.makerequests(market)
    unittest.main()
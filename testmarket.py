from market import Market
from agentactors import makerandomagent, initbaseprices, agenttypes, resourcetypes
from pprint import pprint

def createmarket(numagents=15):
    agents = []
    market = Market()
    initbaseprices(market.marketprices)
    for x in range(numagents):
        agents.append(makerandomagent(market))
        market.addagent(agents[-1])
    return agents, market

resourcefromjob = {}
for i in range(len(resourcetypes)):
    resourcefromjob[agenttypes[i]] = resourcetypes[i]
class World:
    def __init__(self, numagents=15):
        self.agents, self.market = createmarket(numagents)
        self.prices = {}
        self.buyfreq = {}
        self.sellfreq = {}
        self.agenttypes = {}

    def step(self):
        for a in self.agents:
            a.makerequests(self.market)
        r = self.market.cleartrades()
        self.market.processreceipts(r)
        for a in self.agents:
            a.produce()

    def countthings(self):
        marketprices = self.market.marketprices
        # pprint(marketprices)
        for item in marketprices:
            try:
                self.prices[item].append(marketprices[item])
            except:
                self.prices[item] = [marketprices[item]]
        BUYFREQ = self.market.buyorderfreq
        for item in BUYFREQ:
            try:
                self.buyfreq[item].append(BUYFREQ[item])
            except:
                self.buyfreq[item] = [BUYFREQ[item]]
        SELLFREQ = self.market.sellorderfreq
        for item in SELLFREQ:
            try:
                self.sellfreq[item].append(SELLFREQ[item])
            except:
                self.sellfreq[item] = [SELLFREQ[item]]
        # count agent job distribution
        for agenttype in agenttypes:
            try:
                self.agenttypes[resourcefromjob[agenttype]].append(0)
            except:
                self.agenttypes[resourcefromjob[agenttype]] = [0]
        for agent in self.agents:
            self.agenttypes[resourcefromjob[agent.job]][-1] += 1

# import rpdb2; rpdb2.start_embedded_debugger('1234')

if __name__=="__main__":
    import json
    from decimal import Decimal

    class DecimalEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, Decimal):
                return float(o)
            return super(DecimalEncoder, self).default(o)

    items = ['food','fuel','wood', 'ore', 'tools']
    def jsonformatitems(d, f):
        json.dump(d, f, cls=DecimalEncoder)
    world = World(15)
    for x in range(150):
        world.step()
        world.countthings()
    outdir = "/var/www/html/raw/"
    files = [(world.prices, "prices"),
             (world.sellfreq, "sells"),
             (world.buyfreq, "buys"),
             (world.agenttypes, "agents")]
    for obj, name in files:
        with open(outdir + name + ".json", "w") as f:
            jsonformatitems(obj, f)
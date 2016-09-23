from market import Market
import agentactors
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
        # many many logs
        self.prices = {}
        self.buyfreq = {}
        self.sellfreq = {}
        self.agenttypes = {}
        self.volume = {} # how much product was actually moved
        for i in resourcetypes:
            self.volume[i] = []
        self.agentcounter = [] # to see agent replacement rate

    def step(self):
        for a in self.agents:
            a.money -= 1
            a.makerequests(self.market)
        r = self.market.cleartrades()
        self.countvolume(r)
        self.market.processreceipts(r)
        for a in self.agents:
            a.produce()
        # if an agent has less than N money, remove and replace with
        # more profitable one.
        for i in range(len(self.agents)):
            money = self.agents[i].money
            if money < -5:
                oldagent = self.agents[i]
                self.market.removeagent(oldagent)
                # for now, add a random job.
                self.agents[i] = makerandomagent(self.market)
                newagent = self.agents[i]
                self.market.addagent(newagent)

    def countvolume(self, receipts):
        for i in resourcetypes:
            self.volume[i].append(0);
        for item in receipts:
            for r in receipts[item]:
                if r.buyer and r.seller: # the trade actually happened.
                    self.volume[r.item][-1] += r.num


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
        # set delta agent
        try:
            self.agentcounter.append(agentactors.agentcounter - self.agentcounter[-1])
        except:
            self.agentcounter.append(agentactors.agentcounter)

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
    world = World(50)
    world.agentcounter = [250]
    for x in range(500):
        world.step()
        world.countthings()
    outdir = "/usr/share/nginx/html/raw/"
    files = [(world.prices, "prices"),
             (world.sellfreq, "sells"),
             (world.buyfreq, "buys"),
             (world.volume, "volume"),
             (world.agenttypes, "agents")]
    for obj, name in files:
        with open(outdir + name + ".json", "w") as f:
            jsonformatitems(obj, f)
    print(agentactors.agentcounter)
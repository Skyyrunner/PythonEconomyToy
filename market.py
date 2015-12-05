import agentactors

class Market:
    def __init__(self):
        self.buys = {}
        self.sells = {}
        self.marketprices = {}
        self.agents = {}
        self.pricehistories = {} # average prices per round.
        # may have to implement compression once it gets too long

    def cleartrades(self):
        pass

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

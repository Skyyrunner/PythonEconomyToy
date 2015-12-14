class Request:
    def __init__(self, kind, who, item, num, price):
        self.item = item
        self.num = num
        self.price = price
        self.who = who
        self.kind = kind

    def __repr__(self):
        return "<Request: %s %s %d %s at %dg per>" % (self.who, self.kind,
         self.num, self.item, self.price)

class Receipt:
    def __init__(self, buyer, seller, item, num, price, offer):
        self.item = item
        self.num = num
        self.price = price
        self.offer = offer # how much the buyer initially offerd.
        # required because need to refund buyer some money.
        self.buyer = buyer
        self.seller = seller

    def __repr__(self):
        return "<Receipt: %s bought %d %s from %s for %sg each>" % (self.buyer, 
            self.num, self.item, self.seller, self.price)

def average(L):
    if len(L) == 0:
        raise ValueError('Cannot compute average on empty list')
    l = len(L)
    s = sum(L)
    return s/l
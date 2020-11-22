import re
from NDChild import NDChild

class TriggerCacher:
    def __init__(self):
        self.current_trigger = None
        self.current_sentence = None
        self.trigger_methods = [NDChild.spEtrigger,
                                NDChild.hipEtrigger,
                                NDChild.hcpEtrigger,
                                NDChild.optEtrigger,
                                NDChild.nsEtrigger,
                                NDChild.ntEtrigger,
                                NDChild.whmEtrigger,
                                NDChild.piEtrigger,
                                NDChild.tmEtrigger,
                                NDChild.VtoIEtrigger,
                                NDChild.ItoCEtrigger,
                                NDChild.ahEtrigger,
                                NDChild.QInvEtrigger]

    def trigger_name(self, method):
        name = re.sub('Etrigger', '', method.__name__)
        name = name.upper() if name.islower() else name
        return name

    def set_trigger(self, source_trigger, sentence, param, direction, conservative: bool):
        trigs = sentence.triggers
        if source_trigger not in trigs:
            trigs[source_trigger] = [(param, direction, conservative)]
        else:
            trigs[source_trigger].append((param, direction, conservative))

    def adjustweight(self, param, direction):
        self.set_trigger(self.current_trigger, self.current_sentence, param, direction, False)

    def adjustweightConservatively(self, param, direction):
        self.set_trigger(self.current_trigger, self.current_sentence, param, direction, True)

    def consume_sentence(self, s):
        child = NDChild(None, None, None)
        child.adjustweight = self.adjustweight
        child.adjustweightConservatively = self.adjustweightConservatively
        for trigger in self.trigger_methods:
            self.current_trigger = self.trigger_name(trigger)
            self.current_sentence = s
            trigger(child, s)
        self.current_trigger = None
        self.current_sentence= None

cacher = TriggerCacher()

class InstrumentedNDChild(NDChild):
    @staticmethod
    def precompute_sentence(sentence):
        cacher.consume_sentence(sentence)
        return
        child = NDChild(None, None, 611)
        current_trigger = [None]
        child.adjustweight = lambda param, direction: (
            set_trigger(current_trigger[0], sentence, param, direction, conservative=False))
        child.adjustweightConservatively = lambda param, direction: (
            set_trigger(current_trigger[0], sentence, param, direction, conservative=True))

        triggers = [child.spEtrigger,
                    child.hipEtrigger,
                    child.hcpEtrigger,
                    child.optEtrigger,
                    child.nsEtrigger,
                    child.ntEtrigger,
                    child.whmEtrigger,
                    child.piEtrigger,
                    child.tmEtrigger,
                    child.VtoIEtrigger,
                    child.ItoCEtrigger,
                    child.ahEtrigger,
                    child.QInvEtrigger]

        for trigger in triggers:
            name = re.sub('Etrigger', '', trigger.__name__)
            name = name.upper() if name.islower() else name
            current_trigger[0] = name
            trigger(sentence)

    def handleTrigger(self, sentence, etrigger):
        if etrigger not in sentence.triggers:
            return
        for param, direction, conservative in sentence.triggers[etrigger]:
            if conservative:
                self.adjustweightConservatively(param, direction)
            else:
                self.adjustweight(param, direction)

    def QInvEtrigger(self, s):
        self.handleTrigger(s, 'QInv')

    def VtoIEtrigger(self, s):
        self.handleTrigger(s, 'VtoI')

    def hcpEtrigger(self, s):
        self.handleTrigger(s, 'HCP')

    def hipEtrigger(self, s):
        self.handleTrigger(s, 'HIP')

    def nsEtrigger(self, s):
        self.handleTrigger(s, 'NS')

    def ntEtrigger(self, s):
        self.handleTrigger(s, 'NT')

    def piEtrigger(self, s):
        self.handleTrigger(s, 'PI')

    def spEtrigger(self, s):
        self.handleTrigger(s, 'SP')

    def tmEtrigger(self, s):
        self.handleTrigger(s, 'TM')

    def whmEtrigger(self, s):
        self.handleTrigger(s, 'WHM')

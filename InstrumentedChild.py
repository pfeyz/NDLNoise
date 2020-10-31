from NDChild import NDChild

def set_trigger(sentence, param, direction, conservative: bool):
    sentence.triggers[param] = (direction, conservative)


class InstrumentedNDChild(NDChild):

    @staticmethod
    def precompute_sentence(sentence):
        child = NDChild(None, None, 611)
        child.adjustweight = lambda param, direction: (
            set_trigger(sentence, param, direction, conservative=False))
        child.adjustweightConservatively = lambda param, direction: (
            set_trigger(sentence, param, direction, conservative=True))
        child.consumeSentence(sentence)

    def handleTrigger(self, sentence, param):
        if param in sentence.triggers:
            direction, conservative = sentence.triggers[param]
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


# for method in ['QInvEtrigger', 'VtoIEtrigger', 'hcpEtrigger', 'hipEtrigger',
#                'nsEtrigger', 'ntEtrigger', 'piEtrigger', 'spEtrigger',
#                'tmEtrigger', 'whmEtrigger']:
#     param = method.replace('Etrigger', '')
#     if param.islower():
#         param = param.upper()  #
#     print("""    def {method}(self, s):
#         if '{param}' in s.triggers:
#             direction, rate = s.triggers['{param}']
#             self.adjustweight('{param}', direction, rate)
#         """.format(
#         method=method, param=param))

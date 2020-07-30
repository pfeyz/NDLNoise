from NDChild import NDChild

def set_trigger(sentence, param, direction, weight):
    sentence.triggers[param] = (direction, weight)



class InstrumentedNDChild(NDChild):
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     for method in ['QInvEtrigger', 'VtoIEtrigger', 'hcpEtrigger', 'hipEtrigger',
    #                    'nsEtrigger', 'ntEtrigger', 'piEtrigger', 'spEtrigger',
    #                    'tmEtrigger', 'whmEtrigger']:
    #         param = method.replace('Etrigger', '')
    #         if param.islower():
    #             param = param.upper()
    #         setattr(self, method, lambda s: self.trigger(s, param))

    @classmethod
    def precompute(cls, domains, rate, conservativerate):
        for language in domains.values():
            for sentence in language[0]:
                child = NDChild(rate, conservativerate, 611)
                child.adjustweight = lambda param, direction, weight: set_trigger(sentence,
                                                                                  param,
                                                                                  direction,
                                                                                  weight)
                child.consumeSentence(sentence)

    def trigger(self, param, s):
        if param in s.triggers:
            self.adjustweight(param, *s.triggers[param])

    def QInvEtrigger(self, s):
        self.trigger('QInv', s)
    def VtoIEtrigger(self, s):
        self.trigger('VtoI', s)
    def hcpEtrigger(self, s):
        self.trigger('HCP', s)
    def hipEtrigger(self, s):
        self.trigger('HIP', s)
    def nsEtrigger(self, s):
        self.trigger('NS', s)
    def ntEtrigger(self, s):
        self.trigger('NT', s)
    def piEtrigger(self, s):
        self.trigger('PI', s)
    def spEtrigger(self, s):
        self.trigger('SP', s)
    def tmEtrigger(self, s):
        self.trigger('TM', s)
    def whmEtrigger(self, s):
        self.trigger('WHM', s)

# for method in ['QInvEtrigger', 'VtoIEtrigger', 'hcpEtrigger', 'hipEtrigger',
#                'nsEtrigger', 'ntEtrigger', 'piEtrigger', 'spEtrigger',
#                'tmEtrigger', 'whmEtrigger']:
#     param = method.replace('Etrigger', '')
#     if param.islower():
#         param = param.upper()  #
#     print("""    def {method}(self, s):\n        self.trigger('{param}', s)""".format(
#         method=method, param=param))

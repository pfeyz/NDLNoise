from NDChild import NDChild

def set_trigger(sentence, param, direction, weight):
    sentence.triggers[param] = (direction, weight)


class NDMeta(type):
    def __new__(cls, name, bases, dct):
        cls = super().__new__(cls, name, bases, dct)
        for method in ['QInvEtrigger', 'VtoIEtrigger', 'hcpEtrigger',
                       'hipEtrigger', 'nsEtrigger', 'ntEtrigger', 'piEtrigger',
                       'spEtrigger', 'tmEtrigger', 'whmEtrigger']:
            param = method.replace('Etrigger', '')
            if param.islower():
                param = param.upper()
            setattr(cls, method, lambda self, s: self.trigger(param, s))
        return cls


class InstrumentedNDChild(NDChild): #, metaclass=NDMeta):

    @staticmethod
    def precompute_sentence(sentence, rate, conservativerate):
        child = NDChild(rate, conservativerate, 611)
        child.adjustweight = lambda param, direction, weight: (
            set_trigger(sentence, param, direction, weight))
        child.consumeSentence(sentence)

    def trigger(self, param, s):
        if param in s.triggers:
            self.adjustweight(param, *s.triggers[param])

    def QInvEtrigger(self, s):
        if 'QInv' in s.triggers:
            direction, rate = s.triggers['QInv']
            self.adjustweight('QInv', direction, rate)

    def VtoIEtrigger(self, s):
        if 'VtoI' in s.triggers:
            direction, rate = s.triggers['VtoI']
            self.adjustweight('VtoI', direction, rate)

    def hcpEtrigger(self, s):
        if 'HCP' in s.triggers:
            direction, rate = s.triggers['HCP']
            self.adjustweight('HCP', direction, rate)

    def hipEtrigger(self, s):
        if 'HIP' in s.triggers:
            direction, rate = s.triggers['HIP']
            self.adjustweight('HIP', direction, rate)

    def nsEtrigger(self, s):
        if 'NS' in s.triggers:
            direction, rate = s.triggers['NS']
            self.adjustweight('NS', direction, rate)

    def ntEtrigger(self, s):
        if 'NT' in s.triggers:
            direction, rate = s.triggers['NT']
            self.adjustweight('NT', direction, rate)

    def piEtrigger(self, s):
        if 'PI' in s.triggers:
            direction, rate = s.triggers['PI']
            self.adjustweight('PI', direction, rate)

    def spEtrigger(self, s):
        if 'SP' in s.triggers:
            direction, rate = s.triggers['SP']
            self.adjustweight('SP', direction, rate)

    def tmEtrigger(self, s):
        if 'TM' in s.triggers:
            direction, rate = s.triggers['TM']
            self.adjustweight('TM', direction, rate)

    def whmEtrigger(self, s):
        if 'WHM' in s.triggers:
            direction, rate = s.triggers['WHM']
            self.adjustweight('WHM', direction, rate)


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

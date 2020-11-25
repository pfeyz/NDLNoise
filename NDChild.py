import re
from utils import progress_bar


def format_val(val):
    if isinstance(val, float):
        return round(val, 2)
    else:
        return val


class NDChild(object):
    def __repr__(self):
        return 'NDChild({})'.format({k: format_val(v)
                                     for k, v in self.grammar.items()})

    def __init__(self, learningrate, conslearningrate, language):

        self.grammar = {"SP": .5, "HIP": .5, "HCP": .5, "OPT": .5, "NS": .5, "NT": .5, "WHM": .5,
                        "PI": .5, "TM": .5, "VtoI": .5, "ItoC": .5, "AH": .5, "QInv": .5}
        self.target_language = language
        self.r = learningrate  # simulation will pass child a learning rate
        self.conservativerate = conslearningrate
        #self.oprate = oprate
        #self.vtoirate=vtoirate

        self.trigger_methods = [
            self.spEtrigger,
            self.hipEtrigger,
            self.hcpEtrigger,
            self.optEtrigger,
            self.nsEtrigger,
            self.ntEtrigger,
            self.whmEtrigger,
            self.piEtrigger,
            self.tmEtrigger,
            self.VtoIEtrigger,
            self.ItoCEtrigger,
            self.ahEtrigger,
            self.QInvEtrigger
        ]

    def consumeSentence(self, s):  # child is fed a list containing [lang, inflec, sentencestring]
        for trigger in self.trigger_methods:
            trigger(s)

    # etriggers for parameters
    # first parameter Subject Position
    def spEtrigger(self, s):
        # Check if O1 and S are in the sentence and sent is declarative
        if "O1" in s.sentenceList and "S" in s.sentenceList and s.inflection == "DEC":
            O1index = s.sentenceList.index("O1")
            Sindex = s.sentenceList.index("S")  # Sindex is position of S in sentList
            # Make sure O1 is non-sentence-initial and before S
            if O1index > 0 and O1index < s.sentenceList.index("S"):
                # set towards Subject final
                self.adjustweight("SP", 1)
            # S occurs before 01
            elif Sindex > 0 and O1index > s.sentenceList.index("S"):  # S cannot be Sent initial
                # set towards Subject initial
                self.adjustweight("SP", 0)

    # second parameter Head IP, VP, PP, etc
    def hipEtrigger(self, s):
        if "O3" in s.sentenceList and "P" in s.sentenceList:
            O3index = s.sentenceList.index("O3")
            Pindex = s.sentenceList.index("P")
            # O3 followed by P and not topicalized
            if O3index > 0 and Pindex == O3index + 1:
                self.adjustweight("HIP", 1)
            elif O3index > 0 and Pindex == O3index - 1:
                self.adjustweight("HIP", 0)

        # If imperative, make sure Verb directly follows O1
        elif s.inflection == "IMP" and "O1" in s.sentenceList and "Verb" in s.sentenceList:
            if s.sentenceList.index("O1") == s.sentenceList.index("Verb") - 1:
                self.adjustweight("HIP", 1)
            elif s.sentenceList.index("Verb") == (s.sentenceList.index("O1") - 1):
                self.adjustweight("HIP", 0)

    # third parameter Head in CP
    def hcpEtrigger(self, s):
        if s.inflection == "Q":
            # ka or aux last in question
            if s.sentenceList[-1] == 'ka' or ("ka" not in s.sentenceList and s.sentenceList[-1] == "Aux"):
                self.adjustweight("HCP", 1)
            # ka or aux first in question
            elif s.sentenceList[0] == "ka" or ("ka" not in s.sentenceList and s.sentenceList[0] == "Aux"):
                self.adjustweight("HCP", 0)

    # fourth parameter Optional Topic (0 is obligatory,  1 is optional)
    def optEtrigger(self, s):
        if s.inflection == "DEC" and self.grammar["TM"] > 0.5 and self.grammar[
            "NT"] < 0.5 and "[+WA]" not in s.sentenceStr:
            self.adjustweight("OPT", 1)
        #elif s.inflection == "DEC" and self.grammar["TM"] > 0.5 and self.grammar[
            #"NT"] < 0.5 and "[+WA]" in s.sentenceStr:
            #self.adjustweightConservatively("OPT", 0)

        elif s.inflection == "Q" and self.grammar["TM"] > 0.5 and self.grammar[
            "NT"] < 0.5 and "[+WA]" not in s.sentenceStr and "+WH" in s.sentenceStr:
            self.adjustweight("OPT", 1)
        #first word in sentence is any of those & overt subject and full complemenets in VP

        elif (self.grammar["NT"] < 0.5):
            if (s.inflection == "DEC" and s.sentenceList[0] in ["Verb", "Aux", "Not", "Never"]):
                self.adjustweight("OPT", 1)  # Opt to 1 unambig
                ##print("ka in DEC")
            if (s.sentenceList[0] in ["ka","Verb", "Aux", "Not", "Never"] and ("+WH" in s.sentenceStr)  and s.inflection=="Q"):
                self.adjustweight("OPT",1)
                ##print("ka in Q")
            elif self.grammar["NT"] < 0.5 and s.outOblique():
                self.adjustweightConservatively("OPT", 0)
                ##print("fullhouse")
        #if s.fullhouse():
            #self.adjustweightConservatively("OPT",1)
    def nsEtrigger(self, s):
        if s.inflection == "DEC" and "S" not in s.sentenceStr and s.outOblique():
            self.adjustweight("NS", 1)
            self.adjustweight("OPT", 1)

        elif s.inflection == "DEC" and "S" in s.sentenceStr and s.outOblique():
            self.adjustweightConservatively("NS", 0)

    def ntEtrigger(self, s):
        if s.inflection == "DEC" and "O2" in s.sentenceStr and "O1" not in s.sentenceStr:
            self.adjustweight("NT", 1)
            self.adjustweight("OPT", 0) # null topic necessitates obligatory topic

        elif s.inflection == "DEC" and "O2" in s.sentenceStr and "O1" in s.sentenceStr and "O3" in s.sentenceStr and "S" in s.sentenceStr and "Adv" in s.sentenceStr:
            self.adjustweightConservatively("NT", 0)
        # if all possible complements of VP are in sentence, then the sentence is not Null Topic

    def whmEtrigger(self, s):
        if s.inflection == "Q" and "+WH" in s.sentenceStr:
            if ("+WH" in s.sentenceList[0]) or ("P" in s.sentenceList[0] and "O3[+WH]" == s.sentenceList[1]):
                self.adjustweightConservatively("WHM", 1)
            else:
                self.adjustweight("WHM", 0)

    def piEtrigger(self, s):
        pIndex = s.indexString("P")
        O3Index = s.indexString("O3")
        if pIndex > -1 and O3Index > -1:
            if abs(pIndex - O3Index) > 1:
                ##print("pos",s.sentenceStr)
                self.adjustweight("PI", 1)

            elif ((pIndex + O3Index) == 1):
                #print("amb:",s.sentenceStr)
                self.adjustweightConservatively("PI", 0)

    def tmEtrigger(self, s):
        if "[+WA]" in s.sentenceStr:
            self.adjustweight("TM", 1)
        elif "O1" in s.sentenceList and "O2" in s.sentenceList and (
                abs(s.sentenceList.index("O1") - s.sentenceList.index("O2")) > 1):
            self.adjustweight("TM", 0)

    def VtoIEtrigger(self, s):

        # if self.grammar["HIP"]<0.5 and self.grammar["SP"]<0.5 and "Verb" in s.sentenceStr and "Not" in s.sentenceStr and 'Aux' not in s.sentenceStr and s.inflection=="DEC":
        #     Notindex = s.indexString("Not")
        #     #Neverindex= s.indexString("Never")
        #     if Notindex != 0 and (s.indexString("Verb") - Notindex) <= -1:
        #         ##print(s.indexString("Verb"))
        #         ##print( Notindex)
        #         #print("Not before:",s.sentenceStr)
        #         self.adjustweight("VtoI", 1)
        #         self.adjustweight("AH", 0)
        # elif self.grammar["HIP"]<0.5  and self.grammar["SP"]<0.5 and "Verb" in s.sentenceStr and "Never" in s.sentenceStr and 'Aux' not in s.sentenceStr and s.inflection=="DEC":
        #     Neverindex = s.indexString("Never")
        #     if Neverindex!= 0 and (s.indexString("Verb") - Neverindex) <= -1:
        #         #print("never before",s.sentenceStr)
        #         self.adjustweight("VtoI", 1)
        #         self.adjustweight("AH", 0)
        # elif self.grammar["HIP"] > 0.5  and self.grammar["SP"]<0.5 and "Verb" in s.sentenceStr and "Not" in s.sentenceStr and 'Aux' not in s.sentenceStr and s.inflection == "DEC":
        #     Notindex = s.indexString("Not")
        #     # Neverindex= s.indexString("Never")
        #     if Notindex != 0 and (s.indexString("Verb") - Notindex) >= 1:
        #         ##print(s.indexString("Verb"))
        #         ##print( Notindex)
        #         #print("Not before:", s.sentenceStr)
        #         self.adjustweight("VtoI", 1)
        #         self.adjustweight("AH", 0)
        # elif self.grammar["HIP"]>0.5  and self.grammar["SP"]<0.5 and "Verb" in s.sentenceStr and "Never" in s.sentenceStr and 'Aux' not in s.sentenceStr and s.inflection=="DEC":
        #     Neverindex = s.indexString("Never")
        #     if Neverindex!= 0 and (s.indexString("Verb") - Neverindex) >= 1:
        #         #print("never before",s.sentenceStr)
        #         self.adjustweight("VtoI", 1)
        #         self.adjustweight("AH", 0)
        if "Verb" in s.sentenceStr and "O1" in s.sentenceStr and 'Aux' not in s.sentenceStr and s.inflection == "DEC":
            o1index = s.indexString("O1")
            if o1index != 0 and abs(s.indexString("Verb") - o1index) > 1:
                # #print(s.indexString("Verb"))
                # #print(Notindex)
                ##print("01 v separate", s.sentenceStr)
                self.adjustweight("VtoI", 1)
                self.adjustweight("AH", 0)

            # no need to explicitly check inflection because only Q and DEC have AUX
        elif "Aux" in s.sentenceList:
            ##print(s.sentenceStr)
            self.adjustweightConservatively("VtoI", 0)

    def ItoCEtrigger(self, s):
        sp = self.grammar['SP']
        hip = self.grammar['HIP']
        hcp = self.grammar['HCP']

        if s.inflection == "DEC" and "S" in s.sentenceList and "Aux" in s.sentenceList:
            if sp < 0.5 and hip < 0.5:  # (Word orders 1, 5) subject and IP initial, aux to the right of Subject
                Sindex = s.sentenceList.index("S")
                if Sindex > 0 and s.sentenceList.index("Aux") == Sindex + 1:
                    self.adjustweight("ItoC", 0)

                    ##print(s.sentenceStr)

                elif hcp < 0.5 and (s.sentenceList.index("Aux") - s.sentenceList.index("S")) < 0:
                    # above code aux - s position less than 0 means aux precedes s
                    self.adjustweight("ItoC", 1)
                    self.adjustweight("AH", 0)

                elif hcp > 0.5 and s.sentenceList[-1] == "Aux":
                    self.adjustweight("ItoC", 1)
                    self.adjustweight("AH", 0)


            elif sp > 0.5 and hip > 0.5:  # (Word orders 2, 6) #subject and IP final, aux to the left of subject
                AuxIndex = s.sentenceList.index("Aux")
                if (AuxIndex > 0 and s.sentenceList.index("S") == AuxIndex + 1):
                    self.adjustweight("ItoC", 0)
                    ##print(s.sentenceStr)

                elif hcp > 0.5 and s.sentenceList[-1] == "Aux" and s.sentenceList.index("S") == (AuxIndex - 1):
                    self.adjustweight("ItoC", 1)
                    self.adjustweight("AH", 0)
                    #print("itoc1",s.sentenceStr)


                elif hcp < 0.5 and s.sentenceList.index("Aux") == 0:
                    self.adjustweight("ItoC", 1)
                    self.adjustweight("AH", 0)
                    #print("itoc1", s.sentenceStr)
                elif hcp < 0.5 and (s.sentenceList.index("Aux") < s.sentenceList.index("Verb")):
                    self.adjustweight("ItoC", 1)
                    self.adjustweight("AH", 0)
                    #print("itoc1", s.sentenceStr)



            elif sp > 0.5 and hip < 0.5 and hcp > 0.5 and "Verb" in s.sentenceList:  # subject and C initial, IP final, Aux immediately precedes verb
                if s.sentenceList.index("Verb") == s.sentenceList.index("Aux") + 1:
                    #print(s.sentenceStr)
                    self.adjustweight("ItoC", 0)
                elif "Not" in s.sentenceList and (
                        s.sentenceList.index("Verb") == s.sentenceList.index("Not") + 1 and s.sentenceList.index(
                        "Verb") == s.sentenceList.index("Aux") + 2):
                    #print(s.sentenceStr)
                    self.adjustweight("ItoC", 0)
                elif "Never" in s.sentenceList and (
                        s.sentenceList.index("Verb") == s.sentenceList.index("Never") + 1 and s.sentenceList.index(
                        "Verb") == s.sentenceList.index("Aux") + 2):
                    #print(s.sentenceStr)
                    self.adjustweight("ItoC", 0)
                else:
                    self.adjustweight("ItoC", 1)
                    #print("else:",s.sentenceStr)
                    # will experiment with aggressive rate
                    self.adjustweight("AH", 0)

            elif sp < 0.5 and hip > 0.5 and hcp < 0.5 and "Verb" in s.sentenceList:  # subject and C initial, IP final, Aux immediately precedes verb
                if s.sentenceList.index("Aux") == s.sentenceList.index("Verb") + 1:
                    self.adjustweight("ItoC", 0)
                elif "Not" in s.sentenceList and (
                        s.sentenceList.index("Aux") == s.sentenceList.index("Not") + 1 and s.sentenceList.index(
                        "Aux") == s.sentenceList.index("Verb") + 2):
                    self.adjustweight("ItoC", 0)
                elif "Never" in s.sentenceList and (
                        s.sentenceList.index("Aux") == s.sentenceList.index("Never") + 1 and s.sentenceList.index(
                        "Aux") == s.sentenceList.index("Verb") + 2):
                    self.adjustweight("ItoC", 0)
                else:
                    self.adjustweight("ItoC", 1)
                    self.adjustweight("AH", 0)
                    #print("itoc1", s.sentenceStr)
                    # will experiment with aggressive rate




            elif "Aux" in s.sentenceStr and "Verb" in s.sentenceList:  # check if aux and verb in sentence and something comes between them
                Vindex = s.sentenceList.index("Verb")
                Auxindex = s.sentenceList.index("Aux")
                indexlist = []  # tokens that would shed light if between
                if "S" in s.sentenceList:
                    Sindex = s.sentenceList.index("S")
                    indexlist.append(Sindex)

                if "O1" in s.sentenceList:
                    O1index = s.sentenceList.index("O1")
                    indexlist.append(O1index)

                if "O2" in s.sentenceList:
                    O2index = s.sentenceList.index("O2")
                    indexlist.append(O2index)

                if abs(Vindex - Auxindex) != 1:  # if verb and aux not adjacent
                    for idx in indexlist:
                        if (Vindex < idx < Auxindex) or (Vindex > idx > Auxindex):  # if item in index list between them
                            self.adjustweight("ItoC", 1)
                            self.adjustweight("AH", 0) # set toward 1
                            ##print("itoc1", s.sentenceStr)
                            break

        elif s.inflection == "DEC" and "Never" in s.sentenceStr and "Verb" in s.sentenceStr and "O1" in s.sentenceStr and (
                "Aux" not in s.sentenceStr):
            neverPos = s.indexString("Never")
            verbPos = s.indexString("Verb")
            O1Pos = s.indexString("O1")

            if (neverPos > -1 and verbPos == neverPos + 1 and O1Pos == verbPos + 1 and self.grammar["HIP"]<0.5 ) or (
                    O1Pos > 0 and verbPos == O1Pos + 1 and neverPos == verbPos + 1 and self.grammar["HIP"]>0.5):
                self.adjustweight("ItoC", 0)
                #print("o1 v",s.sentenceStr)

        # elif ((sp < 0.5 and hip > 0.5 and hcp > 0.5) or (sp > 0.5 and hip < 0.5 and hcp < 0.5))  and "Verb" in s.sentenceList and "Aux" not in s.sentenceList and "Never" in s.sentenceList:
        #     self.adjustweight("ItoC", 1 )
            # Following line outlines conservative trigger for +ItoC in SOVIC and CIVOS languages. These languages will always have an aux in consv trigger is evidence towards 1 because it is contrary to VPedge triggers
        elif ((sp > 0.5 and hcp < 0.5 and hip < 0.5) or (
                sp < 0.5 and hcp > 0.5 and hip > 0.5)) and "Never" in s.sentenceStr and "Aux" in s.sentenceStr and "Verb" in s.sentenceStr:
            self.adjustweightConservatively("ItoC", 1)


    def ahEtrigger(self, s):
        ##print(s.sentenceStr)
        if (s.inflection == "DEC" and self.grammar["ItoC"]<0.5) and (
                "Aux" not in s.sentenceStr and ("Never" in s.sentenceStr or "Not" in s.sentenceStr) and "Verb" in s.sentenceStr and "O1" in s.sentenceStr):
            neverPos = s.indexString("Never")
            verbPos = s.indexString("Verb")
            O1Pos = s.indexString("O1")
            notPos = s.indexString("Not")
            if (neverPos > -1 and verbPos == neverPos + 1 and O1Pos == verbPos + 1 and self.grammar["HIP"]<0.5) or (
                    O1Pos > -1 and verbPos == O1Pos + 1 and neverPos == verbPos + 1 and self.grammar["HIP"]>0.5):
                ##print("never verb 01",s.sentenceStr)
                self.adjustweight("AH", 1)
                self.adjustweight("VtoI", 0)

            if (notPos > -1 and verbPos == notPos + 1 and O1Pos == verbPos + 1 and self.grammar["HIP"]<0.5) or (
                    O1Pos > -1 and verbPos == O1Pos + 1 and notPos == verbPos + 1 and self.grammar["HIP"]>0.5):
                ##print("not verb 01",s.sentenceStr)
                self.adjustweight("AH", 1)
                self.adjustweight("VtoI", 0)

        elif "Aux" in s.sentenceStr:
            self.adjustweightConservatively("AH", 0)
            # if self.grammar["VtoI"] > 0.5: #If not affix hopping language, vtoi is either 0 or 1, but if evidence of vtoi towards 1 has alreadybeen observed, increase confidence 1VtoI given 0AH
            #   self.adjustweightConservatively("VtoI", 1)

    def QInvEtrigger(self, s):
        if s.inflection == "Q" and "ka" in s.sentenceStr:
            self.adjustweight("QInv", 0)
            self.adjustweight("ItoC", 0)

        elif s.inflection == "Q" and "ka" not in s.sentenceStr and "WH" not in s.sentenceStr:
            self.adjustweight("QInv", 1)

    #            self.adjustweightConservatively("ItoC", 1)

    def adjustweight(self, parameter, direction):
        self._adjustweight(parameter, direction, self.r)

    def adjustweightConservatively(self, parameter, direction):
        self._adjustweight(parameter, direction, self.conservativerate)

    def _adjustweight(self, parameter, direction, rate):
        if direction == 0:
            self.grammar[parameter] -= rate * self.grammar[parameter]
        elif direction == 1:
            self.grammar[parameter] += rate * (1 - self.grammar[parameter])


class NDChildModLRP(NDChild):
    def _adjustweight(self, parameter, direction, rate):
        pval = self.grammar[parameter]
        if pval >= 0.5:
            coef = 1 - pval
        else:
            coef = pval
        if direction == 0:
            self.grammar[parameter] -= rate * coef
        elif direction == 1:
            self.grammar[parameter] += rate * coef


class TriggerCacher:
    def __init__(self):
        self.current_trigger = None
        self.current_sentence = None

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
        for trigger in child.trigger_methods:
            self.current_trigger = self.trigger_name(trigger)
            self.current_sentence = s
            trigger(s)
        self.current_trigger = None
        self.current_sentence = None


class CachedChild(NDChild):
    """An implementation of NDChild where all triggers which are pure functions,
    (whose behavior depends solely on the input sentence, and not the state of
    the grammar) are cached once for every sentence in the domain and then
    simply looked up at runtime.

    """
    cacher = TriggerCacher()

    @classmethod
    def precompute_domain(cls, domain):
        for sentence in progress_bar(domain.sentences.values(),
                                     desc='precomputing triggers'):
            cls.precompute_sentence(sentence)

    @classmethod
    def precompute_sentence(cls, sentence):
        cls.cacher.consume_sentence(sentence)

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

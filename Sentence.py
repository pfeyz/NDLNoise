
# coding: utf-8

# In[ ]:

class Sentence(object):
    def __init__ (self, infoList):
        self.language = infoList[0]
        self.inflection = infoList[1]
        self.sentenceStr = infoList [2]
        self.sentenceList = infoList[2].split()
        self.struct = infoList[3]
        self.triggers = {}

        O1index = self.indexStringFull("O1")
        O2index = self.indexStringFull("O2")
        Pindex = self.indexStringFull("P")
        O3index = self.indexStringFull("O3")

        self.word_indexes = {
            'O3': self.indexStringFull("O3"),
            'P': self.indexStringFull("P"),
            'Not': self.indexStringFull("Not"),
            'O1': self.indexStringFull("O1"),
            'Never': self.indexStringFull("Never"),
            'Verb': self.indexStringFull("Verb")
        }

        self._outOblique = False
        if (O1index != -1 and O1index < O2index < Pindex and O3index == Pindex+1):
            self._outOblique = False
        elif (O3index != -1 and O3index < O2index < O1index and Pindex == O3index+1):
            self._outOblique = False
        elif (O1index != -1 and O2index != -1 and Pindex != -1 and O3index != -1):
            self._outOblique = True

    #indexString returns index of word in sentenceList if key string is contained in that word.
    #Returns -1 if key string is not in sentence
    def indexString(self,key):
        return self.word_indexes[key]

    def indexStringFull(self,key):
        for word in self.sentenceList:
            if key in word:
                return self.sentenceList.index(word)
        return -1

    #outOblique checks to see if something other than subject has been topicalized ie. moved out of canonical argument order
    #not checking for presence of Adv topicalized, maybe add later (this is sufficient but Adv could be informative for longitudinal study)
    def outOblique(self):
        return self._outOblique

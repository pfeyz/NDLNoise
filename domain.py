import re
import logging
from random import choice
from typing import Dict, List, NewType

from InstrumentedChild import InstrumentedNDChild
from Sentence import Sentence
from utils import progress_bar

logging.basicConfig(level=logging.INFO)

SentenceId = NewType('SentenceId', int)
GrammarId = NewType('GrammarId', int)

COLAG_FLAT_FILE_RE = re.compile(r"""
(?P<gramm>[01]+)\s
(?P<illoc>[A-Z]+)\s*\t\s*
(?P<sent>.*?)\s*\t\s*
(?P<struct>.*\))\s+
(?P<grammID>\d+)\s+
(?P<sentID>\d+)\s+
(?P<structID>\d+)\s*$
""", re.VERBOSE)


class ColagDomain:
    languages: Dict[GrammarId, List[SentenceId]]
    sentences: Dict[SentenceId, Sentence]

    def __init__(self):
        self.languages = {}
        self.sentences = {}

    def read_domain_file(self, domain_file, rate, conservativerate):
        """Populates the global DOMAINS, SENTIDS_IN_LANG and ALL_SENTENCES collections.

        """
        logging.info('generating languages')
        count = 0
        with open(domain_file, 'r') as fh:
            for line in progress_bar(fh, total=3081164):
                source = COLAG_FLAT_FILE_RE.match(line).groupdict()
                sent = Sentence([source['grammID'],
                                 source['illoc'],
                                 source['sent'],
                                 source['sentID']])
                grammar_id = int(sent.language)

                try:
                    self.languages[grammar_id].append(sent.sentID)
                except KeyError:
                    self.languages[grammar_id] = [sent.sentID]

                InstrumentedNDChild.precompute_sentence(sent, rate, conservativerate)

                self.sentences[sent.sentID] = sent
                count += 1
        logging.info('%s languages, %s sentence types, %s sentence tokens',
                     len(self.languages),
                     len(self.sentences),
                     count)

    def get_sentence_not_in_language(self, grammar_id: GrammarId):
        while True:
            s = choice(self.sentences)
            if s.sentID not in self.languages[grammar_id]:
                return s

    def get_sentence_in_language(self, grammar_id: GrammarId):
        sentence_id = choice(self.languages[grammar_id])
        return self.sentences[sentence_id]

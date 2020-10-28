import logging
import os.path
import pickle
import re
import shutil
import zipfile

import requests
from hashlib import md5
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


def download_file(url):
    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        with open(local_filename, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    return local_filename


def pickled_path(domain_file):
    """Returns the expected pickled path for the domain file, with the file's hash
    embedded in the filename."""
    return '{}-{}.pkl'.format(domain_file, hash_file(domain_file))


def hash_file(path):
    digest = md5()
    with open(path, 'rb') as fh:
        while True:
            data = fh.read(128*1024)
            if not data:
                break
            digest.update(data)
    return digest.hexdigest()


class ColagDomain:
    # maps from grammar ids -> list of sentence ids
    languages: Dict[GrammarId, List[SentenceId]]

    # maps from sentence ids -> sentence objects
    sentences: Dict[SentenceId, Sentence]

    def __init__(self):
        self.languages = {}
        self.sentences = {}

    def init_from_flatfile(self, rate, conservativerate):
        """Convenience function that downloads, unzips and reads the colag domain file,
        if necessary.

        """
        txt = 'COLAG_2011_flat.txt'
        zipped = 'COLAG_2011_flat.zip'
        if not os.path.exists(txt):
            if not os.path.exists(zipped):
                logging.info('downloading colag flatfile')
                download_file('http://www.colag.cs.hunter.cuny.edu/grammar/data/COLAG_2011_flat.zip')
            logging.info('unzipping colag flatfile')
            with zipfile.ZipFile(zipped, 'r') as zip_ref:
                zip_ref.extractall('.')
        self.read_domain_file(txt, rate, conservativerate)

    def read_domain_file(self, domain_file, rate, conservativerate):
        pickled = pickled_path(domain_file)
        if os.path.exists(pickled):
            logging.info('reading pickled colag domain from %s' % pickled)
            with open(pickled, 'rb') as fh:
                domain = pickle.load(fh)
                self.languages = domain.languages
                self.sentences = domain.sentences
                logging.info('pickled domain successfully read')
                return

        logging.info('generating languages')
        token_count = 0
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
                token_count += 1
        logging.info('%s languages, %s sentence types, %s sentence tokens',
                     len(self.languages),
                     len(self.sentences),
                     token_count)

        logging.info('writing pickled colag domain to %s' % pickled)
        with open(pickled, 'wb') as fh:
            pickle.dump(self, fh)

    def get_sentence_not_in_language(self, grammar_id: GrammarId):
        while True:
            s = choice(self.sentences)
            if s.sentID not in self.languages[grammar_id]:
                return s

    def get_sentence_in_language(self, grammar_id: GrammarId):
        sentence_id = choice(self.languages[grammar_id])
        return self.sentences[sentence_id]

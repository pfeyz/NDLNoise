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

from Sentence import Sentence
from utils import progress_bar

logging.basicConfig(level=logging.INFO)

SentenceId = NewType('SentenceId', int)
GrammarId = NewType('GrammarId', int)

# regex for matching a single line in the colag flat file
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
    """Downloads a file to disk and returns the resulting local filename"""
    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        with open(local_filename, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    return local_filename


# changing the salt will force the cached domain to be regenerated. this should
# be done when changes are made to the domain-generation code that should force
# re-running and re-caching.
SALT = b'j3k2f3'


def pickled_path(domain_file):
    """Returns the expected pickled path for the domain file, with the file's hash
    embedded in the filename. If the domain file ever changes, the hash will
    change, which will force recomputing the domain object from the flat file.

    """
    return '{}-{}.pkl'.format(domain_file, hash_file(domain_file, SALT))


def hash_file(path, salt=None):
    """ Returns the md5 hash of a `path` on disk """
    digest = md5()
    if salt is not None:
        digest.update(SALT)
    with open(path, 'rb') as fh:
        while True:
            data = fh.read(128*1024)
            if not data:
                break
            digest.update(data)
    return digest.hexdigest()


class ColagDomain:
    """ Represents the COLAG language domain."""

    # maps from grammar id -> list of sentence ids
    languages: Dict[GrammarId, List[SentenceId]]

    # maps from sentence id -> sentence objects
    sentences: Dict[SentenceId, Sentence]

    flatfile_url = 'http://www.colag.cs.hunter.cuny.edu/grammar/data/COLAG_2011_flat.zip'

    def __init__(self):
        """Reading the domainfile is deferred so that a single global colag
        object can be created at the beginning of the script, to be shared
        between processes. """
        self.languages = {}
        self.sentences = {}
        self.sentence_list = []

    def init_from_flatfile(self):
        """Convenience function that downloads, unzips and reads the colag domain file,
        if necessary.

        """
        txt = 'COLAG_2011_flat.txt'
        zipped = 'COLAG_2011_flat.zip'
        if not os.path.exists(txt):
            if not os.path.exists(zipped):
                logging.info('downloading colag flatfile')
                download_file(self.flatfile_url)
            logging.info('unzipping colag flatfile')
            with zipfile.ZipFile(zipped, 'r') as zip_ref:
                zip_ref.extractall('.')
        self.read_domain_flatfile(txt)

    def read_domain_flatfile(self, domain_file):
        """Populates ColagDomain object from sentences in colag flatfile
        `domain_file`. If the file has been read before and cached locally on
        disk as pickle, just reads and returns the cached object.

        """
        pickled = pickled_path(domain_file)
        if os.path.exists(pickled):
            logging.info('reading pickled colag domain from %s' % pickled)
            with open(pickled, 'rb') as fh:
                domain = pickle.load(fh)
                self.languages = domain.languages
                self.sentences = domain.sentences
                self.sentence_list = domain.sentence_list
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

                self.sentences[sent.sentID] = sent
                token_count += 1

        self.sentence_list = list(self.sentences.values())

        logging.info('%s languages, %s sentence types, %s sentence tokens',
                     len(self.languages),
                     len(self.sentences),
                     token_count)

        logging.info('writing pickled colag domain to %s' % pickled)
        with open(pickled, 'wb') as fh:
            pickle.dump(self, fh)

    def get_sentence_not_in_language(self, grammar_id: GrammarId):
        while True:
            s: Sentence = choice(self.sentence_list)
            if s.sentID not in self.languages[grammar_id]:
                return s

    def get_sentence_in_language(self, grammar_id: GrammarId):
        sentence_id = choice(self.languages[grammar_id])
        return self.sentences[sentence_id]

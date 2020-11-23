import glob
import gzip
import json
import random
import re

import pytest

from NDChild import NDChild
from main import DOMAIN, InstrumentedNDChild, progress_bar


def find_difference(g1, g2):
    diffs = {}
    for key in g1:
        if g1[key] != g2[key]:
            diffs[key] = g1[key], g2[key]
    return diffs


DOMAIN.init_from_flatfile()

for sent in progress_bar(DOMAIN.sentences.values(),
                         desc='precomputing triggers'):
    InstrumentedNDChild.precompute_sentence(sent)

runs = glob.glob('tests/run_data/*.gz')


@pytest.mark.parametrize('path', runs)
def test_drift_from_original(path):
    lang, rate, cons = re.search(r'lang(\d+):rate(\d+.\d+):cons(\d+.\d+)', path).groups()
    rate, cons = float(rate), float(cons)

    child = NDChild(rate, cons, lang)
    cached_child = InstrumentedNDChild(rate, cons, lang)

    with gzip.open(path) as fh:
        for line in fh:
            data = json.loads(line)
            s = DOMAIN.sentences[data['sentence_id']]
            expected = data['grammar']
            child.consumeSentence(s)
            cached_child.consumeSentence(s)
            assert child.grammar == expected
            assert child.grammar == cached_child.grammar


all_languages = list(DOMAIN.languages.keys())
languages = [random.choice(all_languages) for _ in range(10)]


@pytest.mark.parametrize('language', languages)
def test_ndchild_parity(language):
    """Compares the behavior of NDChild and InstrumentedNDChild to ensure identical
    behavior

    """
    child = NDChild(0.9, 0.005, 2253)
    cached_child = InstrumentedNDChild(0.9, 0.005, 2253)

    num_sents = int(50000)
    for i in range(num_sents):
        s = DOMAIN.get_sentence_in_language(grammar_id=language)
        child.pre = dict(child.grammar)
        cached_child.pre = dict(child.grammar)
        child.consumeSentence(s)
        cached_child.consumeSentence(s)
        assert child.grammar == cached_child.grammar

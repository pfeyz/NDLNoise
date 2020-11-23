import random

from NDChild import NDChild
from main import DOMAIN, InstrumentedNDChild, progress_bar

def test_ndchild_parity():
    """Compares the behavior of NDChild and InstrumentedNDChild to ensure identical
    behavior

    """
    DOMAIN.init_from_flatfile()

    for sent in progress_bar(DOMAIN.sentences.values(),
                             desc='precomputing triggers'):
        InstrumentedNDChild.precompute_sentence(sent)

    child = NDChild(0.9, 0.005, 2253)
    cached_child = InstrumentedNDChild(0.9, 0.005, 2253)

    def find_difference(g1, g2):
        diffs = {}
        for key in g1:
            if g1[key] != g2[key]:
                diffs[key] = g1[key], g2[key]
        return diffs

    num_sents = int(50000)
    for _ in range(10):
        language = random.choice(list(DOMAIN.languages.keys()))
        for i in progress_bar(range(num_sents), total=num_sents, desc=str(language)):
            s = DOMAIN.get_sentence_in_language(grammar_id=language)
            child.pre = dict(child.grammar)
            cached_child.pre = dict(child.grammar)
            child.consumeSentence(s)
            cached_child.consumeSentence(s)
            assert child.grammar == cached_child.grammar, (i, find_difference(child.grammar, cached_child.grammar))

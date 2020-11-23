import gzip
import json
import random

from OriginalNDChild import NDChild
from main import DOMAIN, progress_bar

DOMAIN.init_from_flatfile()


for _ in range(20):
    num_sents = int(random.random() * 100000)
    learningrate = round(random.random(), 2)
    conslearningrate = round(random.choice([1/10, 1/100, 1/1000]) * random.random(), 4)
    language = random.choice(list(DOMAIN.languages.keys()))

    child = NDChild(learningrate, conslearningrate, language)

    path = 'tests/run_data/lang{}:rate{}:cons{}.jsonl.gz'.format(
        language,
        learningrate,
        conslearningrate
    )

    with gzip.open(path, 'wt') as fh:
        for i in progress_bar(range(num_sents), total=num_sents, desc=str(language)):
            s = DOMAIN.get_sentence_in_language(grammar_id=language)
            child.consumeSentence(s)
            d = dict(child.grammar)
            d.pop('lang')
            fh.write(json.dumps(({'sentence_id': s.sentID, 'grammar': d})) + '\n')
        print(f'wrote {path}')

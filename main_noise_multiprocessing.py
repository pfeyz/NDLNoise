# coding: utf-8

import csv
import logging
import multiprocessing
from datetime import datetime
from random import choice, random
from typing import List

from NDChild import NDChild
from Sentence import Sentence


logging.basicConfig(level=logging.INFO)

DOMAINS = {}  # will contain mappings between language ids and (language, noise)
              # domain pairs


class LanguageNotFound(Exception):
    """Raised when a user attempts to read a language that does not exist in domain
    file.

    """
    pass


class Language:
    English = 611
    French = 584
    German = 2253
    Japanese = 3856


def create_language_domain(colag_domain, language: int):
    """Returns a tuple of (language_domain, noise_domain)

    `language_domain` contains all sentences in the language defined by
    language id `language`.

    `noise_domain` contains all sentences in COLAG_DOMAIN_FILE that are not in
    `language_domain`.

    """

    language_domain = []
    noise_domain = []
    for line in colag_domain:
        [gramm01, inflStr, sentenceStr, grammStr, sentID, struID] = line.split("\t")
        sentenceStr = sentenceStr[1:-1].rstrip()
        inflStr = inflStr[1:-1]
        s = Sentence([grammStr, inflStr, sentenceStr])
        if int(grammStr) == language:
            language_domain.append(s)
        else:
            noise_domain.append(s)
    if len(language_domain) == 0:
        raise LanguageNotFound('language %s not found in domain' % language)
    return language_domain, noise_domain


def init_domains(domain_file, languages: List[int]):
    """Populates the global DOMAINS dictionary with the languages listed in
    `languages`. This dict will be available to subprocesses.

    """
    logging.info('generating language and noise domains for %s', languages)
    with open(domain_file, 'r') as fh:
        colag_domain = list(fh)
        for lang in progress_bar(languages, total=len(languages),
                                 desc='initializing language domains'):
            DOMAINS[lang] = create_language_domain(colag_domain, lang)


def progress_bar(iterable, **kwargs):
    """ If tqdm is installed, Reports progress on the generation of `iterable` """
    try:
        import tqdm
    except ImportError:
        return iterable
    return tqdm.tqdm(iterable, **kwargs)


# TODO: this class probably doesn't need to exist
class TrialRunner:
    rate = 0.9
    conservativerate = 0.0005
    numberofsentences = 500000
    threshold = 0.001

    def __init__(self, language: int, noise: float):
        self.language = language
        self.noise_percentage = noise
        self.language_domain, self.noise_domain = DOMAINS[self.language]

    def get_parameters(self):
        return {
            'rate': self.rate,
            'conservativerate': self.conservativerate,
            'numberofsentences': self.numberofsentences,
            'threshold': self.threshold
        }

    def run_child(self):
        aChild = NDChild(self.rate, self.conservativerate, self.language)

        for i in range(self.numberofsentences):
            if random() < self.noise_percentage:
                s = choice(self.noise_domain)
            else:
                s = choice(self.language_domain)
            aChild.consumeSentence(s)

        return aChild


def run_trial(args):
    """ Runs a single echild simulation """
    logging.debug('running echild with %s', args)

    experiment = TrialRunner(args['lang'], args['noise'])
    then = datetime.now()
    child = experiment.run_child()
    now = datetime.now()

    logging.debug('echild learned %s', child.grammar)

    # TODO: define a more explicit SimulationResult class or something with
    # known fields.
    results = {'timestamp': now,
               'duration': now - then,
               **child.grammar,
               **args,
               **experiment.get_parameters()}

    return results


def run_simulations(colag_domain_file: str,
                    languages: List[int],
                    noise_levels: List[float],
                    num_children: int,
                    show_progress=True):
    """Runs echild simulations with given parameters across all available
    processors. Returns a generator that yields one result dictionary (as
    returned by run_trial) for each simulation run.

    """

    tasks = [
        {'lang': lang, 'noise': noise}  # this dict gets passed to
                                        # run_trial()
        for lang in languages
        for noise in noise_levels
        for _ in range(num_children)
    ]

    init_domains(colag_domain_file, languages)

    logging.info('starting simulation with languages=%s, noise_levels=%s, num_children=%s, params=%s',
                 languages, noise_levels, num_children, TrialRunner.get_parameters(TrialRunner))

    with multiprocessing.Pool() as p:
        results = p.imap_unordered(run_trial, tasks)
        if show_progress:
            results = progress_bar(results, total=len(tasks))
        yield from results


def main():
    results = run_simulations(
        colag_domain_file='orig4.txt',
        languages=[Language.English, Language.French, Language.German, Language.Japanese],
        noise_levels=[0, 0.05, 0.10, 0.25, 0.50],
        num_children=100)

    csv_columns = ["lang", "noise", "SP", "HIP", "HCP", "OPT", "NS",
                   "NT", "WHM", "PI", "TM", "VtoI", "ItoC", "AH",
                   "QInv", "threshold", "rate", "numberofsentences",
                   "conservativerate", "timestamp", "duration"]

    with open('output.csv', 'w') as fh:
        writer = csv.DictWriter(fh, fieldnames=csv_columns)
        writer.writeheader()
        for result in results:
            writer.writerow(result)


if __name__ == "__main__":
    main()

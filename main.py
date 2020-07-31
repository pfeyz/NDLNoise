# coding: utf-8

import argparse
import csv
import dataclasses
import logging
import multiprocessing
from datetime import datetime
from random import choice, random
from typing import List

from NDChild import NDChild
from Sentence import Sentence


logging.basicConfig(level=logging.INFO)


class ExperimentDefaults:
    """Defaults paramters for experiment."""
    rate = 0.9
    conservativerate = 0.0005
    numberofsentences = 500000
    threshold = 0.001
    numechildren = 100
    noise_levels = [0, 0.05, 0.10, 0.25, 0.50]


@dataclasses.dataclass
class SimulationParameters:
    """ The parameters for a single echild simulation """
    language: int
    noise: float
    rate: float
    conservativerate: float
    numberofsentences: int
    threshold: float


class Language:
    English = 611
    French = 584
    German = 2253
    Japanese = 3856


DOMAINS = {}  # will contain mappings between language ids and (language, noise)
              # domain pairs


class LanguageNotFound(Exception):
    """Raised when a user attempts to read a language that does not exist in domain
    file.

    """
    pass


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


def run_child(language, noise, rate, conservativerate, numberofsentences,
              threshold):

    aChild = NDChild(rate, conservativerate, language)
    language_domain, noise_domain = DOMAINS[language]

    for i in range(numberofsentences):
        if random() < noise:
            s = choice(noise_domain)
        else:
            s = choice(language_domain)
        aChild.consumeSentence(s)

    return aChild


def run_trial(params: SimulationParameters):
    """ Runs a single echild simulation and reports the results """
    logging.debug('running echild with %s', params)

    params = dataclasses.asdict(params)
    then = datetime.now()
    child = run_child(**params)
    now = datetime.now()

    child.grammar['language'] = child.grammar.pop('lang')
    results = {'timestamp': now,
               'duration': now - then,
               **child.grammar,
               **params}

    logging.debug('experiment results: %s', results)

    return results


def run_simulations(colag_domain_file: str,
                    num_echildren: int,
                    languages: List[int],
                    noise_levels: List[float],
                    numberofsentences: int,
                    rate: float,
                    conservativerate: float,
                    threshold: float,
                    num_procs: int,
                    show_progress=True):
    """Runs echild simulations with given parameters across all available
    processors. Returns a generator that yields one result dictionary (as
    returned by run_trial) for each simulation run.

    """

    tasks = (
        SimulationParameters(
            language=lang,
            noise=noise,
            rate=rate,
            numberofsentences=numberofsentences,
            conservativerate=conservativerate,
            threshold=threshold)

        for lang in languages
        for noise in noise_levels
        for _ in range(num_echildren)
    )

    num_tasks = num_echildren * len(languages) * len(noise_levels)

    init_domains(colag_domain_file, languages)

    with multiprocessing.Pool(num_procs) as p:
        results = p.imap_unordered(run_trial, tasks)
        if show_progress:
            results = progress_bar(results, total=num_tasks,
                                   desc="running simulations")
        yield from results


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--rate',
                        type=float,
                        default=ExperimentDefaults.rate)
    parser.add_argument('-c', '--cons-rate',
                        type=float,
                        default=ExperimentDefaults.conservativerate)
    parser.add_argument('-e', '--num-echildren',
                        type=int,
                        help='number of echildren per language/noise-level',
                        default=ExperimentDefaults.numechildren)
    parser.add_argument('-t', '--threshold',
                        type=float,
                        default=ExperimentDefaults.threshold)
    parser.add_argument('-s', '--num-sents',
                        type=int,
                        default=ExperimentDefaults.numberofsentences)
    parser.add_argument('-n', '--noise-levels', nargs="+", type=float,
                        default=ExperimentDefaults.noise_levels)
    parser.add_argument('-p', '--num-procs', type=int,
                        help='number of concurrent processes to run',
                        default=multiprocessing.cpu_count())
    parser.add_argument('-v', '--verbose', default=False,
                        action='store_const', const=True,
                        help='Output per-echild debugging info')
    return parser.parse_args()


def main():
    args = parse_arguments()

    logging.info('starting simulation with %s', args.__dict__)

    results = run_simulations(
        rate=args.rate,
        conservativerate=args.cons_rate,
        numberofsentences=args.num_sents,
        threshold=args.threshold,
        noise_levels=args.noise_levels,
        num_procs=args.num_procs,
        num_echildren=args.num_echildren,
        colag_domain_file='orig4.txt',
        languages=[Language.English, Language.French, Language.German, Language.Japanese],
    )

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    param_fields = [field.name for field in
                    dataclasses.fields(SimulationParameters)]

    csv_columns = [*param_fields, "SP", "HIP", "HCP", "OPT", "NS", "NT", "WHM",
                   "PI", "TM", "VtoI", "ItoC", "AH", "QInv", "timestamp",
                   "duration"]

    output_name = 'output_{timestamp}_rate:{rate}_consrate:{cons_rate}.csv'.format(
        timestamp=datetime.now().strftime('%F:%R'),
        rate=args.rate,
        cons_rate=args.cons_rate
    )

    logging.info('writing results to %s', output_name)

    with open(output_name, 'w') as fh:
        writer = csv.DictWriter(fh, fieldnames=csv_columns)
        writer.writeheader()
        for result in results:
            writer.writerow(result)


if __name__ == "__main__":
    main()

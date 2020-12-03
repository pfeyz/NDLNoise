# coding: utf-8

import argparse
import logging
import multiprocessing
import os.path
from datetime import datetime
from functools import partial
from random import random

from NDChild import NDChild, NDChildModLRP, cached_child
from datatypes import ExperimentParameters, TrialParameters, NDResult
from domain import ColagDomain
from output_handler import write_results
from utils import progress_bar

logging.basicConfig(level=logging.INFO)

DOMAIN = ColagDomain()


class ExperimentDefaults:
    """Defaults paramters for experiment."""
    rate = 0.9
    conservativerate = 0.0005
    numberofsentences = 500000
    numechildren = 100
    noise_levels = [0, 0.05, 0.10, 0.25, 0.50]


class Language:
    English = 611
    French = 584
    German = 2253
    Japanese = 3856


class LanguageNotFound(Exception):
    """Raised when a user attempts to read a language that does not exist in domain
    file.

    """
    pass


def run_traced_trial(params: TrialParameters, output_directory):
    """ Runs a single echild simulation and reports the results """

    logging.debug('running echild with %s', params)

    language = params.language
    noise_level = params.noise
    child = NDChild(params.rate, params.conservativerate, language)

    history = []

    then = datetime.now()

    sample_period = params.numberofsentences / 1000

    for i in range(params.numberofsentences):
        if random() < noise_level:
            s = DOMAIN.get_sentence_not_in_language(grammar_id=language)
        else:
            s = DOMAIN.get_sentence_in_language(grammar_id=language)
        child.consumeSentence(s)
        if i % sample_period == 0:
            history.append(dict(child.grammar))

    now = datetime.now()

    result = NDResult(
        trial_params=params,
        timestamp=now,
        duration=now - then,
        language=child.target_language,
        grammar=child.grammar)

    logging.debug('experiment result: %s', result)

    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams['figure.figsize'] = 15, 10

    df = pd.DataFrame(history)
    df = df + (np.arange(len(df.columns)) / 500)
    df.index = df.index * 1000
    ax = df.plot(title='lang={}, noise={}'.format(params.language, params.noise),
                 sharey=True,
                 subplots=True)
    # ax.set_xscale('log')
    plt.savefig(os.path.join(output_directory,
                             '{}-{}.png'.format(language, noise_level)))

    return result

def run_trial(params: TrialParameters):
    """ Runs a single echild simulation and reports the results """
    logging.debug('running echild with %s', params)

    language = params.language
    noise_level = params.noise
    child = NDChild(params.rate, params.conservativerate, language)

    then = datetime.now()

    for i in range(params.numberofsentences):
        if random() < noise_level:
            s = DOMAIN.get_sentence_not_in_language(grammar_id=language)
        else:
            s = DOMAIN.get_sentence_in_language(grammar_id=language)
        child.consumeSentence(s)

    now = datetime.now()

    result = NDResult(
        trial_params=params,
        timestamp=now,
        duration=now - then,
        language=child.target_language,
        grammar=child.grammar)

    logging.debug('experiment result: %s', result)

    return result


def run_simulations(params: ExperimentParameters, output_directory):
    """Runs echild simulations according to `params`.

    Returns a generator that yields one result dictionary (as returned by
    run_trial) for each simulation run.

    """

    trials = (
        TrialParameters(language=lang,
                        noise=noise,
                        rate=params.learningrate,
                        numberofsentences=params.num_sentences,
                        conservativerate=params.conservative_learningrate)
        for lang in params.languages
        for noise in params.noise_levels
        for _ in range(params.num_echildren)
    )

    # for reporting progress during the run
    num_trials = (params.num_echildren
                  * len(params.languages)
                  * len(params.noise_levels))

    DOMAIN.init_from_flatfile()

    # compute all "static" triggers once for each sentence in the domain and
    # store the cached value.
    NDChild.precompute_domain(DOMAIN)

    plot_simulations(params, output_directory)

    with multiprocessing.Pool(params.num_procs) as p:
        # run trials across processors (this doesn't actually start them
        # running- `results` is a generator. the actual computation is deferred
        # until somebody iterates through the generator object.
        results = p.imap_unordered(run_trial, trials)

        # report output
        results = progress_bar(results,
                               total=num_trials,
                               desc="running simulations")
        yield from results


def plot_simulations(params: ExperimentParameters, output_directory):

    subdir = os.path.join(output_directory, 'plots')
    os.mkdir(subdir)

    trials = (
        TrialParameters(language=lang,
                        noise=noise,
                        rate=params.learningrate,
                        numberofsentences=params.num_sentences,
                        conservativerate=params.conservative_learningrate)
        for lang in params.languages
        for noise in params.noise_levels
    )

    num_trials = len(params.languages) * len(params.noise_levels)

    with multiprocessing.Pool(params.num_procs) as p:
        # run trials across processors (this doesn't actually start them
        # running- `results` is a generator. the actual computation is deferred
        # until somebody iterates through the generator object.
        results = p.imap_unordered(partial(run_traced_trial,
                                           output_directory=subdir),
                                   trials)

        # report output
        results = progress_bar(results,
                               total=num_trials,
                               desc="plotting runs")

        list(results)


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
    parser.add_argument('-s', '--num-sents',
                        type=int,
                        default=ExperimentDefaults.numberofsentences)
    parser.add_argument('-n', '--noise-levels', nargs="+", type=float,
                        default=ExperimentDefaults.noise_levels)
    parser.add_argument('-l', '--languages', nargs="+", type=int,
                        default=[Language.English,
                                 Language.French,
                                 Language.German,
                                 Language.Japanese])
    parser.add_argument('-p', '--num-procs', type=int,
                        help='number of concurrent processes to run',
                        default=multiprocessing.cpu_count())
    parser.add_argument('-v', '--verbose', default=False,
                        action='store_const', const=True,
                        help='Output per-echild debugging info')
    parser.add_argument('--trace', default=False,
                        action='store_const', const=True,
                        help='Trace & plot per-parameter values over time')
    parser.add_argument('--mod-lrp', default=False,
                        action='store_const', const=True,
                        help='Use the modified-LRP learner')
    return parser.parse_args()


def main():
    global NDChild

    args = parse_arguments()

    if args.trace:
        args.num_echildren = 1

    logging.info('starting simulation with %s',
                 ' '.join('{}={}'.format(key, val)
                          for key, val in args.__dict__.items()))

    params = ExperimentParameters(
        learningrate=args.rate,
        conservative_learningrate=args.cons_rate,
        num_sentences=args.num_sents,
        noise_levels=args.noise_levels,
        num_procs=args.num_procs,
        num_echildren=args.num_echildren,
        languages=args.languages)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    output_directory = os.path.join(
        'simulation_output', '{timestamp}_R{rate}_C{cons_rate}{lrp}'.format(
            timestamp=datetime.now().strftime('%F:%R:%S'),
            lrp='_mod-lrp' if args.mod_lrp else '',
            rate=('%f' % params.learningrate).rstrip('0'),
            cons_rate=('%f' % params.conservative_learningrate).rstrip('0')))
    try:
        os.mkdir('simulation_output')
    except FileExistsError:
        pass

    os.mkdir(output_directory)

    results = run_simulations(params, output_directory)

    if args.mod_lrp:
        NDChild = cached_child(NDChildModLRP)
    else:
        NDChild = cached_child(NDChild)

    write_results(output_directory, args, results)


if __name__ == "__main__":
    main()

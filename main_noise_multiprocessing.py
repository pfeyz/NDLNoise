# coding: utf-8

import multiprocessing
import json
from random import choice, random

from NDChild import NDChild
from Sentence import Sentence

import logging

logging.basicConfig(level=logging.INFO)

COLAG_DOMAIN_FILE = 'orig4.txt'
COLAG_DOMAIN = list(open(COLAG_DOMAIN_FILE, 'r'))
DOMAINS = {}


class Language:
    English = "611"
    French = "584"
    German = "2253"
    Japanese = "3856"


def create_language_domain(language):
    language_domain = []
    noise_domain = []
    logging.info('generating language and noise domains for %s', language)
    for line in COLAG_DOMAIN:
        [gramm01, inflStr, sentenceStr, grammStr, sentID, struID] = line.split("\t")
        sentenceStr = sentenceStr[1:-1].rstrip()
        inflStr = inflStr[1:-1]
        s = Sentence([grammStr, inflStr, sentenceStr])
        if grammStr == language:
            language_domain.append(s)
        else:
            noise_domain.append(s)
    return language_domain, noise_domain


def init_domains(languages):
    for lang in languages:
        DOMAINS[lang] = create_language_domain(lang)


def csvOutput(File, run, lang, noise, child): #each line in csv should contain "lang/noiseamt/child#/final weights##
    outStr = str(run),",",str(lang),",",str(noise),",",child.grammar("SP"),",",child.grammar("HIP"),",",child.grammar("HCP"),",",child.grammar("OPT"),",",child.grammar("NS"),",",child.grammar("NT"),",",child.grammar("WHM"),",",child.grammar("PI"),",",child.grammar("TM"),",",child.grammar("VtoI"),",",child.grammar("ItoC"),",",child.grammar("AH"),",",child.grammar("QInv"),",","\n"
    File.write(outStr)


def progress_bar(iterable, **kwargs):
    """ If tqdm is installed, Reports progress on the generation of `iterable` """
    try:
        import tqdm
    except ImportError:
        return iterable
    return tqdm.tqdm(iterable, **kwargs)


class TrialRunner:
    rate = 0.9
    conservativerate = 0.0005
    numberofsentences = 500000
    threshold = 0.001

    def __init__(self, language, noise_percentage):
        self.language = str(language)
        self.noise_percentage = noise_percentage
        self.language_domain, self.noise_domain = DOMAINS[self.language]

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
    experiment = TrialRunner(args['language'], args['noise_percentage'])
    return {'child': experiment.run_child().grammar,
            'args': args}


def run_simulations(languages, noise_levels, num_children, show_progress=True):
    tasks = [
        {'language': lang, 'noise_percentage': noise}
        for lang in languages
        for noise in noise_levels
        for _ in range(num_children)
    ]

    init_domains(languages)

    logging.info('starting simulation with languages=%s, noise_levels=%s, num_children=%s',
                 languages, noise_levels, num_children)

    with multiprocessing.Pool() as p:
        results = p.imap_unordered(run_trial, tasks)
        if show_progress:
            results = progress_bar(results, total=len(tasks))
        yield from results


def main():
    results = run_simulations(
        languages=[Language.English, Language.French, Language.German, Language.Japanese],
        noise_levels=[0, 0.05, 0.10, 0.25, 0.50],
        num_children=100)

    with open('output.jsonl', 'w') as fh:
        for result in results:
            fh.write(json.dumps(result) + '\n')


if __name__ == "__main__":
    main()

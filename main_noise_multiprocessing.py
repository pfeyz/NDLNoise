# coding: utf-8

import multiprocessing
import json
from random import choice, random
import time

from NDChild import NDChild
from Sentence import Sentence

import datetime


def timed(fn):
    def wrapped(*args, **kwargs):
        then = datetime.datetime.now()
        val = fn(*args, **kwargs)
        delta = datetime.datetime.now() - then
        print(fn.__name__, delta)
        return val
    return wrapped

current_time = time.strftime("%m.%d.%y_%H:%M", time.localtime())
Out_Data_File = 'OUTDATANoise%s.csv' % current_time


def csvOutput(File, run, lang, noise, child): #each line in csv should contain "lang/noiseamt/child#/final weights##
    outStr = str(run),",",str(lang),",",str(noise),",",child.grammar("SP"),",",child.grammar("HIP"),",",child.grammar("HCP"),",",child.grammar("OPT"),",",child.grammar("NS"),",",child.grammar("NT"),",",child.grammar("WHM"),",",child.grammar("PI"),",",child.grammar("TM"),",",child.grammar("VtoI"),",",child.grammar("ItoC"),",",child.grammar("AH"),",",child.grammar("QInv"),",","\n"
    File.write(outStr)


def report_progress(iterable, **kwargs):
    """ If tqdm is installed, Reports progress on the generation of `iterable` """
    try:
        import tqdm
    except ImportError:
        return iterable
    return tqdm.tqdm(iterable, **kwargs)


COLAG_DOMAIN_FILE = 'orig4.txt'
COLAG_DOMAIN = list(open(COLAG_DOMAIN_FILE, 'r'))


class Language:
    English = "611"
    French = "584"
    German = "2253"
    Japanese = "3856"


class TrialRunner:
    rate = 0.9
    conservativerate = 0.0005
    numberofsentences = 500000
    threshold = 0.001

    def __init__(self, language, noise_percentage):
        self.language = str(language)
        self.noise_percentage = noise_percentage
        self.language_domain, self.noise_domain = self.create_language_domain()

    @timed
    def create_language_domain(self):
        language_domain = []
        noise_domain = []
        for line in COLAG_DOMAIN:
            [gramm01, inflStr, sentenceStr, grammStr, sentID, struID] = line.split("\t")
            #[grammStr, inflStr, sentenceStr] = line.split("\t")
            sentenceStr = sentenceStr[1:-1].rstrip()
            inflStr = inflStr[1:-1]
            s = Sentence([grammStr, inflStr, sentenceStr]) #constructor creates sentenceList
            if grammStr == self.language:
                language_domain.append(s)
            else:
                noise_domain.append(s)
        return language_domain, noise_domain

    def run_child(self):
        aChild = NDChild(self.rate, self.conservativerate, self.language)

        for i in range(self.numberofsentences):
            #with some probability choose from LD or NOISE
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


def run_experiment():
    languages = [Language.English, Language.French, Language.German, Language.Japanese]
    noise_levels = [0, 0.05, 0.10, 0.25, 0.50]

    # tasks here is a list of #language * #noise-levels * #echildren (100)
    tasks = [
        {'language': lang, 'noise_percentage': noise}
        for lang in languages
        for noise in noise_levels
        for _ in range(5)
    ]

    OUTDATA = open(Out_Data_File,"w") #open outdata writable file

    with multiprocessing.Pool() as p:
        # each task is procesed on the next available CPU and the results are
        # processed as they come in by this loop.
        with open('output.jsonl', 'w') as fh:
            for result in report_progress(p.imap_unordered(run_trial, tasks), total=len(tasks)):
                # result here is a dict with two keys: 'child' and NDChild, and 'args',
                # the task dictionary from the tasks list that contains 'language' and
                # 'noise' keys.
                fh.write(json.dumps(result) + '\n')


if __name__ == "__main__":
    run_experiment()

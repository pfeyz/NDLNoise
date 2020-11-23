This program was written by Katherine Howitt and Paul Feitzinger under the supervision of Prof. William Sakas
at Hunter College, Computer Science and the Graduate Center, Linguistics and Computer Science of the City University
of New York. It is written in Python 3.

sakas@hunter.cuny.edu

The program implements a learner that weights parameters on a continuum from 0 to 1, using human-like language e-triggers grounded in Chomsky's principles
and parameters framework. The learning model is one of first language acquisition, i.e., acquisition by a child of approximately 2 years of age.


-----

9/1/2020: The program is currently being maintained by Katherine Howitt

kghowitt@gmail.com

## Installation

You can install all required dependencies via

    $ pip install -r ./requirements.txt

## Running regression tests

After runing `pip install` above, pytest should be installed. Simply running:

    $ pytest

from the root directory of the repo will run all the regression tests to ensure
that the behavior of the learner has not drifted from the beginning of this
repository, and that the cached version of NDChild behaves identically to the
optimized one.

## Running the program
The program must be run with a Python interpreter that supports Python 3. It can run with:

    $ python main.py -h
    usage: main.py [-h] [-r RATE] [-c CONS_RATE] [-e NUM_ECHILDREN] [-s NUM_SENTS] [-n NOISE_LEVELS [NOISE_LEVELS ...]] [-l LANGUAGES [LANGUAGES ...]] [-p NUM_PROCS] [-v] [--trace]

    optional arguments:
    -h, --help            show this help message and exit
    -r RATE, --rate RATE
    -c CONS_RATE, --cons-rate CONS_RATE
    -e NUM_ECHILDREN, --num-echildren NUM_ECHILDREN
                            number of echildren per language/noise-level
    -s NUM_SENTS, --num-sents NUM_SENTS
    -n NOISE_LEVELS [NOISE_LEVELS ...], --noise-levels NOISE_LEVELS [NOISE_LEVELS ...]
    -l LANGUAGES [LANGUAGES ...], --languages LANGUAGES [LANGUAGES ...]
    -p NUM_PROCS, --num-procs NUM_PROCS
                            number of concurrent processes to run
    -v, --verbose         Output per-echild debugging info
    --trace               Trace & plot per-parameter values over time


The first time you run main.py, the program will download the colag domain file
from the colag website, then parse the file and cache the resulting data
structure.

Using the --trace option will cause the NUM_ECHILDREN argument to be ignore,
and set to 1. After each simulation a plot of the 13 parameters over time in a
single learner will pop up.

## Output

The output data will be written to
`simulation_output/<TIMESTAMP>_R<learning-rate>_C<conservative-rate>/` in three
files:

- `output.csv`: the per-echild final params
- `summary.xls`: contains the mean & standard deviation for each param, grouped
  by language and noise level.
- `plot.pdf`: a plot of the data in `summary.xls`

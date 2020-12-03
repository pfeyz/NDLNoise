import csv
import datetime
import logging
import os
import os.path
import re
from typing import List

import pandas as pd
import matplotlib.pyplot as plt

from datatypes import NDResult

languages = {
    611: 'english',
    584: 'french',
    2253: 'german',
    3856: 'japanese'
}


def summary_stats_output(results_csv, stats_output):
    df = pd.read_csv(results_csv)
    cols = [x for x in df.columns
            if x not in {'rate', 'conservativerate',
                         'numberofsentences', 'threshold'}]
    df[cols].groupby(['language', 'noise']).agg(['mean', 'var']).to_excel(
        stats_output)


def barplot_output(pathname, image_output):
    plt.rcParams['figure.figsize'] = 15, 25
    hyperparams = re.search(r'R(?P<rate>0.\d+)_C(?P<consrate>0.\d+)',
                            pathname).groupdict()
    df = pd.read_csv(pathname)
    params = [p for p in df.columns if p[0].isupper()]
    hyperparams['noiserates'] = list(df.noise.unique())
    fig, axs = plt.subplots(4, 1, constrained_layout=True)
    fig.suptitle("""Learning Rate: {rate}
    Conservative Rate: {consrate}
    Noise Levels: {noise_levels}
    Echildren per language & noise-level: {num_echildren}
    """.format(noise_levels=', '.join(str(x) for x in df.noise.unique()),
               num_echildren=','.join(
                   str(x)
                   for x in df.groupby(['language', 'noise']).size().unique()),
               **hyperparams),
                 fontsize=24)
    for language, ax in zip(df.language.unique(), axs):
        for noise_level, noise_amt in enumerate(df.noise.unique()):
            param_vals = (df[df.language.eq(language)
                             & df.noise.eq(noise_amt)][params]).values
            ax.boxplot(
                param_vals,
                positions=[n + (noise_level / 5) for n in range(len(params))],
                notch=False,
                widths=1 / 7.5)
        grammar_str = format(language, '013b')
        xlabels = [
            '{}={}'.format(name, grammar_str[num])
            for num, name in enumerate(params)
        ]
        ax.set_xticks(range(len(params)))
        ax.set_xticklabels(xlabels, fontsize=16)
        ax.set_yticks([0.5])
        ax.set_yticks([0, 1], minor=True)
        ax.grid()
        ax.grid(axis='y', which='minor', ls=':')
        ax.set_title('{} {}'.format(language, languages.get(language, '')))

    fig.savefig(image_output)


def write_results(output_directory, params, results: List[NDResult]):
    """Writes simulation results to csv, plots to a pdf and writes summary stats
    to an excel file."""

    csv_output = os.path.join(output_directory, 'output.csv')

    logging.info('writing results to %s', csv_output)

    with open(csv_output, 'w') as fh:
        writer = csv.DictWriter(fh, fieldnames=NDResult.csv_headers())
        writer.writeheader()
        for result in results:
            writer.writerow(result.as_csv_row())

    plot_output = os.path.join(output_directory, 'plot.pdf')
    stats_output = os.path.join(output_directory, 'summary.xls')

    logging.info('writing summary stats to %s', stats_output)
    summary_stats_output(csv_output, stats_output)

    logging.info('plotting results to %s', plot_output)
    barplot_output(csv_output, plot_output)

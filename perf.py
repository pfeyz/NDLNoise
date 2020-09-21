import cProfile
import pstats
from pstats import SortKey

from main import main

cProfile.run('main()', 'main.stats')
p = pstats.Stats('main.stats')
p.strip_dirs()
p.sort_stats(SortKey.CUMULATIVE).print_stats(10)
p.sort_stats(SortKey.TIME).print_stats(10)

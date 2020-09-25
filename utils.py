
def progress_bar(iterable, **kwargs):
    """ If tqdm is installed, Reports progress on the generation of `iterable` """
    try:
        import tqdm
    except ImportError:
        return iterable
    return tqdm.tqdm(iterable, **kwargs)

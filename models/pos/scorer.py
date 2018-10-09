"""
Utils and wrappers for scoring taggers.
"""
from models.common.utils import ud_scores

def score(system_conllu_file, gold_conllu_file, verbose=True):
    """ Wrapper for tagger scorer. """
    evaluation = ud_scores(gold_conllu_file, system_conllu_file)
    el = evaluation['AllTags']
    p = el.precision
    r = el.recall
    f = el.f1
    if verbose:
        scores = [evaluation[k].f1 * 100 for k in ['UPOS', 'XPOS', 'UFeats', 'AllTags']]
        print("UPOS\tXPOS\tUFeats\tAllTags")
        print("{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}".format(*scores))
    #print(evaluation['UPOS'].f1 * 100, evaluation['XPOS'].f1 * 100, evaluation['UFeats'].f1 * 100, evaluation['AllTags'].f1 * 100)
    return p, r, f


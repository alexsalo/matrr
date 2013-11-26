#-*- coding:utf-8 - *-
# http://aimotion.blogspot.com/2013/01/machine-learning-and-data-mining.html
import json
import os
import numpy
from matrr.models import CohortBout, LIGHTS_ON, LIGHTS_OUT

def createC1(dataset):
    """Create a list of candidate item sets of size one."""
    c1 = []
    for transaction in dataset:
        for item in transaction:
            if not [item] in c1:
                c1.append([item])
    c1.sort()
    #frozenset because it will be a ket of a dictionary.
    return map(frozenset, c1)

def scanD(dataset, candidates, min_support):
    """Returns all candidates that meets a minimum support level"""
    sscnt = {}
    for tid in dataset:
        for can in candidates:
            if can.issubset(tid):
                sscnt.setdefault(can, 0)
                sscnt[can] += 1

    num_items = float(len(dataset))
    retlist = []
    support_data = {}
    for key in sscnt:
        support = sscnt[key] / num_items
        if support >= min_support:
            retlist.insert(0, key)
        support_data[key] = support
    return retlist, support_data

def aprioriGen(freq_sets, k):
    """Generate the joint transactions from candidate sets"""
    retList = []
    lenLk = len(freq_sets)
    for i in range(lenLk):
        for j in range(i + 1, lenLk):
            L1 = list(freq_sets[i])[:k - 2]
            L2 = list(freq_sets[j])[:k - 2]
            L1.sort()
            L2.sort()
            if L1 == L2:
                retList.append(freq_sets[i] | freq_sets[j])
    return retList


def apriori(dataset, minsupport=0.5):
    """Generate a list of candidate item sets"""
    C1 = createC1(dataset)
    D = map(set, dataset)
    L1, support_data = scanD(D, C1, minsupport)
    L = [L1]
    k = 2
    while (len(L[k - 2]) > 0):
        Ck = aprioriGen(L[k - 2], k)
        Lk, supK = scanD(D, Ck, minsupport)
        support_data.update(supK)
        L.append(Lk)
        k += 1

    return L, support_data


def generateRules(L, support_data, min_confidence=0.7):
    """Create the association rules
    L: list of frequent item sets
    support_data: support data for those itemsets
    min_confidence: minimum confidence threshold
    """
    def calc_confidence(freqSet, H, support_data, rules, min_confidence=0.7):
        "Evaluate the rule generated"
        pruned_H = []
        for conseq in H:
            conf = support_data[freqSet] / support_data[freqSet - conseq]
            if conf >= min_confidence:
#				print freqSet - conseq, '--->', conseq, 'conf:', conf
                rules.append((freqSet - conseq, conseq, conf))
                pruned_H.append(conseq)
        return pruned_H

    def rules_from_conseq(freqSet, H, support_data, rules, min_confidence=0.7):
        """Generate a set of candidate rules"""
        m = len(H[0])
        if (len(freqSet) > (m + 1)):
            Hmp1 = aprioriGen(H, m + 1)
            Hmp1 = calc_confidence(freqSet, Hmp1,  support_data, rules, min_confidence)
            if len(Hmp1) > 1:
                rules_from_conseq(freqSet, Hmp1, support_data, rules, min_confidence)

    rules = []
    for i in range(1, len(L)):
        for freqSet in L[i]:
            H1 = [frozenset([item]) for item in freqSet]
#			print "freqSet", freqSet, 'H1', H1
            if (i > 1):
                rules_from_conseq(freqSet, H1, support_data, rules, min_confidence)
            else:
                calc_confidence(freqSet, H1, support_data, rules, min_confidence)
    return rules

def confederate_groups(cohort_pk, minutes, load_dataset, min_confidence=0, serializable=False):
    supports = dict()
    for _support in numpy.arange(.05, .96, .05):
        data = load_dataset(cohort_pk, minutes=minutes)
        l, sd = apriori(data, minsupport=_support)
        rules = generateRules(l, sd, min_confidence)
        supports[_support] = rules
    if serializable:
        supports = recreate_serializable_apriori_output(supports)
    return supports

def recreate_serializable_apriori_output(orig):
    new_dict = dict()
    for support, occurrences in orig.iteritems():
        new_occ = list()
        for cause, effect, confidence in occurrences:
            cause = tuple(cause)
            effect = tuple(effect)
            new_occ.append( (cause, effect, confidence) )
        new_dict[float(support)] = new_occ
    return new_dict

# ---- end of library/algorithm functions.


def get_all_confederate_groups(cohort_pk, minutes, min_confidence=0, dir_path='matrr/utils/DATA/apriori/'):
    def _fetch_all_CBT_monkey_groups(cohort_pk, minutes=0):
        cbts = CohortBout.objects.filter(cohort=cohort_pk, cbt_gap_definition=minutes*60)
        bout_groups = list()
        for cbt in cbts:
            monkeys = cbt.edr_set.all().values_list('ebt__mtd__monkey', flat=True).distinct()
            bout_groups.append(set(monkeys))
        return bout_groups

    file_name = "%d-%d-%.3f.json" % (cohort_pk, minutes, min_confidence)
    try:
        f = open(os.path.join(dir_path, file_name), 'r')
    except IOError:
        # pretty sure this will throw another IOException if dir_path doesn't exist
        f = open(os.path.join(dir_path, file_name), 'w')
    else:
        s = f.read()
        f.close()
        d = json.loads(s)
        return d

    supports = confederate_groups(cohort_pk, minutes, _fetch_all_CBT_monkey_groups, min_confidence=min_confidence, serializable=True)
    s = json.dumps(supports)
    f.write(s)
    f.close()
    return supports

def get_nighttime_confederate_groups(cohort_pk, minutes, min_confidence=0, dir_path='matrr/utils/DATA/apriori/'):
    def _fetch_nighttime_CBT_monkey_groups(cohort_pk, minutes=0):
        cbts = CohortBout.objects.filter(cohort=cohort_pk, cbt_gap_definition=minutes*60)
        cbts = cbts.filter(cbt_start_time__gte=LIGHTS_OUT).filter(cbt_start_time__lt=LIGHTS_ON)
        bout_groups = list()
        for cbt in cbts:
            monkeys = cbt.edr_set.all().values_list('ebt__mtd__monkey', flat=True).distinct()
            bout_groups.append(set(monkeys))
        return bout_groups

    file_name = "%d-%d-%.3f-nighttime.json" % (cohort_pk, minutes, min_confidence)
    try:
        f = open(os.path.join(dir_path, file_name), 'r')
    except IOError:
        # This will throw another IOException if dir_path doesn't exist
        f = open(os.path.join(dir_path, file_name), 'w')
    else:
        s = f.read()
        f.close()
        d = json.loads(s)
        return d
    supports = confederate_groups(cohort_pk, minutes, _fetch_nighttime_CBT_monkey_groups, min_confidence=min_confidence, serializable=True)
    s = json.dumps(supports)
    f.write(s)
    f.close()
    return supports



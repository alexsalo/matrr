"""
These functions are designed to be called generically to perform a specialized operation on a generalized input.

Alone, these functions are close to useless.  however, with the the general plotting method for which they are designed
they can be quite useful, especially for reducing/eliminating redundant code.

"""
__author__ = 'developer'
from matrr.models import NecropsySummary


def etoh_intake(queryset):
	return queryset.exclude(mtd_etoh_intake=None).values_list('mtd_etoh_intake')

def total_pellets(queryset):
	return queryset.exclude(mtd_total_pellets=None).values_list('mtd_total_pellets')

def veh_intake(queryset):
	return queryset.exclude(mtd_veh_intake=None).values_list('mtd_veh_intake')

def mtd_weight(queryset):
	return queryset.exclude(mtd_weight=None).values_list('mtd_weight')

def necropsy_summary_avg_22hr_g_per_kg(queryset):
	"""
	This method, used by necropsy graphs, will collect 12 month and 6 month average g/kg etoh intake for the [queryset]

	Args:
	queryset is expected to be a queryset of monkeys

	return:
	tuple, ( list of 6 month averages, list of 12 month averages, list of monkey pk labels )
	"""
	summaries = []
	raw_labels = []
	for mky in queryset.order_by("necropsy_summary__ncm_22hr_12mo_avg_g_per_kg", "necropsy_summary__ncm_22hr_6mo_avg_g_per_kg"):
		try:
			summaries.append(mky.necropsy_summary)
		except NecropsySummary.DoesNotExist:
			continue
		raw_labels.append(str(mky.pk))
	return [summary.ncm_22hr_6mo_avg_g_per_kg for summary in summaries], [summary.ncm_22hr_12mo_avg_g_per_kg for summary in summaries], raw_labels

def necropsy_summary_etoh_4pct(queryset):
	"""
	This method, used by necropsy graphs, will collect 22hr and lifetime etoh intake (in ml) for the [queryset]

	Args:
	queryset is expected to be a queryset of monkeys

	return:
	tuple, ( list of open access total intakes, list of lifetime total intakes, list of monkey pk labels )
	"""
	summaries = []
	raw_labels = []
	for mky in queryset.order_by("necropsy_summary__ncm_etoh_4pct_lifetime", "necropsy_summary__ncm_etoh_4pct_22hr"):
		try:
			summaries.append(mky.necropsy_summary)
		except NecropsySummary.DoesNotExist:
			continue
		raw_labels.append(str(mky.pk))
	return [summary.ncm_etoh_4pct_22hr for summary in summaries], [summary.ncm_etoh_4pct_lifetime for summary in summaries], raw_labels

def necropsy_summary_sum_g_per_kg(queryset):
	"""
	This method, used by necropsy graphs, will collect 22hr and lifetime etoh intake (in g/kg) for the [queryset]

	Args:
	queryset is expected to be a queryset of monkeys

	return:
	tuple, ( list of open access total intakes, list of lifetime total intakes, list of monkey pk labels )
	"""
	summaries = []
	raw_labels = []
	for mky in queryset.order_by("necropsy_summary__ncm_sum_g_per_kg_22hr", "necropsy_summary__ncm_sum_g_per_kg_lifetime"):
		try:
			summaries.append(mky.necropsy_summary)
		except NecropsySummary.DoesNotExist:
			continue
		raw_labels.append(str(mky.pk))
	return [summary.ncm_sum_g_per_kg_22hr for summary in summaries], [summary.ncm_sum_g_per_kg_lifetime for summary in summaries], raw_labels

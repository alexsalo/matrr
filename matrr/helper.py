import StringIO, random, numpy, pylab, time
from django.template import loader, Context
from ho import pisa
import networkx as nx
from utils import plotting_beta

class CytoVisualStyle():
#	family_graph = None
	family_tree = None

	global_vs = {'backgroundColor': "#fff"}
	nodes_vs = {'shape': 'Diamond', 'size': 50, 'color': '#999', 'borderColor': 'orange', 'borderWidth': 5}
	edges_vs = {'color': "blue", 'width': 3}

	def __init__(self, family_tree):
		self.family_tree = family_tree

	def continuous_node_colors(self, attr_name, min_value='#000000', max_value='#ffffff'):
		self.nodes_vs['color'] = {'continuousMapper': {'attrName': attr_name, 'minValue': min_value, 'maxValue': max_value}}

	def discrete_node_shapes(self, shape_method=None):
		def default_shape(node):
			return 'diamond'

		get_shape = shape_method if shape_method else default_shape

		entries = list()
		for node in self.family_tree.family_graph.nodes(data=True):
			# node == ( node_id, {node data dictionary} )
			entries.append({'attrValue': node[0], 'value': get_shape(node)})

		self.nodes_vs['shape'] = {'discreteMapper': {'attrName': "id", 'entries': entries, }}

	def discrete_node_colors(self, color_method=None):
		def default_color(node):
			color = 'orange'
			if node[0] == self.family_tree.me.monkey.pk:
				color = 'white'
			return color

		get_color = color_method if color_method else default_color

		entries = list()
		for node in self.family_tree.family_graph.nodes(data=True):
			# node == ( node_id, {node data dictionary} )
			entries.append({'attrValue': node[0], 'value': get_color(node)})
		self.nodes_vs['color'] = {'discreteMapper': {'attrName': "id", 'entries': entries}}

	def discrete_node_borderColors(self, color_method=None):
		def default_color(node):
			return 'purple'

		get_color = color_method if color_method else default_color

		entries = list()
		for node in self.family_tree.family_graph.nodes(data=True):
			# node == ( node_id, {node data dictionary} )
			entries.append({'attrValue': node[0], 'value': get_color(node)})
		self.nodes_vs['borderColor'] = {'discreteMapper': {'attrName': "id", 'entries': entries}}

	def discrete_node_borderWidth(self, width_method=None):
		def default_width(node):
			return node[1]['borderWidth_input'] / 100

		get_color = width_method if width_method else default_width

		entries = list()
		for node in self.family_tree.family_graph.nodes(data=True):
			# node == ( node_id, {node data dictionary} )
			entries.append({'attrValue': node[0], 'value': get_color(node)})
		self.nodes_vs['borderWidth'] = {'discreteMapper': {'attrName': "id", 'entries': entries}}

	def passthru_node_borderColors(self, attr_name='borderColor_color'):
		self.nodes_vs['borderColor'] = {'passthroughMapper': {'attrName': attr_name}}

	def continuous_edge_curvature(self, attr_name, min_value='1', max_value='90'):
		self.edges_vs['curvature'] = {'continuousMapper': {'attrName': attr_name, 'minValue': min_value, 'maxValue': max_value}}

	def passthru_edge_colors(self, attr_name='edge_color'):
		self.edges_vs['color'] = {'passthroughMapper': {'attrName': attr_name}}

	def passthru_edge_width(self, attr_name='edge_width'):
		self.edges_vs['width'] = {'passthroughMapper': {'attrName': attr_name}}

	def get_visual_style(self):
		""" returns dict() of visual cytoscapeweb style, http://cytoscapeweb.cytoscape.org/documentation/visual_style """
		vs_dict = dict()
		vs_dict['global'] = self.global_vs
		vs_dict['nodes'] = self.nodes_vs
		vs_dict['edges'] = self.edges_vs
		return vs_dict


class FamilyTree(object):
	family_graph = None
	me = None
	depth = None
	visual_style = None

	def __init__(self, family_node, graph=None, depth=3, visual_style=None):
		from matrr.models import FamilyNode
		if isinstance(family_node, FamilyNode):
			self.me = family_node
		else:
			raise Exception("family_node is not an instance of matrr.models.FamilyNode")
		self.family_graph = graph if graph else nx.Graph()
		self.depth = depth

		self.plant_tree()
		self.visual_style = visual_style if visual_style else CytoVisualStyle(self)

	def dump_graphml(self):
		return "".join(nx.generate_graphml(self.family_graph))

	def plant_tree(self):
		from matrr.models import FamilyRelationship
		self._add_family_node(self.me)
		self._add_family_node(self.me.sire)
		self._add_family_node(self.me.dam)
		mydad = FamilyRelationship.objects.get(me=self.me, relative=self.me.sire)
		self._add_family_edge(self.me, self.me.sire, relation=mydad)
		mymom = FamilyRelationship.objects.get(me=self.me, relative=self.me.dam)
		self._add_family_edge(self.me, self.me.dam, relation=mymom)
		self.__grow_tree(self.me.sire, 1)
		self.__grow_tree(self.me.dam, 1)
		print 'Finished'

	def __grow_tree(self, node, current_depth):
		if current_depth < self.depth:
			related_nodes = list()
			for relation in node.my_relations.all():
				self._add_family_node(relation.relative)
				self._add_family_edge(relation.me, relation.relative, relation=relation) # relation.me == node
				related_nodes.append(relation.relative)
			for relative in related_nodes:
				self.__grow_tree(relative, current_depth + 1)
		else:
			print "Max depth reached"


	def _construct_node_data(self, node, data=None):
		#  IMPORTANT NOTE
		# Data put in here _will_ be visible in the GraphML, and in turn the web page's source code
		data = data if data else dict()
		data['label'] = node.monkey.pk
		return data

	def _construct_edge_data(self, source, target, data=None, relation=None):
		#  IMPORTANT NOTE
		# Data put in here _will_ be visible in the GraphML, and in turn the web page's source code
		data = data if data else dict()
		data['label'] = "%d->%d" % (source.monkey.pk, target.monkey.pk)
		return data

	def _add_family_node(self, node):
		self.family_graph.add_node(node.monkey.pk, **self._construct_node_data(node))

	def _add_family_edge(self, source, target, relation=None):
		self.family_graph.add_edge(source.monkey.pk, target.monkey.pk, **self._construct_edge_data(source, target, relation=relation))


class ExampleFamilyTree(FamilyTree):
	def _construct_node_data(self, node, data=None):
		colors = {0: 'purple', 1: 'yellow', 2: 'green'}

		def border_color_calc(node):
			return colors[random.randint(0, 2)]

		data = super(ExampleFamilyTree, self)._construct_node_data(node, data)
		data['shape_input'] = node.monkey.mky_gender # continuousMapper
		data['color_input'] = random.random() # continuousMapper
		data['borderColor_color'] = border_color_calc(node) # passthruMapper
		data['borderWidth_input'] = random.randint(400, 1000) # discreteMapper
		return data

	def _construct_edge_data(self, source, target, data=None, relation=None):
		data = super(ExampleFamilyTree, self)._construct_edge_data(source, target, data, relation)
		data['edge_color'] = 'black' if relation.fmr_type == 'P' else '#ccc' # passthruMapper
		data['edge_width'] = random.randint(4, 12) # passthruMapper
		return data


def family_tree():
	import settings
	from matrr.models import Monkey, Cohort, Institution, FamilyNode, FamilyRelationship


	if not settings.PRODUCTION:
		import random

		for monkey in Monkey.objects.all():
			FamilyNode.objects.get_or_create(monkey=monkey)

		cohort = Cohort.objects.get_or_create(institution=Institution.objects.all()[0], coh_cohort_name='bogus cohort')[0]
		for monkey in Monkey.objects.all():
			fmn = FamilyNode.objects.get_or_create(monkey=monkey)[0]

		monkeys = Monkey.objects.all()[:5]
		female_monkeys = Monkey.objects.filter(mky_gender='F').exclude(pk__in=monkeys)
		male_monkeys = Monkey.objects.filter(mky_gender='M', cohort=3, mky_drinking=True).exclude(pk__in=monkeys)
		for monkey in monkeys:
			index = random.randint(0, min(female_monkeys.count() - 1, male_monkeys.count() - 1))
			monkey.genealogy.sire = male_monkeys[index].genealogy
			monkey.genealogy.dam = female_monkeys[index].genealogy
			monkey.genealogy.save()
			monkey.genealogy.create_parent_relationships()

		fmns = FamilyNode.objects.filter(monkey__in=monkeys)
		parent_pks = set()
		for fmn in fmns:
			parent_pks.add(fmn.sire.monkey.pk)
			parent_pks.add(fmn.dam.monkey.pk)

		parents = Monkey.objects.filter(pk__in=parent_pks)
		female_monkeys = Monkey.objects.exclude(pk__in=parents).exclude(pk__in=monkeys).filter(mky_gender='F', cohort=11)
		male_monkeys = Monkey.objects.exclude(pk__in=parents).exclude(pk__in=monkeys).filter(mky_gender='M', cohort=5)
		for monkey in parents:
			index = random.randint(0, min(female_monkeys.count() - 1, male_monkeys.count() - 1))
			monkey.genealogy.sire = male_monkeys[index].genealogy
			monkey.genealogy.dam = female_monkeys[index].genealogy

			monkey.genealogy.save()
			monkey.genealogy.create_parent_relationships()


		# test
		gp_fmns = FamilyNode.objects.filter(monkey__in=parents)
		gparent_pks = set()
		for fmn in fmns:
			gparent_pks.add(fmn.sire.monkey.pk)
			gparent_pks.add(fmn.dam.monkey.pk)

		for rship in FamilyRelationship.objects.all():
			coeff = random.random() * .5
			rship.fmr_coeff = coeff
			rship.save()
			rev = rship.reverse()
			rev.fmr_coeff = coeff
			rev.save()

	else:
		print "this shit creates a publicly visible bogus cohort.  dont use this."


def export_template_to_pdf(template, context={}, outfile=None, return_pisaDocument=False):
	t = loader.get_template(template)
	c = Context(context)
	r = t.render(c)

	result = outfile if outfile else StringIO.StringIO()
	pdf = pisa.pisaDocument(StringIO.StringIO(r.encode("UTF-8")), dest=result)

	if not pdf.err:
		if return_pisaDocument:
			return pdf
		else:
			return result
	else:
		raise Exception(pdf.err)


def convex_hull(points, graphic=False, smidgen=0.0075):
	'''Calculate subset of points that make a convex hull around points

Recursively eliminates points that lie inside two neighbouring points until only convex hull is remaining.

:Parameters:
	points : ndarray (2 x m)
		array of points for which to find hull
	graphic : bool
		use pylab to show progress?
	smidgen : float
		offset for graphic number labels - useful values depend on your data range

:Returns:
	hull_points : ndarray (2 x n)
		convex hull surrounding points
	'''
	def _angle_to_point(point, centre):
		'''calculate angle in 2-D between points and x axis'''
		delta = point - centre
		res = numpy.arctan(delta[1] / delta[0])
		if delta[0] < 0:
			res += numpy.pi
		return res
	def _draw_triangle(p1, p2, p3, **kwargs):
		tmp = numpy.vstack((p1, p2, p3))
		x, y = [x[0] for x in zip(tmp.transpose())]
		pylab.fill(x, y, **kwargs)
		#time.sleep(0.2)
	def area_of_triangle(p1, p2, p3):
		'''calculate area of any triangle given co-ordinates of the corners'''
		return numpy.linalg.norm(numpy.cross((p2 - p1), (p3 - p1), axis=0)) / 2.


	if graphic:
		pylab.clf()
		pylab.plot(points[0], points[1], 'ro')
	n_pts = points.shape[1]
#	assert(n_pts > 5)
	centre = points.mean(1)
	if graphic: pylab.plot((centre[0],), (centre[1],), 'bo')
	angles = numpy.apply_along_axis(_angle_to_point, 0, points, centre)
	pts_ord = points[:, angles.argsort()]
	if graphic:
		for i in xrange(n_pts):
			pylab.text(pts_ord[0, i] + smidgen, pts_ord[1, i] + smidgen, '%d' % i)
	pts = [x[0] for x in zip(pts_ord.transpose())]
	prev_pts = len(pts) + 1
	k = 0
	while prev_pts > n_pts:
		prev_pts = n_pts
		n_pts = len(pts)
		if graphic: pylab.gca().patches = []
		i = -2
		while i < (n_pts - 2):
			Aij = area_of_triangle(centre, pts[i], pts[(i + 1) % n_pts])
			Ajk = area_of_triangle(centre, pts[(i + 1) % n_pts],\
								   pts[(i + 2) % n_pts])
			Aik = area_of_triangle(centre, pts[i], pts[(i + 2) % n_pts])
			if graphic:
				_draw_triangle(centre, pts[i], pts[(i + 1) % n_pts],\
							   facecolor='blue', alpha=0.2)
				_draw_triangle(centre, pts[(i + 1) % n_pts],\
							   pts[(i + 2) % n_pts],\
							   facecolor='green', alpha=0.2)
				_draw_triangle(centre, pts[i], pts[(i + 2) % n_pts],\
							   facecolor='red', alpha=0.2)
			if Aij + Ajk < Aik:
				if graphic: pylab.plot((pts[i + 1][0],), (pts[i + 1][1],), 'go')
				del pts[i + 1]
			i += 1
			n_pts = len(pts)
		k += 1
	return numpy.asarray(pts)


class RhesusAdjacencyNetwork():
	network = None
	__monkeys = None

	def __init__(self, cohorts, graph=None):
		from matrr.models import Monkey
		self.network = graph if graph else nx.Graph()
		self.__monkeys = Monkey.objects.Drinkers().filter(cohort__in=cohorts)

		self.construct_network()

	def dump_graphml(self):
		return "".join(nx.generate_graphml(self.network))

	def dump_JSON(self):
		from networkx.readwrite import json_graph
		return json_graph.dumps(self.network)

	def construct_network(self):
		self.build_nodes()
		self.build_edges()
		print 'Finished'

	def build_nodes(self):
		for mky in self.__monkeys:
			self.add_node(mky)

	def build_edges(self):
		if not self.network.nodes():
			raise Exception("Build nodes first")
		for source_id in self.network.nodes():
			for target_id in self.network.nodes():
				if target_id == source_id:
					continue
				self.add_edge(source_id, target_id)

	def _construct_node_data(self, mky, data=None):
		#  IMPORTANT NOTE
		# Data put in here _will_ be visible in the GraphML, and in turn the web page's source code
		data = data if data else dict()
		data['monkey'] = mky.pk
		group = None
		for key in plotting_beta.rhesus_drinkers_distinct.iterkeys():
			if mky.pk in plotting_beta.rhesus_drinkers_distinct[key]:
				break
		if key == 'VHD':
			group =  4
		if key == 'HD':
			group =  3
		if key == 'MD':
			group =  2
		if key == 'LD':
			group =  1

		data['group'] = group
		return data

	def _construct_edge_data(self, source, target, data=None):
		from matrr.models import CohortBout
		#  IMPORTANT NOTE
		# Data put in here _will_ be visible in the GraphML, and in turn the web page's source code
		data = data if data else dict()
#		data['source'] = source
#		data['target'] = target
		cbt_count = CohortBout.objects.filter(ebt_set__mtd__monkey=source).filter(ebt_set__mtd__monkey=target).distinct().count()
		data['cbt_count'] = cbt_count
		return data

	def add_node(self, mky):
		self.network.add_node(mky.pk, **self._construct_node_data(mky))

	def add_edge(self, source, target):
		self.network.add_edge(source, target, **self._construct_edge_data(source, target))


def dump_RAN_json(cohort_pk=0, cohorts_pks=None):
	cohorts = [cohort_pk] if cohort_pk else cohorts_pks
	ran = RhesusAdjacencyNetwork(cohorts=cohorts)
	json = ran.dump_JSON()
	cohorts = [str(cohort) for cohort in cohorts]
	cohorts = '_'.join(cohorts)
	f = open('static/js/%s.RAN.json' % cohorts, 'w')
	f.write(json)
	f.close()
import networkx as nx
from matrr.models import FamilyNode, FamilyRelationship
import random

class CytoVisualStyle():
#	family_graph = None
	family_tree = None

	global_vs = {'backgroundColor': "#fff"}
	nodes_vs = {'shape': 'Diamond', 'size': 50, 'color': '#999', 'borderColor': 'orange', 'borderWidth': 5 }
	edges_vs = {'color': "blue", 'width': 3}

	def __init__(self, family_tree):
		self.family_tree = family_tree

	def continuous_node_colors(self, attr_name, min_value='#000000', max_value='#ffffff'):
		self.nodes_vs['color'] = {'continuousMapper': { 'attrName': attr_name,  'minValue': min_value, 'maxValue': max_value }}

	def discrete_node_shapes(self, shape_method=None):
		def default_shape(node):
			return 'diamond'

		get_shape = shape_method if shape_method else default_shape

		entries = list()
		for node in self.family_tree.family_graph.nodes(data=True):
			# node == ( node_id, {node data dictionary} )
			entries.append({'attrValue': node[0], 'value': get_shape(node)})

		self.nodes_vs['shape'] = {'discreteMapper': {'attrName': "id",'entries' : entries,} }

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
		self.nodes_vs['color'] = {'discreteMapper': {'attrName': "id",'entries' : entries} }

	def discrete_node_borderColors(self, color_method=None):
		def default_color(node):
			return 'purple'

		get_color = color_method if color_method else default_color

		entries = list()
		for node in self.family_tree.family_graph.nodes(data=True):
			# node == ( node_id, {node data dictionary} )
			entries.append({'attrValue': node[0], 'value': get_color(node)})
		self.nodes_vs['borderColor'] =  {'discreteMapper': {'attrName': "id", 'entries' : entries } }

	def discrete_node_borderWidth(self, width_method=None):
		def default_width(node):
			return node[1]['borderWidth_input']/100

		get_color = width_method if width_method else default_width

		entries = list()
		for node in self.family_tree.family_graph.nodes(data=True):
			# node == ( node_id, {node data dictionary} )
			entries.append({'attrValue': node[0], 'value': get_color(node)})
		self.nodes_vs['borderWidth'] =  {'discreteMapper': {'attrName': "id", 'entries' : entries } }

	def passthru_node_borderColors(self, attr_name='borderColor_color'):
		self.nodes_vs['borderColor'] =  { 'passthroughMapper': { 'attrName': attr_name } }

	def continuous_edge_curvature(self, attr_name, min_value='1', max_value='90'):
		self.edges_vs['curvature'] = {'continuousMapper': { 'attrName': attr_name,  'minValue': min_value, 'maxValue': max_value }}

	def passthru_edge_colors(self, attr_name='edge_color'):
		self.edges_vs['color'] =  { 'passthroughMapper': { 'attrName': attr_name } }

	def passthru_edge_width(self, attr_name='edge_width'):
		self.edges_vs['width'] =  { 'passthroughMapper': { 'attrName': attr_name } }

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
		if isinstance(family_node, FamilyNode):
			self.me = family_node
		else:
			raise Exception("family_node is not an instance of matrr.models.FamilyNode")
		self.family_graph = graph if graph else nx.Graph()
		self.depth = depth

		self.plant_tree()
		self.visual_style = visual_style if visual_style else CytoVisualStyle(self)

	def dump_graphml(self):
		return 	"".join(nx.generate_graphml(self.family_graph))

	def plant_tree(self):
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
				self.__grow_tree(relative, current_depth+1)
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
			return colors[random.randint(0,2)]

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
	from matrr.models import Monkey, Cohort, Institution
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
			index = random.randint(0, min(female_monkeys.count()-1, male_monkeys.count()-1))
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
			index = random.randint(0, min(female_monkeys.count()-1, male_monkeys.count()-1))
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


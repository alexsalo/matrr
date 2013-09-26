from collections import defaultdict
import math
from utils import gadgets
from matrr.plotting import RHESUS_COLORS
import random
import networkx as nx
import pygraphviz as pgv

class CytoVisualStyle():
#	family_graph = None
    family_tree = None

    global_vs = {'backgroundColor': "#fff"}
    nodes_vs = {'shape': 'Diamond', 'size': 50, 'color': '#999', 'borderColor': 'orange', 'borderWidth': 5}
    edges_vs = {'color': "blue", 'width': 3}

    def __init__(self, family_tree):
        self.family_tree = family_tree

    def continuous_node_colors(self, attr_name, min_value='#000000', max_value='#ffffff'):
        self.nodes_vs['color'] = {
        'continuousMapper': {'attrName': attr_name, 'minValue': min_value, 'maxValue': max_value}}

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
        self.edges_vs['curvature'] = {
        'continuousMapper': {'attrName': attr_name, 'minValue': min_value, 'maxValue': max_value}}

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
        self.family_graph.add_edge(source.monkey.pk, target.monkey.pk,
                                   **self._construct_edge_data(source, target, relation=relation))


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

        cohort = Cohort.objects.get_or_create(institution=Institution.objects.all()[0], coh_cohort_name='bogus cohort')[
            0]
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
        female_monkeys = Monkey.objects.exclude(pk__in=parents).exclude(pk__in=monkeys).filter(mky_gender='F',
                                                                                               cohort=11)
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


class ConfederateNetwork(object):
    network = None
    cohort = None
    monkeys = None
    depth = None # this doesn't do anything at the moment
    normalization_function = None

    nearest_bout_times = defaultdict(lambda: defaultdict(lambda: list())) # nearest_bout_time[source monkey.pk][target monkey.pk] = [array of seconds to nearest bout]
    mean_nearest_bout_times = defaultdict(lambda: dict()) # nearest_bout_time[source monkey.pk][target monkey.pk] = average seconds between monkey's nearest bout
    normalized_relationships = defaultdict(lambda: dict())

    def __init__(self, cohort, normalization_function=None, depth=1):
        from matrr.models import Cohort, Monkey
        assert isinstance(cohort, Cohort)
        self.cohort = cohort
        self.monkeys = Monkey.objects.Drinkers().filter(cohort=self.cohort)
        self.network = pgv.agraph.AGraph(name=self.cohort.coh_cohort_name, directed=True)
        self.normalization_function = normalization_function
        self.depth = depth # this doesn't do anything at the moment
        self.define_nodes()
        self.collect_nearest_bout_times()
        self.average_nearest_bout_times()
        self.normalize_averages()
        self.define_edges()


    def dump_graphml(self):
        return "".join(nx.generate_graphml(self.network))

    def define_edges(self):
        finished = list()
        for source_pk in self.normalized_relationships.iterkeys():
            for target_pk in self.normalized_relationships[source_pk]:
                sorted_pks = sorted([source_pk, target_pk])
                if not sorted_pks in finished and self.normalized_relationships[source_pk][target_pk]:
                    self._add_monkey_edge(source_pk, target_pk)
                    finished.append(sorted_pks)

    def define_nodes(self):
        for monkey in self.monkeys:
            self._add_monkey_node(monkey.pk)

    def collect_nearest_bout_times(self):
        from matrr.models import ExperimentBout
        import json
        print "Collecting nearest bout times..."
        try:
            f = open('utils/DATA/json/ConfederateNetwork-%d-nearest_bout_times.json' % self.cohort.pk, 'r')
        except:
            for monkey in self.monkeys:
                print "Starting Monkey %d" % monkey.pk
                for bout in ExperimentBout.objects.OA().filter(mtd__monkey=monkey):
                    nearest_bouts = gadgets.find_nearest_bouts(bout)
                    for close_bout in nearest_bouts:
                        self.nearest_bout_times[monkey.pk][close_bout.mtd.monkey.pk].append(math.fabs(bout.ebt_start_time-close_bout.ebt_start_time))
        else:
            self.nearest_bout_times = json.loads(f.read())
        finally:
            f = open('utils/DATA/json/ConfederateNetwork-%d-nearest_bout_times.json' % self.cohort.pk, 'w')
            f.write(json.dumps(self.nearest_bout_times))
            f.close()

    def average_nearest_bout_times(self):
        assert bool(self.nearest_bout_times) is True
        import numpy
        print "Averaging nearest bout times..."
        for monkey_pk in self.nearest_bout_times.iterkeys():
            for nearest_mky_pk in self.nearest_bout_times[monkey_pk].iterkeys():
                self.mean_nearest_bout_times[monkey_pk][nearest_mky_pk] = numpy.mean(self.nearest_bout_times[monkey_pk][nearest_mky_pk])

    def normalize_averages(self):
        def norm_sum(source, target):
            return self.mean_nearest_bout_times[source][target] + self.mean_nearest_bout_times[target][source]
        print "Normalizing relationships..."
        norm_function = self.normalization_function if self.normalization_function else norm_sum
        edge_values = list()
        for monkey_pk in self.nearest_bout_times.iterkeys():
            for nearest_mky_pk in self.nearest_bout_times[monkey_pk].iterkeys():
                norm_value = norm_function(monkey_pk, nearest_mky_pk)
                self.normalized_relationships[monkey_pk][nearest_mky_pk] = norm_value
                edge_values.append(norm_value)
        edge_values = sorted(edge_values)
        max_edge = edge_values[len(edge_values)-1]
        pct_cutoff = .25
        value_cutoff = edge_values[int(len(edge_values)*pct_cutoff)]
        for monkey_pk in self.nearest_bout_times.iterkeys():
            for nearest_mky_pk in self.nearest_bout_times[monkey_pk].iterkeys():
                if self.normalized_relationships[monkey_pk][nearest_mky_pk] >= value_cutoff:
                    self.normalized_relationships[monkey_pk][nearest_mky_pk] /= max_edge
                else:
                    self.normalized_relationships[monkey_pk][nearest_mky_pk] = 0

    def _construct_node_data(self, monkey_pk, data=None):
        from matrr.models import MonkeyToDrinkingExperiment
        #  IMPORTANT NOTE
        # Data put in here _will_ be visible in the GraphML, and in turn the web page's source code
        data = data if data else dict()
        mtds = MonkeyToDrinkingExperiment.objects.OA().exclude_exceptions().filter(monkey=monkey_pk)
        data['category'] = gadgets.identify_drinking_category(mtds)
        data['color'] = RHESUS_COLORS[data['category']]
        data['style'] = 'filled'
        data['fillcolor'] = RHESUS_COLORS[data['category']]
        data['fontcolor'] = 'white'
        data['label'] = monkey_pk
        return data

    def _construct_edge_data(self, source_pk, target_pk, data=None):
        #  IMPORTANT NOTE
        # Data put in here _will_ be visible in the GraphML, and in turn the web page's source code
        data = data if data else dict()
#        data['label'] = "%d->%d" % (int(source_pk), int(target_pk))
        data['label'] = "%.2f" % (self.normalized_relationships[source_pk][target_pk] + self.normalized_relationships[target_pk][source_pk])
        data['penwidth'] = (self.normalized_relationships[source_pk][target_pk] + self.normalized_relationships[target_pk][source_pk]+1)**2
        data['style'] = 'solid'
        data['dir'] = 'none'
#        data['penwidth'] = .2
        return data

    def _add_monkey_node(self, monkey_pk):
        self.network.add_node(monkey_pk, **self._construct_node_data(monkey_pk))

    def _add_monkey_edge(self, source_pk, target_pk):
        self.network.add_edge(source_pk, target_pk, **self._construct_edge_data(source_pk, target_pk))


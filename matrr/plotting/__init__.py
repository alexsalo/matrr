__author__ = 'developer'
import matplotlib

###############  matplotlibrc settings
matplotlib.rcParams['figure.subplot.left'] 	= 0.1	# the left side of the subplots of the figure
matplotlib.rcParams['figure.subplot.right'] 	= 0.98	# the right side of the subplots of the figure
matplotlib.rcParams['figure.subplot.bottom'] 	= 0.12	# the bottom of the subplots of the figure
matplotlib.rcParams['figure.subplot.top'] 	= 0.96	# the top of the subplots of the figure
matplotlib.rcParams['figure.subplot.wspace'] 	= 0.05	# the amount of width reserved for blank space between subplots
matplotlib.rcParams['figure.subplot.hspace'] 	= 0.05	# the amount of height reserved for white space between subplots
matplotlib.rcParams['font.size']                = 14 # Default font size
############### end

DEFAULT_CIRCLE_MAX = 280
DEFAULT_CIRCLE_MIN = 20
DEFAULT_FIG_SIZE = (10, 10)
DEFAULT_FIG_SIZE_ALEX = (16, 10)
HISTOGRAM_FIG_SIZE = (15, 10)
THIRDS_FIG_SIZE = (20, 8)
DEFAULT_DPI = 80
DEFAULT_ALEX_DPI = 200

DRINKING_CATEGORIES = ['VHD', 'HD', 'BD', 'LD']
DRINKING_CATEGORIES_CHOICES = []
DRINKING_CATEGORIES_COLORS = {'LD': '#0052CC', 'BD': '#008000', 'HD': '#FF6600', 'VHD': '#FF0000', 'None': 'k', None: 'k'}
DRINKING_CATEGORIES_COLORS_ACCENT = {'LD': '#3396FF', 'BD': '#33B333', 'HD': '#CC3333', 'VHD': '#CC3333'}

DRINKING_CATEGORY_MARKER = {'LD': 'v', 'BD': '<', 'HD': '>', 'VHD': '^'}

COHORT_END_FIRST_OPEN_ACCESS = {10: "2011-08-01", 9: '2012-01-08', 6: "2009-10-13", 5: "2009-05-24"}

RHESUS_DRINKERS = dict()
RHESUS_DRINKERS['LD'] = [10048, 10052, 10055, 10056, 10058, 10083, 10084, 10085, 10089, 10090, 10092] # all drinking monkeys in 5,6,9,10 not listed below
RHESUS_DRINKERS['BD'] = [10082, 10057, 10087, 10088, 10059, 10054, 10086, 10051, 10049, 10063, 10091, 10060, 10064, 10098, 10065, 10097, 10066, 10067, 10061, 10062]
RHESUS_DRINKERS['HD'] = [10082, 10049, 10064, 10063, 10097, 10091, 10065, 10066, 10067, 10088, 10098, 10061, 10062]
RHESUS_DRINKERS['VHD'] = [10088, 10091, 10066, 10098, 10063, 10061, 10062]

RHESUS_DRINKERS_DISTINCT = dict()
RHESUS_DRINKERS_DISTINCT['LD'] = [10048, 10052, 10055, 10056, 10058, 10083, 10084, 10085, 10089, 10090, 10092]
RHESUS_DRINKERS_DISTINCT['BD'] = [10057, 10087, 10059, 10054, 10086, 10051, 10060]
RHESUS_DRINKERS_DISTINCT['HD'] = [10082, 10049, 10064, 10097, 10065, 10067]
RHESUS_DRINKERS_DISTINCT['VHD'] = [10088, 10091, 10066, 10098, 10063, 10061, 10062]

# with cohort_pk=8 included
RDD_56890 = dict()
RDD_56890['LD'] = [10048, 10052, 10055, 10056, 10058, 10083, 10084, 10085, 10089, 10090, 10092, 10072, 10074, 10077]
RDD_56890['BD'] = [10057, 10087, 10059, 10054, 10086, 10051, 10060]
RDD_56890['HD'] = [10082, 10049, 10064, 10097, 10065, 10067]
RDD_56890['VHD'] = [10088, 10091, 10066, 10098, 10063, 10061, 10062, 10073, 10075]

ALL_RHESUS_DRINKERS = [__x for __d in RHESUS_DRINKERS_DISTINCT.itervalues() for __x in __d]
ALL_RDD56890 = [__x for __d in RDD_56890.itervalues() for __x in __d]


RHESUS_COLORS = DRINKING_CATEGORIES_COLORS
RHESUS_COLORS_ACCENT = DRINKING_CATEGORIES_COLORS_ACCENT
RHESUS_MONKEY_CATEGORY = dict()
RHESUS_MONKEY_COLORS = dict()
RHESUS_MONKEY_MARKERS = dict()
for key in DRINKING_CATEGORIES:
    for monkey_pk in RHESUS_DRINKERS_DISTINCT[key]:
        RHESUS_MONKEY_CATEGORY[monkey_pk] = key
        RHESUS_MONKEY_COLORS[monkey_pk] = RHESUS_COLORS[key]
        RHESUS_MONKEY_MARKERS[monkey_pk] = DRINKING_CATEGORY_MARKER[key]

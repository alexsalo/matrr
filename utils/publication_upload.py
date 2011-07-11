from matrr.models import *
from django.db import transaction

from suds.client import Client
from suds.sax.text import Text

import csv

import logging
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger('suds.client').setLevel(logging.CRITICAL)

@transaction.commit_on_success
def add_publications(file):
  input = csv.reader(open( file, 'rU'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
  # get the column headers
  columns = input.next()

  url = 'http://www.ncbi.nlm.nih.gov/entrez/eutils/soap/v2.0/efetch_pubmed.wsdl'
  client = Client(url)

  results = []
  for row in input:
    pmid = row[0]
    result = client.service.run_eFetch(id=int(pmid), retmax=1, email='nicholas.soltau@gmail.com')
    result.cohorts = row[1]
    results.append(result)

  for result in results:
    #print result
    medline = result.PubmedArticleSet.PubmedArticle.MedlineCitation
    article = medline.Article
    journal = article.Journal
    # get the list of authors
    authors = ''
    first = True
    for author in article.AuthorList.Author:
      if not first:
        authors += ", "
      authors += author.LastName + " " + author.ForeName
      first = False
    # get the abstract text
    abstract = None
    if "Abstract" in article.__dict__:
      abstract = ""
      for text in article.Abstract.AbstractText:
        if not isinstance(text, Text):
          # if the AbstractText is not a string,
          # pull the data out of the dict
          if "_Label" in text.__dict__:
            abstract += text._Label + ": "
          abstract += text.value + "\n"
        else:
          # the AbstractText is a string,
          # so just add it
          abstract += text
    # get the MeSH keywords
    keywords = None
    if "MeshHeadingList" in medline.__dict__:
      keywords = ""
      first = True
      for heading in medline.MeshHeadingList.MeshHeading:
        if not first:
          keywords += ", "
        keywords += heading.DescriptorName.value
        first = False
        if "QualifierName" in heading.__dict__:
          keywords += " ("
          first2 = True
          for qualifier in heading.QualifierName:
            if not first2:
              keywords += ", "
            keywords += qualifier.value
            first2 = False
          keywords += ")"
    pub = None
    if Publication.objects.filter(pmid=medline.PMID.value).count() != 0:
      pub = Publication.objects.get(pmid=medline.PMID.value)
    else:
      pub = Publication()
    if authors is not None:
      pub.authors = authors.encode('utf8')
    if "ArticleTitle" in article.__dict__:
      pub.title = article.ArticleTitle.encode('utf8')
    if journal is not None:
      pub.journal = journal.Title.encode('utf8')
    jissue = journal.JournalIssue
    if "Year" in jissue.PubDate.__dict__:
      pub.published_year = jissue.PubDate.Year
    if "Month" in jissue.PubDate.__dict__:
      pub.published_month = jissue.PubDate.Month
    if "Issue" in jissue.__dict__:
      pub.issue = jissue.Issue
    if "Volume" in jissue.__dict__:
      pub.volume = jissue.Volume
    pub.pmid = medline.PMID.value
    if abstract is not None:
      pub.abstract = abstract.encode('utf8')
    if keywords is not None:
      pub.keywords = keywords.encode('utf8')

    pub.save()
    # add the cohorts
    cohorts = []
    if result.cohorts and result.cohorts != "":
      cohort_names = result.cohorts.split(", ")
      print cohort_names
      for cohort_name in cohort_names:
        print cohort_name
        if cohort_name != "CNSA":
          cohorts.append(Cohort.objects.get(coh_cohort_name=cohort_name))
    
    pub.cohorts = cohorts
    pub.save()
    
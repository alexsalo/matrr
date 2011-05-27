from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib import colors

PAGE_HEIGHT=defaultPageSize[1]
PAGE_WIDTH=defaultPageSize[0]
styles = getSampleStyleSheet()

class PdfMaker:

  def __init__(self, title, subtitle=None, style=styles["Normal"]):
    self.title = title
    self.subtitle = subtitle
    self.Story = [Spacer(1, 1.5*inch)]
    self.style = style
    self.keep_together = False

  def myFirstPage(self, canvas, doc):
    canvas.saveState()
    canvas.setFont('Times-Bold',16)
    canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-108, self.title)
    canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-124, self.subtitle)
    canvas.setFont('Times-Roman',9)
    canvas.drawString(inch, 0.75 * inch, "Page %d" % (doc.page))
    canvas.drawCentredString(PAGE_WIDTH/2.0, 0.75 * inch, self.title)
    canvas.drawCentredString(PAGE_WIDTH/2.0, 0.61 * inch, self.subtitle)
    canvas.restoreState()

  def myLaterPages(self, canvas, doc):
    canvas.saveState()
    canvas.setFont('Times-Roman',9)
    canvas.drawString(inch, 0.75 * inch, "Page %d" % (doc.page))
    canvas.drawCentredString(PAGE_WIDTH/2.0, 0.75 * inch, self.title)
    canvas.drawCentredString(PAGE_WIDTH/2.0, 0.61 * inch, self.subtitle)
    canvas.restoreState()

  def createPdf(self, file):
    doc = SimpleDocTemplate(file)
    doc.build(self.Story, onFirstPage=self.myFirstPage, onLaterPages=self.myLaterPages)

    return file

  def addText(self, string, style="Normal", spacing=0.2):
    if self.keep_together:
      story = self.together
    else:
      story = self.Story
    story.append(Paragraph( string, styles[style] ))
    if spacing:
      story.append(Spacer(1, spacing*inch))

  def addTable(self, data, style=None, spacing=0.2, align="CENTER"):
    if self.keep_together:
      story = self.together
    else:
      story = self.Story
    story.append(Table( data=data, style=TableStyle(style), hAlign=align ))
    if spacing:
      story.append(Spacer(1, spacing*inch))

  def addSpace(self, spacing=0.2):
    if self.keep_together:
      story = self.together
    else:
      story = self.Story
    self.Story.append(Spacer(1, spacing*inch))

  def startKeepTogether(self):
    self.begin = self.Story
    self.together=[]
    self.keep_together = True

  def endKeepTogether(self):
    self.Story.append(KeepTogether(self.together))
    self.keep_together = False
  
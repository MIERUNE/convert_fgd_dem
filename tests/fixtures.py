"""Fixtures shared by the tests: a minimal FGD DEM XML and a feedback stub"""

from pathlib import Path

# 2x2 pixels, values are given from the north-west corner, row by row
DEM_XML = """<?xml version="1.0" encoding="utf-8"?>
{doctype}<Dataset xmlns="http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema" xmlns:gml="http://www.opengis.net/gml/3.2">
  <DEM>
    <mesh>{mesh}</mesh>
    <coverage>
      <gml:boundedBy>
        <gml:Envelope>
          <gml:lowerCorner>42.916666667 141.25</gml:lowerCorner>
          <gml:upperCorner>43.0 141.375</gml:upperCorner>
        </gml:Envelope>
      </gml:boundedBy>
      <gml:gridDomain>
        <gml:Grid>
          <gml:limits><gml:GridEnvelope><gml:low>0 0</gml:low><gml:high>1 1</gml:high></gml:GridEnvelope></gml:limits>
        </gml:Grid>
      </gml:gridDomain>
      <gml:rangeSet>
        <gml:DataBlock>
          <gml:tupleList>
地表面,10.5
地表面,11.5
地表面,12.5
地表面,13.5
          </gml:tupleList>
        </gml:DataBlock>
      </gml:rangeSet>
      <gml:coverageFunction>
        <gml:GridFunction><gml:startPoint>0 0</gml:startPoint></gml:GridFunction>
      </gml:coverageFunction>
    </coverage>
  </DEM>
</Dataset>
"""


def write_dem_xml(directory, name="dem.xml", mesh="64413277", doctype=""):
    """Write the fixture in directory and return its path"""
    xml_path = Path(directory) / name
    xml_path.write_text(DEM_XML.format(doctype=doctype, mesh=mesh), encoding="utf-8")
    return xml_path


class DummyFeedback:
    """Stand-in for QgsFeedback, so that the tests do not need QGIS"""

    def __init__(self):
        self.errors = []

    def pushInfo(self, message):
        pass

    def reportError(self, message, fatalError=False):
        self.errors.append(message)

    def setProgress(self, progress):
        pass

    def isCanceled(self):
        return False

    def cancel(self):
        pass

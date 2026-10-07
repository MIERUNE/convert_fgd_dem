import tempfile
import unittest
from pathlib import Path

from convert_fgd_dem.src.convert_fgd_dem.dem import Dem
from convert_fgd_dem.src.convert_fgd_dem.helpers import DemInputXmlException

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


class TestDem(unittest.TestCase):
    def test_bounds_latlng(self):
        dem_ins = Dem(Path("../DEM/FG-GML-6441-32-DEM5A.zip"))
        bounds_latlng = {
            "lower_left": {"lat": 42.916666667, "lon": 141.25},
            "upper_right": {"lat": 43.0, "lon": 141.375},
        }
        self.assertEqual(bounds_latlng, dem_ins.bounds_latlng)


class TestGetXmlContent(unittest.TestCase):
    def _get_xml_content(self, xml):
        with tempfile.TemporaryDirectory() as tmp:
            xml_path = Path(tmp) / "dem.xml"
            xml_path.write_text(xml, encoding="utf-8")
            return Dem(xml_path).get_xml_content(xml_path)

    def test_valid_xml(self):
        content = self._get_xml_content(DEM_XML.format(doctype="", mesh="64413277"))
        self.assertEqual(64413277, content["mesh_code"])
        self.assertEqual(
            ["10.5", "11.5", "12.5", "13.5"], content["elevation"]["items"]
        )

    def test_doctype_with_internal_entity_is_rejected(self):
        # Without the DOCTYPE guard this document is valid and yields mesh 64413277
        doctype = '<!DOCTYPE Dataset [<!ENTITY m "64413277">]>\n'
        with self.assertRaises(DemInputXmlException):
            self._get_xml_content(DEM_XML.format(doctype=doctype, mesh="&m;"))


if __name__ == "__main__":
    unittest.main()

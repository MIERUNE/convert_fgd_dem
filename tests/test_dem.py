import tempfile
import unittest
from pathlib import Path

from convert_fgd_dem.src.convert_fgd_dem.dem import Dem
from convert_fgd_dem.src.convert_fgd_dem.helpers import DemInputXmlException
from convert_fgd_dem.tests.fixtures import DEM_XML


class TestDem(unittest.TestCase):
    def test_bounds_latlng(self):
        with tempfile.TemporaryDirectory() as tmp:
            xml_path = Path(tmp) / "dem.xml"
            xml_path.write_text(
                DEM_XML.format(doctype="", mesh="64413277"), encoding="utf-8"
            )

            # Same steps as Converter.run
            dem_ins = Dem(xml_path)
            dem_ins.all_content_list.append(dem_ins.get_xml_content(xml_path))
            dem_ins.contents_to_array()

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
        with self.assertRaisesRegex(DemInputXmlException, "DOCTYPE"):
            self._get_xml_content(DEM_XML.format(doctype=doctype, mesh="&m;"))

    def test_doctype_after_long_prolog_is_rejected(self):
        # The guard reads the file in chunks: check a DOCTYPE past the first one
        prolog = "<!-- " + "x" * 200_000 + " -->\n"
        doctype = prolog + '<!DOCTYPE Dataset [<!ENTITY m "64413277">]>\n'
        with self.assertRaisesRegex(DemInputXmlException, "DOCTYPE"):
            self._get_xml_content(DEM_XML.format(doctype=doctype, mesh="&m;"))

    def test_invalid_xml_raises_generic_error(self):
        with self.assertRaisesRegex(DemInputXmlException, "Incorrect XML file"):
            self._get_xml_content("<Dataset><unclosed></Dataset>")


if __name__ == "__main__":
    unittest.main()

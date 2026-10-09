import tempfile
import unittest
import zipfile
from pathlib import Path

from osgeo import gdal, gdalconst

from convert_fgd_dem.src.convert_fgd_dem.converter import Converter
from convert_fgd_dem.tests.fixtures import DummyFeedback, write_dem_xml

# Pixel rows go from the north to the south, like the values of the XML
EXPECTED_ELEVATION = [[10.5, 11.5], [12.5, 13.5]]
# Origin is the north-west corner. Pixel size is the extent divided by 2 pixels
EXPECTED_GEO_TRANSFORM = (141.25, 0.0625, 0.0, 43.0, 0.0, -0.0416666665)


class TestConverter(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.output_path = self.tmp / "output"

    def _convert(self, import_path, rgbify=False):
        feedback = DummyFeedback()
        Converter(
            import_path=import_path,
            output_path=self.output_path,
            file_name="dem.tif",
            rgbify=rgbify,
            feedback=feedback,
        ).run()
        self.assertEqual([], feedback.errors)
        return gdal.Open(str(self.output_path / "dem.tif"), gdalconst.GA_ReadOnly)

    def _assert_geometry(self, src):
        self.assertEqual(2, src.RasterXSize)
        self.assertEqual(2, src.RasterYSize)
        for expected, actual in zip(EXPECTED_GEO_TRANSFORM, src.GetGeoTransform()):
            self.assertAlmostEqual(expected, actual, places=9)

    def test_xml_to_geotiff(self):
        xml_path = write_dem_xml(self.tmp)

        src = self._convert(xml_path)

        self._assert_geometry(src)
        self.assertEqual(1, src.RasterCount)
        band = src.GetRasterBand(1)
        self.assertEqual(EXPECTED_ELEVATION, band.ReadAsArray().tolist())
        self.assertEqual(-9999, band.GetNoDataValue())

    def test_zip_to_geotiff(self):
        input_dir = self.tmp / "input"
        input_dir.mkdir()
        xml_path = write_dem_xml(self.tmp)
        zip_path = input_dir / "dem.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(xml_path, xml_path.name)

        src = self._convert(zip_path)

        self._assert_geometry(src)
        self.assertEqual(
            EXPECTED_ELEVATION, src.GetRasterBand(1).ReadAsArray().tolist()
        )
        # The extracted files are removed after the conversion
        self.assertEqual([zip_path], list(input_dir.iterdir()))

    def test_xml_to_terrain_rgb(self):
        xml_path = write_dem_xml(self.tmp)

        src = self._convert(xml_path, rgbify=True)

        self._assert_geometry(src)
        self.assertEqual(3, src.RasterCount)
        r, g, b = (src.GetRasterBand(i).ReadAsArray() for i in (1, 2, 3))
        # Terrain RGB: height = (R * 256 * 256 + G * 256 + B - 100000) / 10
        elevation = (r.astype(int) * 65536 + g.astype(int) * 256 + b - 100000) / 10
        for expected_row, actual_row in zip(EXPECTED_ELEVATION, elevation.tolist()):
            for expected, actual in zip(expected_row, actual_row):
                self.assertAlmostEqual(expected, actual, places=6)


if __name__ == "__main__":
    unittest.main()

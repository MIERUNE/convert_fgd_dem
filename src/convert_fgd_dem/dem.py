import os
import shutil
import xml.etree.ElementTree as et
import zipfile
from pathlib import Path

import numpy as np

from .helpers import DemInputXmlException


class Dem:
    """Retrieve metadata from DEM xml"""

    def __init__(self, import_path):
        """Initializer

        Args:
            import_path (Path): Path object of import path

        Notes:
            "Meta_data" refers to mesh code, lonlat of the bottom left and top right, grid size, initial position, and pixel size of DEM.
            "Content" refers to mesh code, metadata, and elevation values.
        """
        self.import_path: Path = import_path
        self.xml_paths: list = self._get_xml_paths()

        self.all_content_list: list = []
        self.mesh_code_list: list = []
        self.meta_data_list: list = []
        self._get_xml_content_list()

        self.np_array_list: list = []
        self._store_np_array_list()

        self.bounds_latlng: dict = {}
        self._store_bounds_latlng()

    def _unzip_dem(self, dest_dir):
        """Unzip the zip file containing the DEM

        Args:
            dest_dir (Path): Path object of unzip directory
        """
        with zipfile.ZipFile(self.import_path, "r") as zip_data:
            zip_data.extractall(path=dest_dir)
            # Delete unnecessary files created when macOS
            garbage_dir = dest_dir / "__MACOSX"
            if garbage_dir.exists():
                shutil.rmtree(garbage_dir)

            # If the directory with the same name is not created in the unzipped directory, return
            if dest_dir.glob(".xml"):
                return

            # If not, retrieve it from subdirectory
            for path in zip_data.namelist():
                if path.endswith(".xml"):
                    try:
                        shutil.move(dest_dir / path, dest_dir)
                    except shutil.Error:
                        print(
                            f"ファイルがすでに存在しています。"
                            f"ファイルの移動をスキップし、オリジナルファイルを削除します：{dest_dir / path}")
                        os.remove(dest_dir / path)
                        continue
            # Deleted the directory with the same name as the parent folder
            if (dest_dir / self.import_path.stem).exists():
                (dest_dir / self.import_path.stem).rmdir()

    def _get_xml_paths(self):
        """Create a list of xml Path objects from the specified path

        Returns:
            list: List containing xml paths

        """
        if self.import_path.is_dir():
            xml_paths = [
                xml_path for xml_path in self.import_path.glob("*.xml")]
            if xml_paths is None:
                raise DemInputXmlException("指定ディレクトリに.xmlが存在しません")

        elif self.import_path.suffix == ".xml":
            xml_paths = [self.import_path]

        elif self.import_path.suffix == ".zip":
            extract_dir = self.import_path.parent / self.import_path.stem
            self._unzip_dem(extract_dir)
            xml_paths = [
                xml_path for xml_path in extract_dir.glob("*.xml")]
            if not xml_paths:
                raise DemInputXmlException("指定のパスにxmlファイルが存在しません")
        else:
            raise DemInputXmlException(
                "指定できる形式は「xml」「.xmlが格納されたディレクトリ」「.xmlが格納された.zip」のみです")
        return xml_paths

    @staticmethod
    def _format_metadata(raw_metadata):
        """Format the raw metadata

        Args:
            raw_metadata (dict): A dictionary containing raw metadata retrieved from xml

        Returns:
            dict: A dictionary containing processed metadata

        """
        lowers = raw_metadata["lower_corner"].split(" ")
        lower_corner = {"lat": float(lowers[0]), "lon": float(lowers[1])}

        uppers = raw_metadata["upper_corner"].split(" ")
        upper_corner = {"lat": float(uppers[0]), "lon": float(uppers[1])}

        grids = raw_metadata["grid_length"].split(" ")
        grid_length = {"x": int(grids[0]) + 1, "y": int(grids[1]) + 1}

        start_points = raw_metadata["start_point"].split(" ")
        start_point = {"x": int(start_points[0]), "y": int(start_points[1])}

        pixel_size = {
            "x": (
                upper_corner["lon"] -
                lower_corner["lon"]) /
            grid_length["x"],
            "y": (
                lower_corner["lat"] -
                upper_corner["lat"]) /
            grid_length["y"],
        }

        meta_data = {
            "mesh_code": raw_metadata["mesh_code"],
            "lower_corner": lower_corner,
            "upper_corner": upper_corner,
            "grid_length": grid_length,
            "start_point": start_point,
            "pixel_size": pixel_size,
        }

        return meta_data

    def get_xml_content(self, xml_path):
        """Read xml to get mesh code, metadata and elevation value

        Args:
            xml_path (Path): Path object of xml path

        Returns:
            dict: A dictionary containing mesh code, metadata, and elevation values
        """
        if not xml_path.suffix == ".xml":
            raise DemInputXmlException("指定できる形式は.xmlのみです")

        name_space = {
            "dataset": "http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema",
            "gml": "http://www.opengis.net/gml/3.2",
        }

        try:
            tree = et.parse(xml_path)
            root = tree.getroot()
            mesh_code = int(
                root.find(
                    "dataset:DEM//dataset:mesh",
                    name_space
                ).text
            )
        except et.ParseError:
            raise DemInputXmlException("不正なxmlです")

        raw_metadata = {
            "mesh_code": mesh_code,
            "lower_corner": root.find(
                "dataset:DEM//dataset:coverage//gml:boundedBy//gml:Envelope//gml:lowerCorner",
                name_space,
            ).text,
            "upper_corner": root.find(
                "dataset:DEM//dataset:coverage//gml:boundedBy//gml:Envelope//gml:upperCorner",
                name_space,
            ).text,
            "grid_length": root.find(
                "dataset:DEM//dataset:coverage//gml:gridDomain//gml:Grid//gml:high",
                name_space,
            ).text,
            "start_point": root.find(
                "dataset:DEM//dataset:coverage//gml:coverageFunction//gml:GridFunction//gml:startPoint",
                name_space,
            ).text,
        }

        meta_data = self._format_metadata(raw_metadata)

        tuple_list = root.find(
            "dataset:DEM//dataset:coverage//gml:rangeSet//gml:DataBlock//gml:tupleList",
            name_space,
        ).text

        # Create a two-dimensional array list like [[地表面,354.15]...]
        if tuple_list.startswith("\n"):
            strip_tuple_list = tuple_list.strip()
            items = [item.split(",")[1]
                     for item in strip_tuple_list.split("\n")]
        else:
            items = [item.split(",")[1] for item in tuple_list.split("\n")]

        elevation = {"mesh_code": mesh_code, "items": items}

        return {
            "mesh_code": mesh_code,
            "meta_data": meta_data,
            "elevation": elevation,
        }

    def _check_mesh_codes(self):
        """
        Check for overlap between secondary and tertiary meshes

        Raises:
            - Error if the mesh code is other than 6 or 8 digits
            - Error when secondary and tertiary meshes are mixed
        """
        third_mesh_codes = []
        second_mesh_codes = []

        for mesh_code in self.mesh_code_list:
            str_mesh = str(mesh_code)
            if len(str_mesh) == 6:
                second_mesh_codes.append(mesh_code)
            elif len(str_mesh) == 8:
                third_mesh_codes.append(mesh_code)
            else:
                raise DemInputXmlException(f"メッシュコードが不正です。mesh_code={mesh_code}")

        if all((third_mesh_codes, second_mesh_codes)):
            raise DemInputXmlException("2次メッシュと3次メッシュが混合しています。")

    def _get_xml_content_list(self):
        """Create a list of metadata and elevation values"""
        self.all_content_list = [
            self.get_xml_content(xml_path) for xml_path in self.xml_paths
        ]

        self.mesh_code_list = [item["mesh_code"]
                               for item in self.all_content_list]
        self._check_mesh_codes()

        self.meta_data_list = [item["meta_data"]
                               for item in self.all_content_list]

    def _store_bounds_latlng(self):
        """対象の全Demから緯度経度の最大・最小値を取得"""
        lower_left_lat = min([meta_data["lower_corner"]["lat"]
                              for meta_data in self.meta_data_list])
        lower_left_lon = min([meta_data["lower_corner"]["lon"]
                              for meta_data in self.meta_data_list])
        upper_right_lat = max([meta_data["upper_corner"]["lat"]
                               for meta_data in self.meta_data_list])
        upper_right_lon = max([meta_data["upper_corner"]["lon"]
                               for meta_data in self.meta_data_list])

        bounds_latlng = {
            "lower_left": {"lat": lower_left_lat, "lon": lower_left_lon},
            "upper_right": {"lat": upper_right_lat, "lon": upper_right_lon},
        }

        self.bounds_latlng = bounds_latlng

    @staticmethod
    def _get_np_array(content):
        """Gets the elevation value from Dem and returns the mesh code and elevation value (np.array)

        Args:
            content(dict): Dictionary containing detailed information of DEM

        Returns:
            dict: A dictionary containing mesh code and elevation values (np.array)
        """
        mesh_code = content["mesh_code"]
        meta_data = content["meta_data"]
        elevation = content["elevation"]["items"]

        x_length = meta_data["grid_length"]["x"]
        y_length = meta_data["grid_length"]["y"]

        array = np.empty((y_length, x_length), np.float32)
        array.fill(-9999)

        start_point_x = meta_data["start_point"]["x"]
        start_point_y = meta_data["start_point"]["y"]

        # Since the data is arranged from the northwest to the southeast,
        # put the coordinates in the array for each row.
        index = 0
        for y in range(start_point_y, y_length):
            for x in range(start_point_x, x_length):
                try:
                    insert_value = float(elevation[index])
                    array[y][x] = insert_value
                # The number of rows of data and the size of the grid do not always match
                except IndexError:
                    break
                index += 1
            start_point_x = 0

        np_array = {"mesh_code": mesh_code, "np_array": array}

        return np_array

    def _store_np_array_list(self):
        """Create a list of dictionaries containing mesh code and elevation value np.array from Dem"""
        self.np_array_list = [
            self._get_np_array(content) for content in self.all_content_list
        ]

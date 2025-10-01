import cadquery as cq
from ocp_vscode import show
import cv2
import numpy as np
import os
from tqdm import tqdm


class ArucoMarkerGenerator:
    """
    A class to generate 3D models of ArUco markers.
    """

    def __init__(self, aruco_dict_id=cv2.aruco.DICT_4X4_50, marker_id=0, side_length=20, thickness=2.0, margin=2, black_bits_thickness=0.4, white_bits_thickness=1.8):
        """
        Initializes the ArUco marker generator.

        :param aruco_dict_id: The ID of the ArUco dictionary.
        :param marker_id: The ID of the marker.
        :param side_length: The side length of the marker (mm).
        :param thickness: The total thickness of the marker (mm).
        :param margin: The margin around the marker (mm).
        :param black_bits_thickness: The thickness of the black bits (mm).
        :param white_bits_thickness: The thickness of the white bits (mm).
        """
        self.aruco_dict_id = aruco_dict_id
        self.marker_id = marker_id
        self.side_length = side_length
        self.thickness = thickness
        self.margin = margin
        self.black_bits_thickness = black_bits_thickness
        self.white_bits_thickness = white_bits_thickness

        self.aruco_dict = cv2.aruco.getPredefinedDictionary(self.aruco_dict_id)
        self.pixels = self.aruco_dict.markerSize + 2  # code area + border(2)
        self.pixel_side_length = self.side_length / self.pixels
        self.img_bin = self._generate_marker_image_binary()

    def _generate_marker_image_binary(self):
        """Generates a binary image of the marker."""
        img = cv2.aruco.generateImageMarker(self.aruco_dict, self.marker_id, self.pixels)
        return 1 - (img // 255)  # black=1, white=0

    def _create_black_bits(self):
        """Creates the 3D model for the black bits."""
        black_bits_body = cq.Workplane("XY")
        for x, y in np.ndindex(self.img_bin.shape):
            if self.img_bin[x, y] == 1:  # black pixel
                x_pos = x * self.pixel_side_length
                y_pos = y * self.pixel_side_length
                pixel_box = cq.Workplane("XY").rect(self.pixel_side_length, self.pixel_side_length).extrude(-self.black_bits_thickness).translate((x_pos, y_pos, self.thickness))
                black_bits_body = black_bits_body.union(pixel_box)
        return black_bits_body

    def _create_white_bits(self, black_bits_body):
        """Creates the 3D model for the white bits."""
        offset = self.side_length / 2 - self.pixel_side_length / 2
        white_bits_sketch = cq.Workplane("XY").rect(self.side_length, self.side_length)
        white_bits_sketch_margin = white_bits_sketch.offset2D(self.margin)
        white_bits_body = white_bits_sketch_margin.extrude(self.white_bits_thickness).translate((offset, offset, 0))
        white_bits_body = white_bits_body.cut(black_bits_body)
        return white_bits_body

    def create_assembly(self):
        """Creates the 3D assembly of the marker."""
        black_bits = self._create_black_bits()
        white_bits = self._create_white_bits(black_bits)

        assy = cq.Assembly(name="aruco_marker")
        assy.add(white_bits, name="white_bits", color=cq.Color("white"))
        assy.add(black_bits, name="black_bits", color=cq.Color("black"))
        return assy

    def get_aruco_dict_name(self):
        """Gets the name of the ArUco dictionary."""
        aruco_dict_names = {value: name for name, value in cv2.aruco.__dict__.items() if name.startswith("DICT_")}
        return aruco_dict_names.get(self.aruco_dict_id, f"CUSTOM_DICT_{self.aruco_dict_id}")

    def save(self, assembly, output_dir="output"):
        """Saves the assembly to a file."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        dict_name = self.get_aruco_dict_name()
        filename = f"marker_{dict_name}_id={self.marker_id}.stl"
        filepath = os.path.join(output_dir, filename)

        assembly.save(filepath)
        # print(f"Saved to {filepath}")


if __name__ == "__main__":

    for id in tqdm(range(0, 16)):

        generator = ArucoMarkerGenerator(cv2.aruco.DICT_4X4_50, marker_id=id, side_length=20, thickness=2.0, margin=1.5, black_bits_thickness=0.4, white_bits_thickness=1.8)

        marker_assembly = generator.create_assembly()

        generator.save(marker_assembly, output_dir="output")

        # show(marker_assembly)

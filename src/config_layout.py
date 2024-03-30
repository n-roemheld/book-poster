import numpy as np
from dataclasses import dataclass
from Dimensions_file import Dimensions, Dimensions_cm, Length, Position, Dimensions_px


@dataclass
class ConfigLayout:

    poster = {}
    poster["background_color_hex"]: str = "#FFFFFF"
    poster["dim"]: Dimensions_cm = Dimensions_cm(width=60, height=90)
    poster["min_margins_factor"] = 0.01 * np.array([1, 1, 1])  # of poster height

    grid = {}
    grid["n_books"]: tuple[int, int] = (8, 8)
    grid["cover_dist_factor"] = np.array([0.01, 0.01])  # of cover width, height

    year_shading = {}
    year_shading["enable"]: bool = True
    year_shading["color1_hex"]: str = "#FFFFFF"
    year_shading["color2_hex"]: str = "#CCCCCC"
    year_shading["factors"] = 1 * np.array([0.1, 0.05])  # of cover width, height

    book = {}
    book["rating_print"]: bool = True
    book["default_aspect_ratio"]: float = 0.6555
    book["font_path"]: str = "./fonts/Lato-star.ttf"
    book[
        "expected_cover_height"
    ]: (
        int
    ) = 475  # px, common height of cover images on goodreads, used for dpi calculations
    book["shadow_factors"] = np.array([0.03, 0.06])  # of cover width, height
    book["font_height_factor"]: float = 1 / 15.0  # of cover height
    book["font_vspace_factor"]: float = 1 / 4.0  # of font height

    title = {}
    title["enable"]: bool = True
    title["font_path"]: str = "./fonts/Merriweather-Regular.ttf"
    title["font_height_factor"]: float = 0.02  # of poster height
    title["vspace_factor"]: float = 0.5  # of font height

    signature = {}
    signature["enable"]: bool = True
    signature["font_path"]: str = "./fonts/Lato-star.ttf"
    signature["height_factor"]: float = 1.2  # of title height
    signature["vspace_factor"]: float = 0.3  # of signature height
    signature["font_height_factor"]: float = 0.35  # of signature height
    signature["hspace_factor"]: float = 0.35  # of signature height

    def get_layout_config_dicts(self):
        return (
            self.poster,
            self.grid,
            self.year_shading,
            self.book,
            self.title,
            self.signature,
        )

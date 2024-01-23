from dataclasses import dataclass, fields, Field
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import NamedTuple
from datetime import datetime, timezone
from Dimensions_file import Dimensions, Dimensions_cm, Length, Position

H = 0 # horizontal index
V = 1 # vertical intex

TOP = 0 # top margin index
BOTTOM = 1 # bottom margin index
SIDES = 2 # sides margin index

# TODO: Change into PosterLayoutFactory (not dataclass) that returns a PosterLayout that only contains used attributes
@dataclass(frozen=True)
class PosterParametersPublic:
    '''Poster design parameters that are used externally unmodified'''
    output_file:            str                 = "poster.jpg"
    background_color_hex:   str                 = "#FFFFFF"
    year_shading:           bool                = True
    year_shading_color1_hex:str                 = "#CCCCCC"
    year_shading_color2_hex:str                 = "#FFFFFF"
    number_of_text_lines:   int                 = 1 # TODO: make dynamic, depending on text used
    print_rating:           bool                = True
    print_title:            bool                = True
    print_signature:        bool                = True
    n_books_grid:           tuple[int,int]      = (8,8)

@dataclass
class PosterParametersPrivate:
    '''Poster design parameters that are only used to compute other parameters and not used on their own'''
    # Internal only!
    poster_dim:             Dimensions_cm       = Dimensions_cm(width=60, height=90)
    title_font_str:         str                 = "./fonts/Merriweather-Regular.ttf"
    book_font_str:          str                 = "./fonts/Lato-star.ttf"
    signature_font_str:     str                 = "./fonts/Lato-star.ttf"
    expected_cover_height:  int                 = 475 # px, common height of cover images on goodreads, used for dpi calculations
    default_aspect_ratio:   float               = .6555
    # Factors
    cover_dist_factor:            np.ndarray    = np.array([.01,.01])  # of cover width, height
    shading_factors:              np.ndarray    = 1 * np.array([.1,.05]) # of cover width, height
    shadow_factors:               np.ndarray    = np.array([.03,.06]) # of cover width, height
    min_margins_factor:           np.ndarray    = .01 * np.array([1,1,1]) # of poster height
    book_font_height_factor:      float         = 1/15. # of cover height
    book_font_vspace_factor:      float         = 1/4. # of font height
    title_font_height_factor:     float         = .02 # of poster height
    title_vspace_factor:          float         = .5 # of font height
    signature_height_factor:      float         = 1.2 # of title height
    signature_vspace_factor:      float         = .3 # of signature height
    signature_font_height_factor: float         = .35 # of signature height
    signature_hspace_factor:      float         = .35 # of signature height

    def __post_init__(self):
        # Ensures enough space between covers, so shading does not overlap
        self.cover_dist_factor      = np.maximum(self.cover_dist_factor, self.shading_factors*2)  # of cover width, height

@dataclass
class MergedDataclass():
    def __init__(self, dc1, dc2):
        for field in fields(dc1):
            setattr(self, field.name, getattr(dc1, field.name))
        for field in fields(dc2):
            setattr(self, field.name, getattr(dc2, field.name))

@dataclass
class PosterLayout:
    def __init__(self, initializer_dict, initializer_dataclass):
        for key in initializer_dict:
            setattr(self, key, initializer_dict[key])
        for field in fields(initializer_dataclass):
            setattr(self, field.name, getattr(initializer_dataclass, field.name))

    def get_text_width_px(self, text: str, font: ImageFont) -> int:
        dummy_poster = Image.new("RGB", (200,50), 'white')
        draw = ImageDraw.Draw(dummy_poster)
        _, _, text_w_px, _ = draw.textbbox((0, 0), text, font=font)
        return text_w_px

    def get_text_width(self, text: str, font: ImageFont) -> int:
        text_w_px = self.get_text_width_px(text, font)
        return Length(text_w_px, unit="px", dpi=self.dpi)

    def get_title_position(self) -> Position:
        # title_w = self.get_text_width(title, self.title_font) #not necessary with middle anchor
        return Position(self.poster_dim.width_px / 2., 
                        self.margins[TOP].px, unit="px", dpi=self.dpi)

    def get_shading_start_position(self, cover_index_H: int, cover_index_V: int) -> Position:
        cover_area_position = self.get_cover_area_position(cover_index_H, cover_index_V)
        return Position(
                cover_area_position.x_cm - self.shading.width_cm,
                # self.margins[SIDES].cm + cover_index_H * self.book_area.width_cm, # inferior alternative for horizontal position
                cover_area_position.y_cm - self.shading.height_cm,                
                # self.margins[TOP].cm + cover_index_V * self.book_area.height_cm + self.title_font_size.cm + self.title_vspace.cm + self.cover_dist.height_cm/4.,
                unit="cm", dpi=self.dpi)

    def get_shading_end_position(self, cover_index_H: int, cover_index_V: int) -> Position:
        cover_area_position = self.get_cover_area_position(cover_index_H, cover_index_V)
        text_position_last_line = self.get_cover_text_position(cover_index_H, cover_index_V, cover_text_lines=['' for i in range(self.number_of_text_lines)], line_index=self.number_of_text_lines-1)
        return Position(
                cover_area_position.x_cm + self.cover_area.width_cm + self.shading.width_cm,
                # self.margins[SIDES].cm + (cover_index_H + 1) * self.book_area.width_cm, # inferior alternative for horizontal position
                text_position_last_line.y_cm + self.book_font_size.cm + self.shading.height_cm,
                # self.margins[TOP].cm + self.title_font_size.cm + self.title_vspace.cm + (cover_index_V + 1) * self.book_area.height_cm + self.cover_dist.height_cm/4.,
                unit="cm", dpi=self.dpi)

    def get_cover_area_position(self, cover_index_H: int, cover_index_V: int) -> Position:
        return Position(self.margins[SIDES].cm + cover_index_H * self.book_area.width_cm + self.cover_dist.width_cm/2.,
                self.margins[TOP].cm + cover_index_V * self.book_area.height_cm + self.title_font_size.cm + self.title_vspace.cm + self.cover_dist.height_cm/2.,
                unit="cm", dpi=self.dpi)

    def get_cover_position(self, cover_index_H: int, cover_index_V: int, cover_size: Dimensions) -> Position:
        cover_area_position = self.get_cover_area_position(cover_index_H, cover_index_V)
        cover_offset = self.cover_area.add(cover_size.scale(-1)).scale(.5)
        return cover_area_position.add(cover_offset)

    def get_cover_text_position(self, cover_index_H: int, cover_index_V: int, cover_text_lines: list[str], line_index: int) -> Position:
        cover_position = self.get_cover_area_position(cover_index_H, cover_index_V)
        text_centering_offset = self.cover_area.width_cm / 2. #- self.get_text_width(cover_text_lines[line_index], self.book_font).cm / 2.
        return Position(cover_position.width_cm + text_centering_offset,
            cover_position.height_cm + self.cover_area.height_cm + (line_index + 1) * self.book_font_vspace.cm + line_index * self.book_font_size.cm,
                unit="cm", dpi=self.dpi)

    def get_signature_position_left(self) -> Position:
        return Position(self.margins[SIDES].cm, 
                self.poster_dim.height_cm - self.margins[BOTTOM].cm - self.signature_height.cm,
                unit="cm", dpi=self.dpi)

    def get_signature_position_right(self) -> Position:
        return Position(self.poster_dim.width_cm - self.margins[SIDES].cm - self.signature_height.cm, 
                self.poster_dim.height_cm - self.margins[BOTTOM].cm - self.signature_height.cm,
                unit="cm", dpi=self.dpi)
    
    def get_qr_code_size(self) -> Dimensions:
        return Dimensions.from_length(self.signature_height, self.signature_height)
    
    def get_signature_text_position_left(self) -> Position:
        sig_pos = self.get_signature_position_left()
        pos_x = sig_pos.x_cm + self.signature_height.cm + self.signature_hspace.cm
        pos_y = sig_pos.y_cm + self.signature_height.cm / 2.
        return Position(pos_x, pos_y, unit="cm", dpi=self.dpi)
    
    def get_signature_text_position_right(self) -> Position:
        sig_pos = self.get_signature_position_right()
        pos_x = sig_pos.x_cm - self.signature_hspace.cm
        pos_y = sig_pos.y_cm + self.signature_height.cm / 2.
        return Position(pos_x, pos_y, unit="cm", dpi=self.dpi)


class PosterLayoutFactory:
    '''Creates a PosterLayout object based on the parameters'''

    def __init__(self, params_public: PosterParametersPublic, params_private: PosterParametersPrivate) -> None:
        self.p_public = params_public 
        self.p = MergedDataclass(params_private, params_public)
        # Dictionary of calculated parameters
        self.out = dict()
    
    # def __post_init__(self):
        self.n_books_grid_total = np.prod(self.p.n_books_grid) 

        # Various dimensions based on cm parameters and factors
        min_margins                 = self.p.poster_dim.height * self.p.min_margins_factor # top, bottom, left&right
        title_font_height           = self.p.title_font_height_factor * self.p.poster_dim.height
        title_vspace                = self.p.title_vspace_factor * title_font_height
        signature_height            = self.p.signature_height_factor * title_font_height
        signature_vspace            = self.p.signature_vspace_factor * signature_height
        signature_font_height       = self.p.signature_font_height_factor * signature_height
        signature_hspace            = self.p.signature_hspace_factor * signature_height

        book_grid_area_height       = self.p.poster_dim.height - min_margins[TOP] - min_margins[BOTTOM] - title_vspace - signature_vspace - title_font_height - signature_height 
        book_grid_area_width        = self.p.poster_dim.width - 2*min_margins[SIDES]
        book_area_width             = book_grid_area_width / self.p.n_books_grid[H]
        book_area_height            = book_grid_area_height / self.p.n_books_grid[V]
        non_cover_height_factor     = self.p.number_of_text_lines * (self.p.book_font_height_factor * (1 + self.p.book_font_vspace_factor)) + self.p.cover_dist_factor[V]
        cover_area_width            = book_area_width / (1 + self.p.cover_dist_factor[H])
        cover_area_height           = book_area_height / (1 + non_cover_height_factor)
        current_aspect_ratio        = cover_area_width / cover_area_height

        # Leftover space is added to margins.
        # This changes the cover area and requires the updating of various values
        if current_aspect_ratio > self.p.default_aspect_ratio: # width changes
            cover_area_width        = cover_area_height * self.p.default_aspect_ratio
            book_area_width         = cover_area_width * (1 + self.p.cover_dist_factor[H])
            book_grid_area_width    = book_area_width * self.p.n_books_grid[H]
            min_margins[SIDES]      = (self.p.poster_dim.width - book_grid_area_width)/2.
        else: # height changes
            cover_area_height       = cover_area_width / self.p.default_aspect_ratio
            book_area_height        = cover_area_height * (1 + non_cover_height_factor)
            book_grid_area_height   = book_area_height * self.p.n_books_grid[V]
            margins_V_increment     = (self.p.poster_dim.height - book_grid_area_height - min_margins[TOP] - min_margins[BOTTOM])/2.
            min_margins[TOP]        += margins_V_increment
            min_margins[BOTTOM]     += margins_V_increment
        # Additional dimensions based on the new cover_area
        cover_dist_w                = self.p.cover_dist_factor[H] * cover_area_width
        cover_dist_h                = self.p.cover_dist_factor[V] * cover_area_height
        shading_w                   = self.p.shading_factors[H] * cover_area_width
        shading_h                   = self.p.shading_factors[V] * cover_area_height
        

        # Calculate dpi to match the expected cover resolution
        self.out["dpi"]                    = round(self.p.expected_cover_height/cover_area_height * 2.54)

        # Converting layout parameters into multi-unit data types (dpi-sensitive!)
        self.out["poster_dim"]             = Dimensions(self.p.poster_dim.width, self.p.poster_dim.height, unit="cm", dpi=self.dpi)
        self.out["margins"]                = [Length(m, unit="cm", dpi=self.dpi) for m in min_margins]
        self.out["book_grid_area"]         = Dimensions(book_grid_area_width, book_grid_area_height, unit="cm", dpi=self.dpi)
        self.out["book_area"]              = Dimensions(book_area_width, book_area_height, unit="cm", dpi=self.dpi)
        self.out["cover_area"]             = Dimensions(cover_area_width, cover_area_height, unit="cm", dpi=self.dpi)
        self.out["cover_dist"]             = Dimensions(cover_dist_w, cover_dist_h, unit="cm", dpi=self.dpi)
        self.out["shading"]                = Dimensions(shading_w, shading_h, unit="cm", dpi=self.dpi)
        self.out["book_font_size"]         = Length(self.p.book_font_height_factor * cover_area_height, unit="cm", dpi=self.dpi)
        self.out["book_font_vspace"]       = Length(self.p.book_font_vspace_factor * self.book_font_size.cm, unit="cm", dpi=self.dpi)
        self.out["title_vspace"]           = Length(title_vspace, unit="cm", dpi=self.dpi)
        self.out["title_font_size"]        = Length(title_font_height, unit="cm", dpi=self.dpi)
        self.out["signature_height"]       = Length(signature_height, unit="cm", dpi=self.dpi)  
        self.out["signature_font_size"]    = Length(signature_font_height, unit="cm", dpi=self.dpi)
        self.out["signature_vspace"]       = Length(signature_vspace, unit="cm", dpi=self.dpi)
        self.out["signature_hspace"]       = Length(signature_hspace, unit="cm", dpi=self.dpi)
        
        # Font creation (dpi-sensitive!)
        self.out["title_font"]             = ImageFont.truetype(self.p.title_font_str, size=self.title_font_size.px)
        self.out["book_font"]              = ImageFont.truetype(self.p.book_font_str, size=self.book_font_size.px)
        self.out["signature_font"]         = ImageFont.truetype(self.p.signature_font_str, size=self.signature_font_size.px)

    def get_poster_layout(self) -> PosterLayout:
        return PosterLayout(self.out, self.p_public)

def get_poster_layout():
    p_public = PosterParametersPublic()
    p_private = PosterParametersPrivate()
    factory = PosterLayoutFactory(p_public, p_private)
    return factory.get_poster_layout()

if __name__ == '__main__':
    from book_poster_creator import main
    main()
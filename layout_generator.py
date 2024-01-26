from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import NamedTuple, Literal
from datetime import datetime, timezone
from Dimensions_file import Dimensions, Dimensions_cm, Length, Position, Dimensions_px
from poster_config import Config

H = 0 # horizontal index
V = 1 # vertical intex

TOP = 0 # top margin index
BOTTOM = 1 # bottom margin index
SIDES = 2 # sides margin index



@dataclass
class PosterLayoutCreator:
    signature       = {}
    title           = {}
    year_shading    = {}
    poster          = {}
    grid            = {}
    book            = {}

    # Poster design parameters that are used externally unmodified
    config                                                  = Config()  
    poster['background_color_hex']:     str                 = "#FFFFFF"
    poster['dim']:                      Dimensions_cm       = Dimensions_cm(width=60, height=90)
    poster['min_margins_factor']                            = .01 * np.array([1,1,1]) # of poster height
    grid['n_books']:                    tuple[int,int]      = (8,8)
    grid['cover_dist_factor']                               = np.array([.01,.01])  # of cover width, height
    year_shading['enable']:             bool                = True
    year_shading['color1_hex']:         str                 = "#FFFFFF"
    year_shading['color2_hex']:         str                 = "#CCCCCC"
    year_shading['factors']                                 = 1 * np.array([.1,.05]) # of cover width, height
    book['rating_print']:               bool                = True
    book['default_aspect_ratio']:       float               = .6555
    book['font_str']:                   str                 = "./fonts/Lato-star.ttf"
    book['expected_cover_height']:      int                 = 475 # px, common height of cover images on goodreads, used for dpi calculations
    book['shadow_factors']                                  = np.array([.03,.06]) # of cover width, height
    book['font_height_factor']:         float               = 1/15. # of cover height
    book['font_vspace_factor']:         float               = 1/4. # of font height
    title['enable']:                    bool                = True
    title['font_str']:                  str                 = "./fonts/Merriweather-Regular.ttf"
    title['font_height_factor']:        float               = .02 # of poster height
    title['vspace_factor']:             float               = .5 # of font height
    signature['enable']:                bool                = True
    signature['font_str']:              str                 = "./fonts/Lato-star.ttf"
    signature['height_factor']:         float               = 1.2 # of title height
    signature['vspace_factor']:         float               = .3 # of signature height
    signature['font_height_factor']:    float               = .35 # of signature height
    signature['hspace_factor']:         float               = .35 # of signature height

    def __post_init__(self):
        # Ensures enough space between covers, so shading does not overlap
        self.grid['cover_dist_factor']      = np.maximum(self.grid['cover_dist_factor'], self.year_shading['factors'] * 2)  # of cover width, height
        self.book['number_of_text_lines']   = self.config.get_num_book_text_lines()
        # Various dimensions based on cm parameters and factors
        self.calculate_layout_parameters_from_factors()
        # Leftover space is added to margins.
        # This changes the cover area and requires the updating of various values
        self.update_cover_area()
        # Calculate dpi to match the expected cover resolution
        self.dpi                        = round(self.book['expected_cover_height']/self.book['cover_area_height'] * 2.54)
        # Converting layout parameters into multi-unit data types (dpi-sensitive!)
        self.convert_parameters_to_multiunit_format()

    def convert_parameters_to_multiunit_format(self):
        self.convert_poster_parameters_to_multiunit_format()
        self.convert_grid_parameters_to_multiunit_format()
        self.convert_book_parameters_to_multiunit_format()
        self.convert_year_shading_parameters_to_multiunit_format()
        self.convert_title_parameters_to_multiunit_format()
        self.convert_signature_parameters_to_multiunit_format()

    def convert_poster_parameters_to_multiunit_format(self):
        self.poster['dim']              = Dimensions(self.poster['dim'].width, self.poster['dim'].height, unit="cm", dpi=self.dpi)
        self.poster['margins']          = [Length(m, unit="cm", dpi=self.dpi) for m in self.poster['min_margins']]

    def convert_grid_parameters_to_multiunit_format(self):
        self.grid['area']               = Dimensions(self.book['grid_area_width'], self.book['grid_area_height'], unit="cm", dpi=self.dpi)
        cover_dist_w                    = self.grid['cover_dist_factor'][H] * self.book['cover_area_width']
        cover_dist_h                    = self.grid['cover_dist_factor'][V] * self.book['cover_area_height']
        self.grid['cover_dist']         = Dimensions(cover_dist_w, cover_dist_h, unit="cm", dpi=self.dpi)

    def convert_book_parameters_to_multiunit_format(self):
        self.book['area']               = Dimensions(self.book['area_width'], self.book['area_height'], unit="cm", dpi=self.dpi)
        self.book['cover_area']         = Dimensions(self.book['cover_area_width'], self.book['cover_area_height'], unit="cm", dpi=self.dpi)
        self.book['font_size']          = Length(self.book['font_height_factor'] * self.book['cover_area_height'], unit="cm", dpi=self.dpi)
        self.book['font_vspace']        = Length(self.book['font_vspace_factor'] * self.book['font_size'].cm, unit="cm", dpi=self.dpi)
        self.book['font']               = ImageFont.truetype(self.book['font_str'], size=self.book['font_size'].px)

    def convert_year_shading_parameters_to_multiunit_format(self):
        shading_w                       = self.year_shading['factors'][H] * self.book['cover_area_width']
        shading_h                       = self.year_shading['factors'][V] * self.book['cover_area_height']
        self.year_shading['protrusion']        = Dimensions(shading_w, shading_h, unit="cm", dpi=self.dpi)

    def convert_title_parameters_to_multiunit_format(self):
        self.title['vspace']            = Length(self.title['vspace'], unit="cm", dpi=self.dpi)
        self.title['font_size']         = Length(self.title['font_height'], unit="cm", dpi=self.dpi)
        self.title['font']              = ImageFont.truetype(self.title['font_str'], size=self.title['font_size'].px)

    def convert_signature_parameters_to_multiunit_format(self):
        self.signature['height']        = Length(self.signature['height'], unit="cm", dpi=self.dpi)  
        self.signature['font_size']     = Length(self.signature['font_height'], unit="cm", dpi=self.dpi)
        self.signature['vspace']        = Length(self.signature['vspace'], unit="cm", dpi=self.dpi)
        self.signature['hspace']        = Length(self.signature['hspace'], unit="cm", dpi=self.dpi)
        self.signature['font']          = ImageFont.truetype(self.signature['font_str'], size=self.signature['font_size'].px)

    def calculate_layout_parameters_from_factors(self):
        self.poster['min_margins']          = self.poster['dim'].height * self.poster['min_margins_factor'] # top, bottom, left&right
        self.calculate_title_parameters_from_factors()
        self.calculate_signature_parameters_from_factors()
        self.calculate_book_parameters_from_factors()

    def calculate_title_parameters_from_factors(self):
        self.title['font_height']           = self.title['font_height_factor'] * self.poster['dim'].height
        self.title['vspace']                = self.title['vspace_factor'] * self.title['font_height']

    def calculate_signature_parameters_from_factors(self):
        self.signature['height']            = self.signature['height_factor'] * self.title['font_height']
        self.signature['vspace']            = self.signature['vspace_factor'] * self.signature['height']
        self.signature['font_height']       = self.signature['font_height_factor'] * self.signature['height']
        self.signature['hspace']            = self.signature['hspace_factor'] * self.signature['height']

    def calculate_book_parameters_from_factors(self):
        self.book['grid_area_height']       = self.poster['dim'].height - self.poster['min_margins'][TOP] - self.poster['min_margins'][BOTTOM] - self.title['vspace'] - self.signature['vspace'] - self.title['font_height'] - self.signature['height'] 
        self.book['grid_area_width']        = self.poster['dim'].width - 2*self.poster['min_margins'][SIDES]
        self.book['area_width']             = self.book['grid_area_width'] / self.grid['n_books'][H]
        self.book['area_height']            = self.book['grid_area_height'] / self.grid['n_books'][V]
        self.compute_book_area()
        self.book['current_aspect_ratio']   = self.book['cover_area_width'] / self.book['cover_area_height']

    def compute_book_area(self, which: Literal['width', 'height', 'both'] = 'both'):
        if which in ['width', 'both']:
            self.book['cover_area_width']       = self.book['area_width'] / (1 + self.grid['cover_dist_factor'][H])
        if which in ['height', 'both']:
            self.book['cover_area_height']      = self.book['area_height'] / (1 + self.get_non_cover_height_factor())

    def get_non_cover_height_factor(self):
        return self.book['font_height_factor'] * (self.book['number_of_text_lines'] + self.book['font_vspace_factor']) \
            + self.grid['cover_dist_factor'][V]

    def update_cover_area(self):
        if self.book['current_aspect_ratio'] > self.book['default_aspect_ratio']: # width changes
            self.update_cover_area_width_and_dependents()
        else: # height changes
            self.update_cover_area_height_and_dependents()

    def update_cover_area_width_and_dependents(self):
        self.book['cover_area_width']       = self.book['cover_area_height'] * self.book['default_aspect_ratio']
        self.compute_book_area('width')
        self.book['grid_area_width']        = self.book['area_width'] * self.grid['n_books'][H]
        self.poster['min_margins'][SIDES]   = (self.poster['dim'].width - self.book['grid_area_width'])/2.

    def update_cover_area_height_and_dependents(self):
        self.book['cover_area_height']      = self.book['cover_area_width'] / self.book['default_aspect_ratio']
        self.compute_book_area('height')
        self.book['grid_area_height']       = self.book['area_height'] * self.grid['n_books'][V]
        margins_V_increment                 = (self.poster['dim'].height - self.book['grid_area_height'] - self.poster['min_margins'][TOP] - self.poster['min_margins'][BOTTOM])/2.
        self.poster['min_margins'][TOP]    += margins_V_increment
        self.poster['min_margins'][BOTTOM] += margins_V_increment

    def create_poster_layout(self):
        return PosterLayout(      
            poster                  = self.create_poster_parameter_obj(),
            grid                    = self.create_grid_parameter_obj(),
            year_shading            = self.create_year_shading_parameter_obj(),
            book                    = self.create_book_parameter_obj(),
            title                   = self.create_title_parameter_obj(),
            signature               = self.create_signature_parameter_obj(),
            dpi                     = self.dpi)

    def create_poster_parameter_obj(self):
        return PosterParameters(
            background_color_hex    = self.poster['background_color_hex'],
            dim                     = self.poster['dim'],              
            margins                 = self.poster['margins'])

    def create_grid_parameter_obj(self):
        return GridParameters(
            n_books                 = self.grid['n_books'],
            area                    = self.grid['area'],   
            cover_dist              = self.grid['cover_dist'])

    def create_year_shading_parameter_obj(self):
        return YearShadingParameters(
            enable      = self.year_shading['enable'],
            color1_hex  = self.year_shading['color1_hex'],
            color2_hex  = self.year_shading['color2_hex'],
            protrusion  = self.year_shading['protrusion'])

    def create_book_parameter_obj(self):
        return BookParameters(
            rating_print            = self.book['rating_print'],                    
            default_aspect_ratio    = self.book['default_aspect_ratio'],                    
            area                    = self.book['area'],                  
            cover_area              = self.book['cover_area'],    
            font_vspace             = self.book['font_vspace'],               
            font                    = self.book['font'],               
            number_of_text_lines    = self.book['number_of_text_lines'])

    def create_title_parameter_obj(self):
        return TitleParameters(
            enable  = self.title['enable'],
            font    = self.title['font'],
            vspace  = self.title['vspace'])

    def create_signature_parameter_obj(self):
        return SignatureParameters(
            enable  = self.signature['enable'],
            font    = self.signature['font'],
            vspace  = self.signature['vspace'],
            hspace  = self.signature['hspace'],
            height  = self.signature['height'])
    
@dataclass
class PosterLayout:     
    poster       : PosterParameters
    grid         : GridParameters
    year_shading : YearShadingParameters
    book         : BookParameters
    title        : TitleParameters
    signature    : SignatureParameters
    dpi          : int

    @property
    def book_font_size(self) -> Length:
        return Length(self.book.font.size, unit="px", dpi=self.dpi)
    @property
    def title_font_size(self) -> Length:
        return Length(self.title.font.size, unit="px", dpi=self.dpi)
    @property
    def signature_font_size(self) -> Length:
        return Length(self.signature.font.size, unit="px", dpi=self.dpi)

    # def __post_init__(self):
    #     poster_area = Area(self.poster.dim.dim_px)
    #     marginless_area_dim = Dimensions_px(self.poster.dim.width_px - self.poster.margins[SIDES].px * 2, self.poster.dim.height_px - self.poster.margins[TOP].px * 2)
    #     marginless_area = Area(container=poster_area, offset=Dimensions_px(self.poster.margins[SIDES].px, self.poster.margins[TOP].px), dimensions=marginless_area_dim)
    #     # book_grid_area = Area(container=marginless_area, offset=(0,title_font.))
    #     # title_area = 
    
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
        return Position(self.poster.dim.width_px / 2., 
                        self.poster.margins[TOP].px, unit="px", dpi=self.dpi)

    def get_shading_start_position(self, cover_index_H: int, cover_index_V: int) -> Position:
        cover_area_position = self.get_cover_area_position(cover_index_H, cover_index_V)
        return Position(
                cover_area_position.x_cm - self.year_shading.protrusion.width_cm,
                # self.margins[SIDES].cm + cover_index_H * self.book_area.width_cm, # inferior alternative for horizontal position
                cover_area_position.y_cm - self.year_shading.protrusion.height_cm,                
                # self.margins[TOP].cm + cover_index_V * self.book_area.height_cm + self.title_font_size.cm + self.title_vspace.cm + self.cover_dist.height_cm/4.,
                unit="cm", dpi=self.dpi)

    def get_shading_end_position(self, cover_index_H: int, cover_index_V: int) -> Position:
        cover_area_position = self.get_cover_area_position(cover_index_H, cover_index_V)
        # text_position_last_line = self.get_cover_text_position(cover_index_H, cover_index_V, cover_text_lines=['' for i in range(self.book.number_of_text_lines)], line_index=self.book.number_of_text_lines-1)
        return Position(
                cover_area_position.x_cm + self.book.cover_area.width_cm + self.year_shading.protrusion.width_cm,
                # self.margins[SIDES].cm + (cover_index_H + 1) * self.book_area.width_cm, # inferior alternative for horizontal position
                cover_area_position.y_cm + self.book.area.height_cm - self.grid.cover_dist.height_cm + self.year_shading.protrusion.height_cm,
                # text_position_last_line.y_cm + self.book_font_size.cm + self.shading.height_cm,
                # self.margins[TOP].cm + self.title_font_size.cm + self.title_vspace.cm + (cover_index_V + 1) * self.book_area.height_cm + self.cover_dist.height_cm/4.,
                unit="cm", dpi=self.dpi)

    def get_cover_area_position(self, cover_index_H: int, cover_index_V: int) -> Position:
        return Position(self.poster.margins[SIDES].cm + cover_index_H * self.book.area.width_cm + self.grid.cover_dist.width_cm/2.,
                self.poster.margins[TOP].cm + cover_index_V * self.book.area.height_cm + self.title_font_size.cm + self.title.vspace.cm + self.grid.cover_dist.height_cm/2.,
                unit="cm", dpi=self.dpi)

    def get_cover_position(self, cover_index_H: int, cover_index_V: int, cover_size: Dimensions) -> Position:
        cover_area_position = self.get_cover_area_position(cover_index_H, cover_index_V)
        cover_offset = self.book.cover_area.add(cover_size.scale(-1)).scale(.5)
        return cover_area_position.add(cover_offset)

    def get_cover_text_position(self, cover_index_H: int, cover_index_V: int, cover_text_lines: list[str], line_index: int) -> Position:
        cover_position = self.get_cover_area_position(cover_index_H, cover_index_V)
        text_centering_offset = self.book.cover_area.width_cm / 2. #- self.get_text_width(cover_text_lines[line_index], self.book_font).cm / 2.
        return Position(cover_position.width_cm + text_centering_offset,
            cover_position.height_cm + self.book.cover_area.height_cm + (line_index + 1) * self.book.font_vspace.cm + line_index * self.book_font_size.cm,
                unit="cm", dpi=self.dpi)

    def get_signature_position_left(self) -> Position:
        return Position(self.poster.margins[SIDES].cm, 
                self.poster.dim.height_cm - self.poster.margins[BOTTOM].cm - self.signature.height.cm,
                unit="cm", dpi=self.dpi)

    def get_signature_position_right(self) -> Position:
        return Position(self.poster.dim.width_cm - self.poster.margins[SIDES].cm - self.signature.height.cm, 
                self.poster.dim.height_cm - self.poster.margins[BOTTOM].cm - self.signature.height.cm,
                unit="cm", dpi=self.dpi)
    
    def get_qr_code_size(self) -> Dimensions:
        return Dimensions.from_length(self.signature.height, self.signature.height)
    
    def get_signature_text_position_left(self) -> Position:
        sig_pos = self.get_signature_position_left()
        pos_x = sig_pos.x_cm + self.signature.height.cm + self.signature.hspace.cm
        pos_y = sig_pos.y_cm + self.signature.height.cm / 2.
        return Position(pos_x, pos_y, unit="cm", dpi=self.dpi)
    
    def get_signature_text_position_right(self) -> Position:
        sig_pos = self.get_signature_position_right()
        pos_x = sig_pos.x_cm - self.signature.hspace.cm
        pos_y = sig_pos.y_cm + self.signature.height.cm / 2.
        return Position(pos_x, pos_y, unit="cm", dpi=self.dpi)
    
@dataclass
class PosterParameters:
    background_color_hex:   str
    dim:                    Dimensions
    margins:                list[Length]

@dataclass
class GridParameters:
    n_books:                tuple[int, int]
    area:                   Dimensions
    cover_dist:             Length
    @property
    def n_books_total(self):
        return self.n_books[0] * self.n_books[1]

@dataclass
class BookParameters:
    rating_print:           bool
    default_aspect_ratio:   float
    area:                   Dimensions
    cover_area:             Dimensions
    font_vspace:            Length
    font:                   ImageFont
    number_of_text_lines:   int

@dataclass
class YearShadingParameters:
    enable:                 bool      
    color1_hex:             str       
    color2_hex:             str       
    protrusion:             Dimensions

@dataclass
class TitleParameters:
    enable:                 bool      
    font:                   ImageFont
    vspace:                 Length
    @property
    def font_size(self):
        return Length(self.font.size, unit="px", dpi=self.vspace.dpi)

@dataclass
class SignatureParameters:
    enable:                 bool      
    font:                   ImageFont
    vspace:                 Length
    hspace:                 Length
    height:                 Length
    @property
    def font_size(self):
        return Length(self.font.size, unit="px", dpi=self.vspace.dpi)
    
# class Area:
#     # content: list[Area] = list()
#     content = {}
#     def __init__(self, container: Area = None, offset: Dimensions_px = (0,0), dimensions: Dimensions_px = (0,0)):
#         self.offset = offset
#         self.dimensions = dimensions
#         self.position = None
    
#     # def add_content(self, new_content):
#     #     self.content.append(new_content)
#     #     self._update_content_positions()
        
#     def add_content(self, identifier: str, new_content):
#         self.content[identifier] = new_content
#         self.content[identifier].calculate_position(self.position)
#         # self._update_content_positions()
    
#     def via_position(self, position: Position, dimensions: Dimensions):
#         assert position.dpi == dimensions.dpi, "DPI mismatch!"
#         self.offset = Dimensions(0,0, unit="cm", dpi=self._dpi)
#         self.position = position
#         self.dimensions = dimensions
    
#     def _update_content_positions(self):
#         for c in self.content:
#             c.calculate_position(self.position)
    
#     def calculate_position(self, container_position: Position):
#         self.position = container_position.add(self.offset)
    
#     def draw_outline(self, draw: ImageDraw, outline_width: int = 1):
#         draw.rectangle([self.position.xy_px, self.dimensions.dim_px], fill=None, width=outline_width, outline="black")

#     def get_position_of(self, vertical_pos: Literal['top', 'middle', 'bottom'], horizontal_pos: Literal['left', 'middle', 'right']):
#         if self.position is None:
#             raise ValueError("Position not set!")
#         if vertical_pos == 'top':
#             vertical_offset = 0
#         elif vertical_pos =='middle':
#             vertical_offset = self.dimensions.height_cm / 2
#         elif vertical_pos == 'bottom':
#             vertical_offset = self.dimensions.height_cm
#         else:
#             raise ValueError("Vertical position not recognized!")
#         if horizontal_pos == 'left':
#             horizontal_offset = 0
#         elif horizontal_pos =='middle':
#             horizontal_offset = self.dimensions.width_cm / 2
#         elif horizontal_pos == 'right':
#             horizontal_offset = self.dimensions.width_cm
#         else:
#             raise ValueError("Horizontal position not recognized!")
#         return self.position.add(Dimensions(horizontal_offset, vertical_offset, unit="cm", dpi=self.dimensions.dpi))
    

if __name__ == '__main__':
    from book_poster_creator import main
    main()
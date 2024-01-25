from dataclasses import dataclass
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import NamedTuple
from datetime import datetime, timezone
from Dimensions_file import Dimensions, Dimensions_cm, Length, Position
from poster_config import Config

H = 0 # horizontal index
V = 1 # vertical intex

TOP = 0 # top margin index
BOTTOM = 1 # bottom margin index
SIDES = 2 # sides margin index

class Area:
    content = list()
    def __init__(self, position: Position, dimensions: Dimensions):
        self.position = position
        self.dimensions = dimensions


# @dataclass
# class YearShadingParameters:
#     do_it:      bool      
#     color1_hex: str       
#     color2_hex: str       
#     protrusion: Dimensions

# @dataclass
# class TiteParameters:
#     do_it:      bool      
#     vspace:     Length       
#     font_size:  Length
#     font:       ImageFont
#     _dpi:       int
#     @property
#     def font_size(self):
#         return Length(self.font.size, unit="px", dpi=self._dpi)

@dataclass
class PosterLayoutCreator:

    # Poster design parameters that are used externally unmodified
    background_color_hex:   str                 = "#FFFFFF"
    year_shading:           bool                = True
    year_shading_color1_hex:str                 = "#FFFFFF"
    year_shading_color2_hex:str                 = "#CCCCCC"
    print_rating:           bool                = True
    print_title:            bool                = True
    print_signature:        bool                = True
    n_books_grid:           tuple[int,int]      = (8,8)
    default_aspect_ratio:   float               = .6555

    def __post_init__(self):
        # Internal only!
        poster_dim:             Dimensions_cm       = Dimensions_cm(width=60, height=90)
        title_font_str:         str                 = "./fonts/Merriweather-Regular.ttf"
        book_font_str:          str                 = "./fonts/Lato-star.ttf"
        signature_font_str:     str                 = "./fonts/Lato-star.ttf"
        expected_cover_height:  int                 = 475 # px, common height of cover images on goodreads, used for dpi calculations
        config:                 Config              = Config()  

        # Factors
        cover_dist_factor                           = np.array([.01,.01])  # of cover width, height
        shading_factors                             = 1 * np.array([.1,.05]) # of cover width, height
        shadow_factors                              = np.array([.03,.06]) # of cover width, height
        min_margins_factor                          = .01 * np.array([1,1,1]) # of poster height
        book_font_height_factor:      float         = 1/15. # of cover height
        book_font_vspace_factor:      float         = 1/4. # of font height
        title_font_height_factor:     float         = .02 # of poster height
        title_vspace_factor:          float         = .5 # of font height
        signature_height_factor:      float         = 1.2 # of title height
        signature_vspace_factor:      float         = .3 # of signature height
        signature_font_height_factor: float         = .35 # of signature height
        signature_hspace_factor:      float         = .35 # of signature height

        # Ensures enough space between covers, so shading does not overlap
        cover_dist_factor      = np.maximum(cover_dist_factor, shading_factors * 2)  # of cover width, height

        
        self.number_of_text_lines = config.get_num_book_text_lines()
        
        # Various dimensions based on cm parameters and factors
        min_margins                 = poster_dim.height * min_margins_factor # top, bottom, left&right
        title_font_height           = title_font_height_factor * poster_dim.height
        title_vspace                = title_vspace_factor * title_font_height
        signature_height            = signature_height_factor * title_font_height
        signature_vspace            = signature_vspace_factor * signature_height
        signature_font_height       = signature_font_height_factor * signature_height
        signature_hspace            = signature_hspace_factor * signature_height

        book_grid_area_height       = poster_dim.height - min_margins[TOP] - min_margins[BOTTOM] - title_vspace - signature_vspace - title_font_height - signature_height 
        book_grid_area_width        = poster_dim.width - 2*min_margins[SIDES]
        book_area_width             = book_grid_area_width / self.n_books_grid[H]
        book_area_height            = book_grid_area_height / self.n_books_grid[V]
        # non_cover_height_factor     = self.number_of_text_lines * (book_font_height_factor * (1 + book_font_vspace_factor)) + cover_dist_factor[V]
        non_cover_height_factor     = (self.number_of_text_lines + book_font_vspace_factor) * book_font_height_factor + cover_dist_factor[V]
        cover_area_width            = book_area_width / (1 + cover_dist_factor[H])
        cover_area_height           = book_area_height / (1 + non_cover_height_factor)
        current_aspect_ratio        = cover_area_width / cover_area_height

        # Leftover space is added to margins.
        # This changes the cover area and requires the updating of various values
        if current_aspect_ratio > self.default_aspect_ratio: # width changes
            cover_area_width        = cover_area_height * self.default_aspect_ratio
            book_area_width         = cover_area_width * (1 + cover_dist_factor[H])
            book_grid_area_width    = book_area_width * self.n_books_grid[H]
            min_margins[SIDES]      = (poster_dim.width - book_grid_area_width)/2.
        else: # height changes
            cover_area_height       = cover_area_width / self.default_aspect_ratio
            book_area_height        = cover_area_height * (1 + non_cover_height_factor)
            book_grid_area_height   = book_area_height * self.n_books_grid[V]
            margins_V_increment     = (poster_dim.height - book_grid_area_height - min_margins[TOP] - min_margins[BOTTOM])/2.
            min_margins[TOP]        += margins_V_increment
            min_margins[BOTTOM]     += margins_V_increment
        # Additional dimensions based on the new cover_area
        cover_dist_w                = cover_dist_factor[H] * cover_area_width
        cover_dist_h                = cover_dist_factor[V] * cover_area_height
        shading_w                   = shading_factors[H] * cover_area_width
        shading_h                   = shading_factors[V] * cover_area_height


        # Calculate dpi to match the expected cover resolution
        self.dpi                    = round(expected_cover_height/cover_area_height * 2.54)

        # Converting layout parameters into multi-unit data types (dpi-sensitive!)
        self.poster_dim             = Dimensions(poster_dim.width, poster_dim.height, unit="cm", dpi=self.dpi)
        self.margins                = [Length(m, unit="cm", dpi=self.dpi) for m in min_margins]
        self.book_grid_area         = Dimensions(book_grid_area_width, book_grid_area_height, unit="cm", dpi=self.dpi)
        self.book_area              = Dimensions(book_area_width, book_area_height, unit="cm", dpi=self.dpi)
        self.cover_area             = Dimensions(cover_area_width, cover_area_height, unit="cm", dpi=self.dpi)
        self.cover_dist             = Dimensions(cover_dist_w, cover_dist_h, unit="cm", dpi=self.dpi)
        self.shading                = Dimensions(shading_w, shading_h, unit="cm", dpi=self.dpi)
        self.book_font_size         = Length(book_font_height_factor * cover_area_height, unit="cm", dpi=self.dpi)
        self.book_font_vspace       = Length(book_font_vspace_factor * self.book_font_size.cm, unit="cm", dpi=self.dpi)
        self.title_vspace           = Length(title_vspace, unit="cm", dpi=self.dpi)
        title_font_size        = Length(title_font_height, unit="cm", dpi=self.dpi)
        self.signature_height       = Length(signature_height, unit="cm", dpi=self.dpi)  
        signature_font_size    = Length(signature_font_height, unit="cm", dpi=self.dpi)
        self.signature_vspace       = Length(signature_vspace, unit="cm", dpi=self.dpi)
        self.signature_hspace       = Length(signature_hspace, unit="cm", dpi=self.dpi)
        
        # Font creation (dpi-sensitive!)
        self.title_font             = ImageFont.truetype(title_font_str, size=title_font_size.px)
        self.book_font              = ImageFont.truetype(book_font_str, size=self.book_font_size.px)
        self.signature_font         = ImageFont.truetype(signature_font_str, size=signature_font_size.px)

    def create_poster_layout(self):
        return PosterLayout(      
            background_color_hex    = self.background_color_hex,    
            year_shading            = self.year_shading,            
            year_shading_color1_hex = self.year_shading_color1_hex, 
            year_shading_color2_hex = self.year_shading_color2_hex, 
            print_rating            = self.print_rating,            
            print_title             = self.print_title,             
            print_signature         = self.print_signature,         
            n_books_grid            = self.n_books_grid,            
            default_aspect_ratio    = self.default_aspect_ratio,     
            dpi                     = self.dpi,                     
            poster_dim              = self.poster_dim,              
            margins                 = self.margins,                 
            book_grid_area          = self.book_grid_area,          
            book_area               = self.book_area,               
            cover_area              = self.cover_area,              
            cover_dist              = self.cover_dist,              
            shading                 = self.shading,                 
            book_font_vspace        = self.book_font_vspace,        
            title_vspace            = self.title_vspace,             
            signature_height        = self.signature_height,        
            signature_vspace        = self.signature_vspace,        
            signature_hspace        = self.signature_hspace,        
            title_font              = self.title_font,              
            book_font               = self.book_font,               
            signature_font          = self.signature_font,          
            number_of_text_lines    = self.number_of_text_lines,
        )

@dataclass
class PosterLayout:     
    background_color_hex:   str           
    year_shading:           bool          
    year_shading_color1_hex:str           
    year_shading_color2_hex:str           
    print_rating:           bool          
    print_title:            bool          
    print_signature:        bool          
    n_books_grid:           tuple[int,int]
    default_aspect_ratio:   float         
    dpi:                    int
    poster_dim:             Dimensions
    margins:                list[Length]
    book_grid_area:         Dimensions
    book_area:              Dimensions
    cover_area:             Dimensions
    cover_dist:             Dimensions
    shading:                Dimensions
    book_font_vspace:       Length
    title_vspace:           Length
    signature_height:       Length
    signature_vspace:       Length
    signature_hspace:       Length
    title_font:             ImageFont
    book_font:              ImageFont
    signature_font:         ImageFont
    number_of_text_lines:   int           

    @property
    def n_books_grid_total(self) -> int:
        return np.prod(self.n_books_grid)
    @property
    def book_font_size(self) -> Length:
        return Length(self.book_font.size, unit="px", dpi=self.dpi)
    @property
    def title_font_size(self) -> Length:
        return Length(self.title_font.size, unit="px", dpi=self.dpi)
    @property
    def signature_font_size(self) -> Length:
        return Length(self.signature_font.size, unit="px", dpi=self.dpi)

    
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
                cover_area_position.y_cm + self.book_area.height_cm - self.cover_dist.height_cm + self.shading.height_cm,
                # text_position_last_line.y_cm + self.book_font_size.cm + self.shading.height_cm,
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


if __name__ == '__main__':
    from book_poster_creator import main
    main()
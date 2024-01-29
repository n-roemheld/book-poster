# Unused and unfinished code for a new layout generator based on nested area objects

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from PIL import ImageDraw
from typing import Literal
from Dimensions_file import Dimensions, Position, Dimensions_px
import layout_generator as lg

H = 0 # horizontal index
V = 1 # vertical intex

TOP = 0 # top margin index
BOTTOM = 1 # bottom margin index
SIDES = 2 # sides margin index

class Area:
    # content: list[Area] = list()
    content = {}
    def __init__(self, container: Area = None, offset: Dimensions_px = (0,0), dimensions: Dimensions_px = (0,0)):
        self.offset = offset
        self.dimensions = dimensions
        self.position = None
    
    # def add_content(self, new_content):
    #     self.content.append(new_content)
    #     self._update_content_positions()
        
    def add_content(self, identifier: str, new_content):
        self.content[identifier] = new_content
        self.content[identifier].calculate_position(self.position)
        # self._update_content_positions()
    
    def via_position(self, position: Position, dimensions: Dimensions):
        assert position.dpi == dimensions.dpi, "DPI mismatch!"
        self.offset = Dimensions(0,0, unit="cm", dpi=self._dpi)
        self.position = position
        self.dimensions = dimensions
    
    def _update_content_positions(self):
        for c in self.content:
            c.calculate_position(self.position)
    
    def calculate_position(self, container_position: Position):
        self.position = container_position.add(self.offset)
    
    def draw_outline(self, draw: ImageDraw, outline_width: int = 1):
        draw.rectangle([self.position.xy_px, self.dimensions.dim_px], fill=None, width=outline_width, outline="black")

    def get_position_of(self, vertical_pos: Literal['top', 'middle', 'bottom'], horizontal_pos: Literal['left', 'middle', 'right']):
        if self.position is None:
            raise ValueError("Position not set!")
        if vertical_pos == 'top':
            vertical_offset = 0
        elif vertical_pos =='middle':
            vertical_offset = self.dimensions.height_cm / 2
        elif vertical_pos == 'bottom':
            vertical_offset = self.dimensions.height_cm
        else:
            raise ValueError("Vertical position not recognized!")
        if horizontal_pos == 'left':
            horizontal_offset = 0
        elif horizontal_pos =='middle':
            horizontal_offset = self.dimensions.width_cm / 2
        elif horizontal_pos == 'right':
            horizontal_offset = self.dimensions.width_cm
        else:
            raise ValueError("Horizontal position not recognized!")
        return self.position.add(Dimensions(horizontal_offset, vertical_offset, unit="cm", dpi=self.dimensions.dpi))
    

        
@dataclass
class PosterLayout:     
    poster       : lg.PosterParameters
    grid         : lg.GridParameters
    year_shading : lg.YearShadingParameters
    book         : lg.BookParameters
    title        : lg.TitleParameters
    signature    : lg.SignatureParameters
    dpi          : int

    def __post_init__(self):
        poster_area = Area(self.poster.dim.dim_px)
        marginless_area_dim = Dimensions_px(self.poster.dim.width_px - self.poster.margins[SIDES].px * 2, self.poster.dim.height_px - self.poster.margins[TOP].px * 2)
        marginless_area = Area(container=poster_area, offset=Dimensions_px(self.poster.margins[SIDES].px, self.poster.margins[TOP].px), dimensions=marginless_area_dim)
        # book_grid_area = Area(container=marginless_area, offset=(0,title_font.))
    #     # title_area = 
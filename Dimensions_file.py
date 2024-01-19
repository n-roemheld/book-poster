from typing import Any, NamedTuple

INCH_IN_CM = 2.54

class Length: 
    '''Class for handling lengths in pixels and cm'''
    # length_px : Dimensions_pixel = (0,0)
    # length_cm : Dimensions_cm = (0.,0.)
    def __init__(self, length_in: float, unit: str = 'px', dpi: int = 208) -> None:
        self.dpi = dpi
        cm_to_pixel_factor = dpi / INCH_IN_CM
        if unit == 'px':
            self.px = round(length_in)
            self.cm = length_in / cm_to_pixel_factor
        elif unit == 'cm':
            self.cm = length_in 
            self.px = round(length_in * cm_to_pixel_factor)
        else:
            raise ValueError(f'Unknown unit {unit}')
    
    # def as_cm(self) -> float:
    #     return self.length_cm
    
    # def as_px(self) -> int:
    #     return self.length_px
        
class Dimensions_pixel(NamedTuple):
    width: int
    height: int

class Dimensions_cm(NamedTuple):
    width: float
    height: float

class Dimensions: 
    '''Class for handling dimensions in pixels and cm'''
    # dim_px : Dimensions_pixel = (0,0)
    # dim_cm : Dimensions_cm = (0.,0.)
    def __init__(self, width: float, height: float, unit: str = 'px', dpi: int = 208) -> None:
        self.dpi = dpi
        cm_to_pixel_factor = dpi / INCH_IN_CM
        if unit == 'px':
            self.dim_px = Dimensions_pixel(width, height)
            self.dim_cm = Dimensions_cm(width/cm_to_pixel_factor, height/cm_to_pixel_factor)
        elif unit == 'cm':
            self.dim_cm = Dimensions_cm(width, height)
            self.dim_px = Dimensions_pixel(int(width*cm_to_pixel_factor), int(height*cm_to_pixel_factor))
        else:
            raise ValueError(f'Unknown unit {unit}')
    
    # def __init__(self, width: Length, height: Length) -> None:
    #     assert width.dpi == height.dpi, 'DPI mismatch'
    #     self.__init__(width=width.cm, height=height.cm, lunit='cm', dpi=width.dpi)
    
    def get_dim_in_px(self) -> Dimensions_pixel:
        return self.dim_px # pointer problem?
    
    def get_dim_in_cm(self) -> Dimensions_cm:
        return self.dim_cm # pointer problem?
    
    def width_px(self) -> int:
        return self.dim_px.width
    
    def width_cm(self) -> int:
        return self.dim_cm.width
    
    def height_px(self) -> int:
        return self.dim_px.height
    
    def height_cm(self) -> int:
        return self.dim_cm.height
    
    def add(self, other: 'Dimensions') -> 'Dimensions':
        assert self.dpi == other.dpi, 'DPI mismatch'
        return Dimensions(self.width_cm() + other.width_cm(), self.height_cm() + other.height_cm(), unit='cm', dpi=self.dpi)
    
    def scale(self, factor: float) -> 'Dimensions':
        return Dimensions(self.width_cm() * factor, self.height_cm() * factor, unit='cm', dpi=self.dpi)

class Position (Dimensions):
    def x_px(self):
        return super().width_px()
    def y_px(self):
        return super().height_px()
    def x_cm(self):
        return super().width_cm()
    def y_cm(self):
        return super().height_cm()
    def xy_px(self):
        return super().get_dim_in_px()
    def xy_cm(self):
        return super().get_dim_in_cm()


## Poster layout parameters
# Image DPI determines resolution and file size
dpi:                    int = 208
# Poster size in cm (horizontal, vertical)
poster_size_cm:         tuple[float,float] = (60,90)
# (Minimum) distance between the book covers in cm (horizontal, vertical)
min_distance_cm:        tuple[float,float] = (.8,1.6)#(.6,1)
# (Maximum) height of the book covers. 
max_cover_height_cm:    float = 9#6.3
# The (maximum) width of the covers is determined by the default_aspect_ratio
default_aspect_ratio:   float = .6555 # Should be a good value. It is the median of a large set of book covers.
# Additional empty space at the top of the poster
title_height_cm:        float = 0 
# Filename of the poster image
output_file:            str = "poster.jpg"
# Font for the read date. UTF-8 fonts recommended.
font_str:               str = "./DejaVuSans.ttf"
# Poster background color
background_color_hex:   str = "#FFFFFF"
# Enable or disable the shading of books read within the same year
year_shading:           bool = True
year_shading_color1_hex:str = "#DDDDDD"
year_shading_color2_hex:str = "#BBBBBB"
# Controls the width of the separator line in the book grid. Factor of the max cover width.
separator_width_factor: float = 1/40.

# Start date
# Only books read after this date are included  
startdate_year:         int = 2022 #2015
startdate_month:        int = 1#7
startdate_day:          int = 1#27
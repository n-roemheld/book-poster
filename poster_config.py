from datetime import datetime, timezone
from dataclasses import dataclass
import numpy as np
from Dimensions_file import Dimensions_cm

@ dataclass 
class Config():
    DEFAULT_READ_DATE = datetime(year=1900, month=1, day=1, tzinfo=timezone.utc)

    input_rss_file:         str                 = "rss_urls.txt"
    output_file:            str                 = "poster.jpg"

    aspect_ratio_stretch_tolerance = 1.15 # tol > 1. Max. rel. difference between the larger a.r. to the smaller one.

    # Only books read after this date are included  
    start_date = datetime(year=2015, month=1, day=1, tzinfo=timezone.utc)
    # Only books read before this date are included  
    end_date = datetime.now(timezone.utc).astimezone() # Now in local timezone

    credit_str = 'Created with the\nBook Poster Creator by N. Römheld'
    credit_url = 'https://github.com/n-roemheld/book-poster'

    def get_title_str(self):
        return f'Books read between {str(self.start_date.date())} and {str(self.end_date.date())}'
    
    def get_book_str(self, book: dict) -> tuple[str, str]:
        # Available information in book (examples): 
        # 'title', 'author_name', 'book_published', 'num_pages', 'average_rating', 'user_rating', 
        # 'user_read_at', 'user_date_created', 'user_date_added'
        read_date_str       = str(datetime.strptime(book['user_read_at'], '%a, %d %b %Y %H:%M:%S %z').date()) if book['user_read_at'] else ''
        goodreads_rating    =  f'{float(book["average_rating"]):.1f}' + u"\u2606"
        user_rating         =  f'{book["user_rating"]}' + u"\u2605" if int(book['user_rating']) else ''
        rating_str          = user_rating if int(book['user_rating']) else goodreads_rating
        n_pages_str         = f'{book["num_pages"]} pages' if book['num_pages'] else ''
        book_str            = f'Read {read_date_str}\n{n_pages_str} {goodreads_rating} {user_rating}'
        align_multiline     = 'center'
        return book_str, align_multiline

@dataclass
class ConfigLayout:

    poster = {}
    poster['background_color_hex']:     str                 = "#FFFFFF"
    poster['dim']:                      Dimensions_cm       = Dimensions_cm(width=60, height=90)
    poster['min_margins_factor']                            = .01 * np.array([1,1,1]) # of poster height

    grid = {}
    grid['n_books']:                    tuple[int,int]      = (8,8)
    grid['cover_dist_factor']                               = np.array([.01,.01])  # of cover width, height

    year_shading = {}
    year_shading['enable']:             bool                = True
    year_shading['color1_hex']:         str                 = "#FFFFFF"
    year_shading['color2_hex']:         str                 = "#CCCCCC"
    year_shading['factors']                                 = 1 * np.array([.1,.05]) # of cover width, height

    book = {}
    book['rating_print']:               bool                = True
    book['default_aspect_ratio']:       float               = .6555
    book['font_path']:                  str                 = "./fonts/Lato-star.ttf"
    book['expected_cover_height']:      int                 = 475 # px, common height of cover images on goodreads, used for dpi calculations
    book['shadow_factors']                                  = np.array([.03,.06]) # of cover width, height
    book['font_height_factor']:         float               = 1/15. # of cover height
    book['font_vspace_factor']:         float               = 1/4. # of font height

    title = {}
    title['enable']:                    bool                = True
    title['font_path']:                 str                 = "./fonts/Merriweather-Regular.ttf"
    title['font_height_factor']:        float               = .02 # of poster height
    title['vspace_factor']:             float               = .5 # of font height

    signature = {}
    signature['enable']:                bool                = True
    signature['font_path']:             str                 = "./fonts/Lato-star.ttf"
    signature['height_factor']:         float               = 1.2 # of title height
    signature['vspace_factor']:         float               = .3 # of signature height
    signature['font_height_factor']:    float               = .35 # of signature height
    signature['hspace_factor']:         float               = .35 # of signature height

    def get_layout_config_dicts(self):
        return self.poster, self.grid, self.year_shading, self.book, self.title, self.signature

if __name__ == '__main__':
    from book_poster_creator import main
    main()
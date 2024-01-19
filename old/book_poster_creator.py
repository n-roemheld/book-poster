# Future work:
# To do: use class instead of named tuple classes
# To do: Add a shadow to the books (plot blurred rectangle first, use mask to blurr selectively? or paste blurred image?)
# To do: Automatic dpi and distance calculation based on the size of the poster. Ensure compatibility with separators and text.
# To do: Add a permissible amount of stretch for the cover images and apply it.
# To do: Add the started reading date
# To do: Add option to include the rating
# To do: Add a Title, e.g. "Books read betweey x and y"
# To do: Add a signature with QR codes for the repository (made with...) and goodreads profile (follow me on goodreads)


import warnings
from datetime import datetime, timezone
import os
from os.path import exists
from dataclasses import dataclass, field
from typing import NamedTuple
import urllib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import feedparser
import poster_config as config
from Dimensions_file import Dimensions_cm, Dimensions_pixel

H = 0 # horizontal index
V = 1 # vertical intex
INCH_IN_CM = 2.54

def main() -> None:
    '''Creates a poster with the book covers of a 'read' shelf on goodreads using RSS feeds'''
    # List of RSS-feeds to use
    # Warning: goodreads only supports upto 100 books per rss feed!
    #          Recommended: To get the 100 books you read last, add '&sort=user_read_at' at the end of the rss url.
    #          For posters with more than 100 books, split shelves into shelves with less than 100 books.
    #          Duplicates are eliminated.
    if exists('rss_urls.txt'):
        filename = 'rss_urls.txt'
    else:
        filename = 'rss_urls_test.txt'
    with open(filename) as f:
        rss_urls = [line for line in f.readlines()]

    # Only books read after this date are included
    START_DATE = datetime(year=config.startdate_year, month=config.startdate_month, day=config.startdate_day, tzinfo=timezone.utc)

    design_parameters = PosterParameters(dpi                        = config.dpi, 
                                        poster_size_cm              = config.poster_size_cm, 
                                        min_distance_cm             = config.min_distance_cm, 
                                        max_cover_height_cm         = config.max_cover_height_cm, 
                                        default_aspect_ratio        = config.default_aspect_ratio, 
                                        title_height_cm             = config.title_height_cm, 
                                        output_file                 = config.output_file,
                                        font_str                    = config.font_str,
                                        background_color_hex        = config.background_color_hex,
                                        year_shading                = config.year_shading,
                                        year_shading_color1_hex     = config.year_shading_color1_hex,
                                        year_shading_color2_hex     = config.year_shading_color2_hex,
                                        separator_width_factor      = config.separator_width_factor
                                        )
    create_poster_from_rss(rss_urls, START_DATE, design_parameters)



@dataclass
class PosterParameters:
    '''Class for handling poster layout parameters'''
    # Initialized by constructor
    dpi:                    int                 = 208
    poster_size_cm:         Dimensions_cm       = (60,90)
    min_distance_cm:        Dimensions_cm       = (.6,1)
    max_cover_height_cm:    float               = 6.3
    default_aspect_ratio:   float               = .6555
    title_height_cm:        float               = 0 # space for a possible title
    output_file:            str                 = "poster.jpg"
    font_str:               str                 = "./DejaVuSans.ttf"
    background_color_hex:   str                 = "#FFFFFF"
    year_shading:           bool                = True
    year_shading_color1_hex:str                 = "#CCCCCC"
    year_shading_color2_hex:str                 = "#FFFFFF"
    separator_width_factor: float               = 1/40. # width of the separator line in the book grid
    print_rating:           bool                = True
    # Computed from other attributes via post_init
    poster_size:            Dimensions_pixel        = field(init=False)
    max_cover_size_cm:      Dimensions_cm           = field(init=False)
    max_cover_size:         Dimensions_pixel        = field(init=False)
    min_distance:           Dimensions_pixel        = field(init=False)
    n_books_grid:           tuple[int,int]          = field(init=False)
    margins:                Dimensions_pixel        = field(init=False)
    opt_aspect_ratio:       float                   = field(init=False)
    fontsize:               int                     = field(init=False)
    font:                   ImageFont.FreeTypeFont  = field(init=False)
    n_books_grid_total:     int                     = field(init=False)

    def __post_init__(self):
        # Setup poster size
        self.poster_size = self.convert_cm_to_pixel(self.poster_size_cm) # in pixel, (horizontal,vertical)
        
        # Setup cover size
        self.max_cover_size_cm = (self.default_aspect_ratio * self.max_cover_height_cm, self.max_cover_height_cm)
        self.max_cover_size = self.convert_cm_to_pixel(self.max_cover_size_cm) # in pixel, (horizontal,vertical)
        
        # Setup cover spacing
        self.min_distance = self.convert_cm_to_pixel(self.min_distance_cm) # in pixel, (horizontal,vertical)

        # Calculate margins 
        self.calc_n_books_grid()
        self.calc_margins()
        
        # Other properties
        H = 0 # horizontal index
        V = 1 # vertical intex
        self.opt_aspect_ratio = self.max_cover_size_cm[H] / self.max_cover_size_cm[V]
        self.fontsize = int(self.max_cover_size[V] / 15)
        self.font = ImageFont.truetype(self.font_str, size=self.fontsize)
        self.n_books_grid_total = self.n_books_grid[H] * self.n_books_grid[V]

    def convert_cm_to_pixel(self, values_cm):
        cm_to_pixel_factor = self.dpi / INCH_IN_CM
        if isinstance(values_cm, (tuple, list, NamedTuple)):
            values_pix = [round(v_cm * cm_to_pixel_factor) for v_cm in values_cm]
        else:  # scalar
            values_pix = round(values_cm * cm_to_pixel_factor)
        return values_pix
    
    def calc_n_books_grid(self) -> None:    
        n_books_h = int((self.poster_size_cm[H] - self.min_distance_cm[H]) / (self.max_cover_size_cm[H] + self.min_distance_cm[H]))
        n_books_v = int((self.poster_size_cm[V] - self.min_distance_cm[V] - self.title_height_cm) / (self.max_cover_size_cm[V] + self.min_distance_cm[V]))
        self.n_books_grid = (n_books_h, n_books_v)

    def calc_margins(self) -> None:
        margins_cm_h = (self.poster_size_cm[H] + self.min_distance_cm[H] - self.n_books_grid[H] * (self.max_cover_size_cm[H] + self.min_distance_cm[H]))/2.
        margins_cm_v = (self.poster_size_cm[V] + self.min_distance_cm[V] - self.n_books_grid[V] * (self.max_cover_size_cm[V] + self.min_distance_cm[V]))/2.
        margins_cm = (margins_cm_h, margins_cm_v)
        self.margins = self.convert_cm_to_pixel(margins_cm) # in pixel, (horizontal,vertical)

def create_poster_from_rss(rss_urls: list[str], START_DATE: datetime, design_parameters: PosterParameters) -> None:
    # Loading feeds
    books = load_feeds(rss_urls)
    user_profile_link = get_user_profile_link_from_rss(rss_urls[0])

    # Reordering books by read date
    books, read_at_list = sort_books(books)

    # Excluding books read before START_DATE
    books = filter_books(START_DATE, books, read_at_list)

    # Download covers from goodreads
    download_covers(books)
    
    # Composition of the image
    create_poster_image(books, design_parameters, user_profile_link=user_profile_link)

def get_cover_filename(book: dict, PATH_TO_COVERS='./covers') -> str:
    '''Get the path to the cover image of the book'''
    return f'{PATH_TO_COVERS}/{book["book_id"]}.jpg'

def load_feeds(rss_urls: list) -> np.ndarray:
    '''Downloading the RSS feed and converting it to an array of books'''
    print('Loading feeds...')
    books = np.atleast_1d(np.array([]))
    for i,url in enumerate(rss_urls):
        feed = feedparser.parse(url)
        print(f"Feed {i}:", feed.feed.title)
        books_from_feed = np.array(feed.entries)
        books = np.concatenate((books, books_from_feed))
    books = np.array(list({b['book_id']:b for b in books}.values())) # removing duplicates
    if books.size == 0:
        exit(f"No books found in the feeds. Please check the feeds and try again.")
    return books

def get_user_profile_link_from_rss(rss_url: str) -> str:
    user_id = int(rss_url.split("?")[0].split("/")[-1])
    link_to_user_profile = f"https://www.goodreads.com/user/show/{user_id}"
    return link_to_user_profile

def sort_books(books: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    '''Reordering books by read date'''
    read_at_list = []
    for book in books:
        if book['user_read_at'] == '': # no read date entered
            read_at_list.append(datetime(year=1900, month=1, day=1, tzinfo=timezone.utc))
        else:
            read_at_list.append(datetime.strptime(book['user_read_at'], '%a, %d %b %Y %H:%M:%S %z'))
    read_at_list = np.array(read_at_list)
    order = np.argsort(read_at_list).astype(int)
    books = books[order]
    read_at_list = read_at_list[order]
    return books, read_at_list

def filter_books(START_DATE: datetime, books: np.ndarray, read_at_list: np.ndarray) -> np.ndarray:
    '''Excluding books read before START_DATE'''
    try:
        start_index = np.where(START_DATE <= read_at_list)[0][0]
    except IndexError:
        exit(f"No books read after {START_DATE}. Please check the feeds and your date constraints and try again.")
    read_at_list = read_at_list[start_index:]
    books = books[start_index:]
    return books

def download_covers(books: np.ndarray, COVER_URL_KEY: str ='book_large_image_url', PATH_TO_COVERS='./covers') -> None:
    '''Downloading the book covers from goodreads (if not downloaded already)'''
    print(f"Downloading missing covers of {int(books.size)} books...")
    if not exists(PATH_TO_COVERS):
        os.mkdir(PATH_TO_COVERS)
    for book in books:
        if not exists(get_cover_filename(book)):
            urllib.request.urlretrieve(book[COVER_URL_KEY], get_cover_filename(book, PATH_TO_COVERS))
    print('Done!')

def create_poster_image(books: np.ndarray, params: PosterParameters, user_profile_link: str = None) -> None:
    '''Creating the poster image with the book covers and read date'''
    if books.size > params.n_books_grid_total:
        warnings.warn(f"Warning: The current poster grid only supports {params.n_books_grid_total} books. {books.size - params.n_books_grid_total} books are not included.", DeprecationWarning)
        # Removing the first books to only include the books read last in the poster.
        books = books[-params.n_books_grid_total:]

    # Create a blank poster
    print('Creating poster...')
    poster = Image.new("RGB", params.poster_size, params.background_color_hex)
    draw = ImageDraw.Draw(poster)

    # Adding shading for the years to the poster
    if params.year_shading:
        shade_years(books, params, draw)

    # Populate the poster with book covers and titles
    print('Adding books to poster...')
    for i, book in enumerate(books):
        # Check if the grid is already full
        assert (i + 1 <= params.n_books_grid_total), "More books than the poster can handle!"

        # Grid position of the current cover
        row = i // params.n_books_grid[H]
        col = i % params.n_books_grid[H]

        # Load cover image
        cover_image = Image.open(get_cover_filename(book))
        # Resizing cover image
        cover_image = resize_cover_image(params, cover_image)
        # Adding the cover to the poster
        cover_position = calc_cover_position(params, row, col, cover_image.size)
        poster.paste(cover_image, cover_position)

        # Additing an outline to the cover
        draw.rectangle((cover_position, tuple(cover_position[i] + cover_image.size[i] for i in range(2))), fill=None, width=int(cover_image.size[H]/200.), outline="black")

        # Add read date below the cover
        if book['user_read_at'] != '':
            read_date = str(datetime.strptime(book['user_read_at'], '%a, %d %b %Y %H:%M:%S %z').date())
            text = read_date
            if params.print_rating:
                if int(book['user_rating']) > 0:
                    text = text + f' ({book["user_rating"]}' + u"\u2605" + ')'
                else:
                    text = text + f' ({float(book["average_rating"]):.1f}' + u"\u2606" + ')'
            text_position = calc_text_position(params, draw, row, col, text)
            draw.text(text_position, text, fill="black", font=params.font, align='center')
    
    # Save the poster
    print('Saving Poster...')
    poster.save(params.output_file)
    print('Done!')

def resize_cover_image(params: PosterParameters, cover_image: Image.Image) -> tuple[Image.Image, tuple[int,int]]:
    '''Resampling the cover images with the appropriate resolution'''
    aspect_ratio = cover_image.size[H] / cover_image.size[V]
    # If the cover's aspect ratio is similar to the optimal aspect ratio, the cover is stretched.
    if np.maximum(aspect_ratio/params.opt_aspect_ratio, params.opt_aspect_ratio/aspect_ratio) < 1.2:
        cover_image_size = params.max_cover_size
    elif (params.opt_aspect_ratio < aspect_ratio):
        cover_image_size = (params.max_cover_size[H], np.round(params.max_cover_size[H] / aspect_ratio).astype(int))
    else:
        cover_image_size = (np.round(params.max_cover_size[V] * aspect_ratio).astype(int), params.max_cover_size[V])
    cover_image = cover_image.resize(cover_image_size, Image.BICUBIC)
    return cover_image

def calc_cover_position(params: PosterParameters, row: int, col: int, image_size: tuple[int,int], offset: int = 0) -> tuple[int,int]:
    '''Calculating the position where the next cover is inserted'''
    pos_h = round(params.margins[H] + col * (params.max_cover_size[H] + params.min_distance[H]) + (params.max_cover_size[H]-image_size[H])/2)
    pos_v = round(params.title_height_cm + params.margins[V] + row * (params.max_cover_size[V] + params.min_distance[V]) + (params.max_cover_size[V]-image_size[V])/2)
    cover_position = (pos_h + offset, pos_v + offset)
    return cover_position

def calc_text_position(params: PosterParameters, draw: ImageDraw, row: int, col: int, read_date: str) -> tuple[int,int]:
    '''Calculating the position where the read date is inserted'''
    _, _, w, _ = draw.textbbox((0, 0), read_date, font=params.font)
    text_position_h = round(params.margins[H] + col * (params.max_cover_size[H] + params.min_distance[H]) + params.max_cover_size[H]/2 - w/2)
    text_position_v = round(params.title_height_cm + params.margins[V] + row * (params.max_cover_size[V] + params.min_distance[V]) + params.max_cover_size[V]*1 + params.fontsize/4)
    text_position = (text_position_h, text_position_v)
    return text_position


def shade_years(books: np.ndarray, params: PosterParameters, draw: ImageDraw) -> None:
    if params.separator_width_factor == 0:
        half_separator_width = 0
    else:
        half_separator_width = int(params.max_cover_size[H]*params.separator_width_factor/2.)+1
    years, row_first_book_in_year, col_first_book_in_year = get_grid_index_of_first_books_in_years(books, params)
    for y in range(years.size-1):
        for row in range(row_first_book_in_year[y], row_first_book_in_year[y+1] + 1):
            start_col, end_col = get_grid_col_indices_in_row(row, y, params, row_first_book_in_year, col_first_book_in_year)
            # print(f'year index {y}, row {row}, start_col {start_col}, end_col {end_col}')
            if ((row == row_first_book_in_year[y+1]) and (end_col == params.n_books_grid[H] - 1)) or (row >= params.n_books_grid[V]):
                continue
            else:
                cover_position_start = calc_cover_position(params, row, start_col, params.max_cover_size, half_separator_width)
                cover_position_end = calc_cover_position(params, row, end_col, params.max_cover_size, -half_separator_width)
                # start_pos = tuple(cover_position[])
                start_h, start_v, end_h, end_v = get_shading_rectangle_corners(params, cover_position_start, cover_position_end)

                if y % 2 == 0:
                    color = params.year_shading_color1_hex
                else:
                    color = params.year_shading_color2_hex
                draw.rectangle(((start_h, start_v), (end_h, end_v)), fill=color, outline=None)

def get_shading_rectangle_corners(params: PosterParameters, cover_position_start: np.ndarray, cover_position_end: np.ndarray) -> tuple[int,int,int,int]:
    start_h = cover_position_start[H] - round(params.min_distance[H] / 2.)
    start_v = cover_position_start[V] - round(params.min_distance[V] / 3.)
    end_h   = cover_position_end[H] + params.max_cover_size[H] + round(params.min_distance[H] / 2.)
    end_v   = cover_position_end[V] + params.max_cover_size[V] + round(params.min_distance[V] * 2/3.)
    return start_h, start_v, end_h, end_v

def get_grid_col_indices_in_row(row: int, y: int, params: PosterParameters, row_first_book_in_year: np.ndarray, col_first_book_in_year: np.ndarray) -> tuple[int,int]:
    if row == row_first_book_in_year[y]:
        start_col = col_first_book_in_year[y]
    else:
        start_col = 0
    if row == row_first_book_in_year[y+1] and start_col < col_first_book_in_year[y+1]:
        end_col = col_first_book_in_year[y+1] - 1
    else:
        end_col = params.n_books_grid[H] - 1
    return start_col, end_col

def get_grid_index_of_first_books_in_years(books: np.ndarray, params: PosterParameters) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # Add first book/year
    years = [int(datetime.strptime(books[0]['user_read_at'], '%a, %d %b %Y %H:%M:%S %z').year),]
    row_first_book_in_year = [0,]
    col_first_book_in_year = [0,]
    for b, book in enumerate(books):
        if b == 0: # already added
            continue
        current_year = int(datetime.strptime(book['user_read_at'], '%a, %d %b %Y %H:%M:%S %z').year)
        if years[-1] < current_year: # New year
            years.append(current_year)
            # Grid position of the current cover
            row = b // params.n_books_grid[H]
            col = b % params.n_books_grid[H]
            row_first_book_in_year.append(row)
            col_first_book_in_year.append(col)
    # Dummy for end of grid
    b = b + 1
    years.append(current_year+1)
    row = b // params.n_books_grid[H]
    col = b % params.n_books_grid[H]
    row_first_book_in_year.append(row)
    col_first_book_in_year.append(col)
    # np array conversion
    years = np.array(years, dtype=int)
    row_first_book_in_year = np.array(row_first_book_in_year, dtype=int)
    col_first_book_in_year = np.array(col_first_book_in_year, dtype=int)
    return years, row_first_book_in_year, col_first_book_in_year

if __name__ == '__main__':
    main()

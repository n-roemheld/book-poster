import feedparser
from datetime import datetime, timezone
import urllib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from os.path import exists
import warnings
from dataclasses import dataclass, field

def main() -> None:
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
    START_DATE = datetime(year=2015, month=12, day=31, tzinfo=timezone.utc)

    design_parameters = PosterParameter(dpi=100, poster_size_cm=(60,90), min_distance_cm=(.6,1), max_cover_height_cm=6.3)
    create_poster_from_rss(rss_urls, START_DATE, design_parameters)

@dataclass
class PosterParameter:
    '''Class for handling some poster layout parameters'''
    # Initialized by constructor
    dpi:                    int = 100
    poster_size_cm:         tuple[float,float] = (60,90)
    min_distance_cm:        tuple[float,float] = (.6,1)
    max_cover_height_cm:    float = 6.3
    default_aspect_ratio:   float = .6555
    title_height_cm:        float = 0 # space for a possible title
    output_file:            str = "poster.jpg"
    font_str:               str = "arial.ttf"
    # Computed from other attributes via post_init
    poster_size:            tuple[int,int]          = field(init=False)
    max_cover_size_cm:      tuple[float,float]      = field(init=False)
    max_cover_size:         tuple[int,int]          = field(init=False)
    min_distance:           tuple[int,int]          = field(init=False)
    n_books_grid:           tuple[int,int]          = field(init=False)
    margins:                tuple[int,int]          = field(init=False)
    opt_aspect_ratio:       float                   = field(init=False)
    fontsize:               int                     = field(init=False)
    font:                   ImageFont.FreeTypeFont  = field(init=False)
    n_books_grid_total:     int                     = field(init=False)

    def __post_init__(self):
        # Setup poster size
        self.poster_size = self.convert_cm_to_pixel(self.poster_size_cm, self.dpi) # in pixel, (horizontal,vertical)
        
        # Setup cover size
        self.max_cover_size_cm = (self.default_aspect_ratio * self.max_cover_height_cm, self.max_cover_height_cm)
        self.max_cover_size = self.convert_cm_to_pixel(self.max_cover_size_cm, self.dpi) # in pixel, (horizontal,vertical)
        
        # Setup cover spacing
        self.min_distance = self.convert_cm_to_pixel(self.min_distance_cm, self.dpi) # in pixel, (horizontal,vertical)

        # Calculate margins 
        self.n_books_grid = self.calc_n_books_grid(self.poster_size_cm, self.max_cover_size_cm, self.min_distance_cm, self.title_height_cm)
        self.margins = self.calc_margins(self.poster_size_cm, self.min_distance_cm, self.n_books_grid, self.max_cover_size_cm, self.dpi)
        
        # Other properties
        H = 0 # horizontal index
        V = 1 # vertical intex
        self.opt_aspect_ratio = self.max_cover_size_cm[H] / self.max_cover_size_cm[V]
        self.fontsize = int(self.max_cover_size[V] / 15)
        self.font = ImageFont.truetype(self.font_str, size=self.fontsize)
        self.n_books_grid_total = self.n_books_grid[H] * self.n_books_grid[V]

    def convert_cm_to_pixel(self, values_cm, dpi: int = 100):
        cm_to_pixel_factor = dpi * 2.54
        if isinstance(values_cm, (tuple, list)):
            values_pix = [round(v_cm * cm_to_pixel_factor) for v_cm in values_cm]
        else:  # scalar
            values_pix = round(values_cm * cm_to_pixel_factor)
        return values_pix
    
    def calc_n_books_grid(self, poster_size_cm, max_cover_size_cm, min_distance_cm, title_height_cm=0) -> tuple[int,int]:    
        H = 0 # horizontal index
        V = 1 # vertical intex
        n_books_h = int((poster_size_cm[H] - min_distance_cm[H]) / (max_cover_size_cm[H] + min_distance_cm[H]))
        n_books_v = int((poster_size_cm[V] - min_distance_cm[V] - title_height_cm) / (max_cover_size_cm[V] + min_distance_cm[V]))
        n_books_grid = (n_books_h, n_books_v)
        return n_books_grid

    def calc_margins(self, poster_size_cm, min_distance_cm, n_books_grid, max_cover_size_cm, dpi) -> tuple[int,int]:
        H = 0 # horizontal index
        V = 1 # vertical intex
        margins_cm_h = (poster_size_cm[H] + min_distance_cm[H] - n_books_grid[H] * (max_cover_size_cm[H] + min_distance_cm[H]))/2.
        margins_cm_v = (poster_size_cm[V] + min_distance_cm[V] - n_books_grid[V] * (max_cover_size_cm[V] + min_distance_cm[V]))/2.
        margins_cm = (margins_cm_h, margins_cm_v)
        margins = self.convert_cm_to_pixel(margins_cm, dpi) # in pixel, (horizontal,vertical)
        return margins

def create_poster_from_rss(rss_urls: list, START_DATE: datetime, design_parameters: PosterParameter) -> None:
    # Loading feeds
    books = load_feeds(rss_urls)

    # Reordering books by read date
    books, read_at_list = sort_books(books)

    # Excluding books read before START_DATE
    books = filter_books(START_DATE, books, read_at_list)

    # Download covers from goodreads
    download_covers(books)
    
    # Composition of the image
    create_poster_image(books, design_parameters)

def get_cover_filename(book: np.array, PATH_TO_COVERS='./covers') -> str:
    # Path to the cover image of the book
    return f'{PATH_TO_COVERS}/{book['book_id']}.jpg'

def load_feeds(rss_urls: list) -> np.array:
    # Downloading the RSS feed and converting it to an array of books
    print('Loading feeds...')
    books = np.atleast_1d(np.array([]))
    for i,url in enumerate(rss_urls):
        feed = feedparser.parse(url)
        print(f"Feed {i}:", feed.feed.title)
        books_from_feed = np.array(feed.entries)
        books = np.concatenate((books, books_from_feed))
    books = np.array(list({b['book_id']:b for b in books}.values())) # removing duplicates
    return books

def sort_books(books: np.array) -> tuple[np.array, np.array]:
    # Reordering books by read date
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

def filter_books(START_DATE: datetime, books: np.array, read_at_list: np.array) -> np.array:
    # Excluding books read before START_DATE
    start_index = np.where(START_DATE <= read_at_list)[0][0]
    read_at_list = read_at_list[start_index:]
    books = books[start_index:]
    return books

def download_covers(books: np.array, COVER_URL_KEY: str ='book_large_image_url') -> None:
    # Downloading the book covers from goodreads (if not downloaded already)
    print(f"Downloading missing covers of {int(books.size)} books...")
    for book in books:
        if not exists(get_cover_filename(book)):
            urllib.request.urlretrieve(book[COVER_URL_KEY], get_cover_filename(book))
    print('Done!')

def create_poster_image(books: np.array, params: PosterParameter) -> None:
    # Creating the poster image with the book covers and read date
    H = 0 # horizontal index
    V = 1 # vertical intex

    # Create a blank poster
    print('Creating poster...')
    poster = Image.new("RGB", params.poster_size, "white")
    draw = ImageDraw.Draw(poster)

    # Populate the poster with book covers and titles
    print('Adding books to poster...')
    if books.size > params.n_books_grid_total:
        warnings.warn(f"Warning: The current poster grid only supports {params.n_books_grid}. {books.size - params.n_books_grid_total} books are not included.", DeprecationWarning)
    for i, book in enumerate(books):
        # Check if the grid is already full
        if i + 1 > params.n_books_grid_total:
            break

        # Grid position of the current cover
        row = i // params.n_books_grid[H]
        col = i % params.n_books_grid[H]

        # Load cover image
        cover_image = Image.open(get_cover_filename(book))
        # Resizing cover image
        cover_image = resize_cover_image(params.max_cover_size, params.opt_aspect_ratio, cover_image)
        # Adding the cover to the poster
        cover_position = calc_cover_position(params, row, col, cover_image.size)
        poster.paste(cover_image, cover_position)

        # Add read date below the cover
        if book['user_read_at'] == '': # no read date entered
            read_date = str(datetime(year=1900, month=1, day=1, tzinfo=timezone.utc).date())
        else:
            read_date = str(datetime.strptime(book['user_read_at'], '%a, %d %b %Y %H:%M:%S %z').date())
        text_position = calc_text_position(params, draw, row, col, read_date)
        draw.text(text_position, read_date, fill="black", font=params.font, align='center')

    # Save the poster
    print('Saving Poster...')
    poster.save(params.output_file)
    print('Done!')

def resize_cover_image(max_cover_size, opt_aspect_ratio, cover_image) -> tuple[Image, tuple[int,int]]:
    # Resampling the cover images with the appropriate resolution
    H = 0 # horizontal index
    V = 1 # vertical intex
    aspect_ratio = cover_image.size[H] / cover_image.size[V]
    if (opt_aspect_ratio < aspect_ratio):
        cover_image_size = (max_cover_size[H], np.round(max_cover_size[H] / aspect_ratio).astype(int))
    else:
        cover_image_size = (np.round(max_cover_size[V] * aspect_ratio).astype(int), max_cover_size[V])
    cover_image = cover_image.resize(cover_image_size, Image.BICUBIC)
    return cover_image

def calc_cover_position(params: PosterParameter, row: int, col: int, image_size: tuple[int,int]) -> tuple[int,int]:
    # Calculating the position where the next cover is inserted
    H = 0 # horizontal index
    V = 1 # vertical intex
    pos_h = round(params.margins[H] + col * (params.max_cover_size[H] + params.min_distance[H]) + (params.max_cover_size[H]-image_size[H])/2)
    pos_v = round(params.title_height_cm + params.margins[V] + row * (params.max_cover_size[V] + params.min_distance[V]) + (params.max_cover_size[V]-image_size[V])/2)
    cover_position = (pos_h, pos_v)
    return cover_position

def calc_text_position(params: PosterParameter, draw: ImageDraw, row: int, col: int, read_date: str) -> tuple[int,int]:
    # Calculating the position where the read date is inserted
    H = 0 # horizontal index
    V = 1 # vertical intex
    _, _, w, _ = draw.textbbox((0, 0), read_date, font=params.font)
    text_position_h = round(params.margins[H] + col * (params.max_cover_size[H] + params.min_distance[H]) + params.max_cover_size[H]/2 - w/2)
    text_position_v = round(params.title_height_cm + params.margins[V] + row * (params.max_cover_size[V] + params.min_distance[V]) + params.max_cover_size[V]*1 + params.fontsize/4)
    text_position = (text_position_h, text_position_v)
    return text_position

if __name__ == '__main__':
    main()
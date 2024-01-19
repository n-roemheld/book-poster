# Future work:
# To do: use class instead of named tuple classes
# To do: Add a shadow to the books (plot blurred rectangle first, use mask to blurr selectively? or paste blurred image?)
# To do: Automatic dpi and distance calculation based on the size of the poster. Ensure compatibility with separators and text.
# To do: Add a permissible amount of stretch for the cover images and apply it.
# To do: Add the started reading date
# To do: Add option to include the rating
# To do: Add a Title, e.g. "Books read betweey x and y"
# To do: Add a signature with QR codes for the repository (made with...) and goodreads profile (follow me on goodreads)
# To do: Font color options


import warnings
from datetime import datetime, timezone
import os
from os.path import exists
import urllib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import feedparser
import poster_config as config
from Dimensions_file import Dimensions, Position, Length
from layout_generator import PosterLayout

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
    rss_urls = read_rss_urls()
    layout_parameters = PosterLayout()
    create_poster_from_rss(rss_urls, layout_parameters, config.start_date, config.end_date)

def read_rss_urls() -> list[str]:
    if exists('rss_urls.txt'):
        filename = 'rss_urls.txt'
    else:
        filename = 'rss_urls_test.txt'
    with open(filename) as f:
        rss_urls = [line for line in f.readlines()]
    return rss_urls


def create_poster_from_rss(rss_urls: list[str], layout_parameters: PosterLayout, start_date: datetime, end_date: datetime = datetime.today()) -> None:
    # Loading feeds
    books = load_feeds(rss_urls)
    user_profile_link = get_user_profile_link_from_rss(rss_urls[0])

    # Reordering books by read date
    books, read_at_list = sort_books(books)

    # Excluding books read before start_date
    books = filter_books(books, read_at_list, start_date, end_date)

    # Download covers from goodreads
    download_covers(books)
    
    # Composition of the image
    create_poster_image(books, layout_parameters, user_profile_link=user_profile_link)

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

def filter_books(books: np.ndarray, read_at_list: np.ndarray, start_date: datetime, end_date: datetime) -> np.ndarray:
    '''Excluding books read before start_date'''
    try:
        start_index = np.where(start_date <= read_at_list)[0][0]
        end_index   = np.where(read_at_list <= end_date)[0][-1]
    except IndexError:
        exit(f"No books read between {start_date.date()} and {end_date.date()}. Please check the feeds and your date constraints and try again.")
    read_at_list = read_at_list[start_index:end_index+1]
    books = books[start_index:end_index+1]
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

def create_poster_image(books: np.ndarray, layout: PosterLayout, user_profile_link: str = None) -> None:
    '''Creating the poster image with the book covers and read date'''
    if books.size > layout.n_books_grid_total:
        warnings.warn(f"Warning: The current poster grid only supports {layout.n_books_grid_total} books. {books.size - layout.n_books_grid_total} books are not included.", DeprecationWarning)
        # Removing the first books to only include the books read last in the poster.
        books = books[-layout.n_books_grid_total:]

    # Create a blank poster
    print('Creating poster...')
    poster = Image.new("RGB", layout.poster_size, layout.background_color_hex)
    draw = ImageDraw.Draw(poster)

    # Adding the title
    if layout.print_title:
        title_position = layout.get_title_position(config.title_str)
        draw.text(title_position.get_dim_in_px(), config.title_str, font=layout.title_font)

    # Adding shading for the years to the poster
    if layout.year_shading:
        shade_years(books, layout, draw)

    # Populate the poster with book covers and titles
    print('Adding books to poster...')
    for i, book in enumerate(books):
        # Check if the grid is already full
        assert (i + 1 <= layout.n_books_grid_total), "More books than the poster can handle!"

        # Grid position of the current cover
        row = i // layout.n_books_grid[H]
        col = i % layout.n_books_grid[H]

        # Add book cover to the poster
        add_cover_to_poster(layout, poster, draw, book, row, col)

        # Add book-specific information below the cover
        add_book_text(layout, draw, book, row, col)
    
    # Save the poster
    print('Saving Poster...')
    poster.save(layout.output_file)
    print('Done!')

def add_book_text(layout, draw, book, row, col):
    # Add book-specific information below the cover
    if book['user_read_at'] != '':
        read_date = str(datetime.strptime(book['user_read_at'], '%a, %d %b %Y %H:%M:%S %z').date())
        text = read_date
        if layout.print_rating:
            if int(book['user_rating']) > 0:
                text = text + f' ({book["user_rating"]}' + u"\u2605" + ')'
            else:
                text = text + f' ({float(book["average_rating"]):.1f}' + u"\u2606" + ')'
        text_position = layout.get_cover_text_position(col, row, [text], line_index=0)
        draw.text(text_position.get_dim_in_px(), text, fill="black", font=layout.book_font, align='center')

def add_cover_to_poster(layout, poster, draw, book, row, col) -> None:
    # Load cover image
    cover_image = Image.open(get_cover_filename(book))
    # Resizing cover image
    cover_image = resize_cover_image(layout, cover_image)
    cover_size = Dimensions(cover_image.size[0], cover_image.size[1], unit='px', dpi=layout.dpi)
    # Adding the cover to the poster
    cover_position = layout.get_cover_position(col, row, cover_size)
    poster.paste(cover_image, cover_position.get_dim_in_px())

    # Additing an outline to the cover
    draw.rectangle((cover_position.get_dim_in_px(), tuple(cover_position.get_dim_in_px()[i] + cover_image.size[i] for i in range(2))), fill=None, width=int(cover_image.size[H]/200.), outline="black")


def resize_cover_image(layout: PosterLayout, cover_image: Image.Image) -> tuple[Image.Image, tuple[int,int]]:
    '''Resampling the cover images with the appropriate resolution'''
    aspect_ratio = cover_image.size[H] / cover_image.size[V]
    # If the cover's aspect ratio is similar to the optimal aspect ratio, the cover is stretched.
    if np.maximum(aspect_ratio/layout.default_aspect_ratio, layout.default_aspect_ratio/aspect_ratio) < 1.2:
        cover_image_size = layout.cover_area.get_dim_in_px()
    elif (layout.default_aspect_ratio < aspect_ratio):
        cover_image_size = (layout.cover_area.width_px(), np.round(layout.cover_area.width_px() / aspect_ratio).astype(int))
    else:
        cover_image_size = (np.round(layout.cover_area.height_px() * aspect_ratio).astype(int), layout.cover_area.height_px())
    cover_image = cover_image.resize(cover_image_size, Image.BICUBIC)
    return cover_image

def shade_years(books: np.ndarray, layout: PosterLayout, draw: ImageDraw) -> None:
    # if layout.separator_width_factor == 0:
    half_separator_width = 0
    # else:
    #     half_separator_width = int(layout.cover_area.width_px()*layout.separator_width_factor/2.)+1
    years, row_first_book_in_year, col_first_book_in_year = get_grid_index_of_first_books_in_years(books, layout)
    for y in range(years.size-1):
        for row in range(row_first_book_in_year[y], row_first_book_in_year[y+1] + 1):
            start_col, end_col = get_grid_col_indices_in_row(row, y, layout, row_first_book_in_year, col_first_book_in_year)
            # print(f'year index {y}, row {row}, start_col {start_col}, end_col {end_col}')
            if ((row == row_first_book_in_year[y+1]) and (end_col == layout.n_books_grid[H] - 1)) or (row >= layout.n_books_grid[V]):
                continue
            else:
                start_position   = layout.get_shading_start_position(start_col, row)
                end_position     = layout.get_shading_start_position(end_col, row)

                if y % 2 == 0:
                    color = layout.year_shading_color1_hex
                else:
                    color = layout.year_shading_color2_hex
                draw.rectangle((start_position.xy_px(), end_position.xy_px()), fill=color, outline=None)

def get_grid_col_indices_in_row(row: int, y: int, layout: PosterLayout, row_first_book_in_year: np.ndarray, col_first_book_in_year: np.ndarray) -> tuple[int,int]:
    if row == row_first_book_in_year[y]:
        start_col = col_first_book_in_year[y]
    else:
        start_col = 0
    if row == row_first_book_in_year[y+1] and start_col < col_first_book_in_year[y+1]:
        end_col = col_first_book_in_year[y+1] - 1
    else:
        end_col = layout.n_books_grid[H] - 1
    return start_col, end_col

def get_grid_index_of_first_books_in_years(books: np.ndarray, layout: PosterLayout) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
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
            row = b // layout.n_books_grid[H]
            col = b % layout.n_books_grid[H]
            row_first_book_in_year.append(row)
            col_first_book_in_year.append(col)
    # Dummy for the end of the grid
    b = b + 1
    years.append(current_year+1)
    row = b // layout.n_books_grid[H]
    col = b % layout.n_books_grid[H]
    row_first_book_in_year.append(row)
    col_first_book_in_year.append(col)
    # np array conversion
    years = np.array(years, dtype=int)
    row_first_book_in_year = np.array(row_first_book_in_year, dtype=int)
    col_first_book_in_year = np.array(col_first_book_in_year, dtype=int)
    return years, row_first_book_in_year, col_first_book_in_year

def create_qr_code(link: str, size_px: int) -> Image:
    import qrcode
    qr = qrcode.QRCode(version=1,box_size=size_px, border=1)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    return img

if __name__ == '__main__':
    main()

# Future work:
# TODO: Add a shadow to the books (plot blurred rectangle first, use mask to blurr selectively? or paste blurred image?)
# TODO: Font color options
# TODO: Update class structure


import warnings
from datetime import datetime
import sys
import os
from os.path import exists
import urllib
import numpy as np
from PIL import Image, ImageDraw
import poster_config
from Dimensions_file import Dimensions
import layout_generator
from book_loader import Book_loader
from year_shader import Year_shader
from auxiliary_text_creator import Auxiliary_text_creator
from constants import *


def main() -> None:
    """Creates a poster with the book covers of a 'read' shelf on goodreads using RSS feeds"""
    check_python_version()
    # List of RSS-feeds to use
    # Warning: Goodreads only supports upto 100 books per rss feed!
    #          Recommended: To get the 100 books you read last, add '&sort=user_read_at' at the end of the rss url.
    #          For posters with more than 100 books, split shelves into shelves with less than 100 books.
    #          Duplicates are eliminated.
    layout = layout_generator.PosterLayoutCreator().create_poster_layout()
    config = poster_config.Config()
    rss_urls = read_rss_urls(config.input_rss_file)
    creator = Book_poster_creator(layout, config, rss_urls)
    creator.create_poster_image()


def read_rss_urls(input_rss_file: str) -> list[str]:
    with open(input_rss_file) as f:
        rss_urls = [
            line.strip().strip("-,.:;!#$%^&*_=+<>'\" ") for line in f.readlines()
        ]
    rss_urls = [line for line in rss_urls if line]  # removes empty lines
    for line in rss_urls:
        if "&sort=" not in line:
            line += "&sort=user_read_at"
        if "/list_rss/" not in line and "/list/" in line:
            line = "".join(
                line.split("/list/")[0], "/list_rss/", line.split("/list/")[1]
            )
    return rss_urls


class Book_poster_creator:
    def __init__(
        self,
        layout: layout_generator.PosterLayout,
        config: poster_config.Config,
        rss_urls: list[str],
    ) -> None:
        self.layout = layout
        self.config = config
        self.user_profile_link = self.get_user_profile_link_from_rss(rss_urls[0])
        loader = Book_loader(self.config)
        self.books = loader.get_list_of_books(rss_urls)
        # Eliminate books that do not fit on the poster (for the given grid size)
        self.filter_books_by_grid_size()
        # Download the book covers from Goodreads
        self.download_covers()

    def get_user_profile_link_from_rss(self, rss_url: str) -> str:
        user_id = int(rss_url.split("?")[0].split("/")[-1])
        return f"https://www.goodreads.com/user/show/{user_id}"

    def filter_books_by_grid_size(self) -> None:
        if self.books.size > self.layout.grid.n_books_total:
            warnings.warn(
                f"Warning: The current poster grid only supports {self.layout.grid.n_books_total} books. {self.books.size - self.layout.grid.n_books_total} books are not included.",
                DeprecationWarning,
            )
            # Removing the first books to only include the books read last in the poster.
            self.books = self.books[-self.layout.grid.n_books_total :]
            self.config.start_date = datetime.strptime(
                self.books[0]["user_read_at"], "%a, %d %b %Y %H:%M:%S %z"
            )

    def download_covers(
        self, COVER_URL_KEY: str = "book_large_image_url", PATH_TO_COVERS="./covers"
    ) -> None:
        """Downloading the book covers from goodreads (if not downloaded already)"""
        print(f"Downloading missing covers of {int(self.books.size)} books...")
        if not exists(PATH_TO_COVERS):
            os.mkdir(PATH_TO_COVERS)
        for book in self.books:
            if not exists(self.get_cover_filename(book)):
                urllib.request.urlretrieve(
                    book[COVER_URL_KEY], self.get_cover_filename(book, PATH_TO_COVERS)
                )
        print("Done!")

    def get_cover_filename(self, book: dict, PATH_TO_COVERS="./covers") -> str:
        """Get the path to the cover image of the book"""
        return f'{PATH_TO_COVERS}/{book["book_id"]}.jpg'

    def create_poster_image(self) -> None:
        """Creating the poster image with the book covers and read date"""

        # Create a blank poster
        print("Creating poster...")
        poster_image = Image.new(
            "RGB",
            self.layout.poster.dim.dim_px,
            self.layout.poster.background_color_hex,
        )
        draw = ImageDraw.Draw(poster_image)

        # Object for adding the title and signature/footer text to the poster
        if self.layout.title.enable or self.layout.signature.enable:
            text_creator = Auxiliary_text_creator(self.layout, self.config)
        # Adding the title
        if self.layout.title.enable:
            text_creator.add_title(draw)
        # Adding the signature
        if self.layout.signature.enable:
            user_name = self.books[0]["user_name"]
            text_creator.add_left_signature(
                self.user_profile_link, poster_image, draw, user_name=user_name
            )
            text_creator.add_right_signature(poster_image, draw)

        # Adding shading for the years to the poster
        if self.layout.year_shading:
            shader = Year_shader(self.layout)
            shader.shade_years(self.books, draw)

        # Populate the poster with book covers and titles
        print("Adding books to poster...")
        for book_index, book in enumerate(self.books):
            # Check if the grid is already full
            assert (
                book_index + 1 <= self.layout.grid.n_books_total
            ), "More books than the poster can handle!"

            # Grid position of the current cover
            row, col = self.grid_position(book_index)

            # Add book cover to the poster
            self.add_cover_to_poster(poster_image, draw, book, row, col)

            # Add book-specific information below the cover
            self.add_book_text(draw, book, row, col)

        # Save the poster
        print("Saving Poster...")
        poster_image.save(self.config.output_file)
        print("Done!")

    def grid_position(self, i):
        row = i // self.layout.grid.n_books[H]
        col = i % self.layout.grid.n_books[H]
        return row, col

    def add_book_text(self, draw, book, row, col):
        # Add book-specific information below the cover
        # Available information in book (examples): 'title', 'author_name', 'book_published', 'num_pages', 'average_rating', 'user_rating', 'user_read_at', 'user_date_created', 'user_date_added'
        if book["user_read_at"] != "":
            text, align_multiline = self.config.get_book_str(book)
            text_position = self.layout.get_cover_text_position(
                col, row, [text], line_index=0
            )
            draw.text(
                text_position.dim_px,
                text,
                fill="black",
                font=self.layout.book.font,
                align=align_multiline,
                anchor="ma",
            )

    def add_cover_to_poster(self, poster_image, draw, book, row, col) -> None:
        # Load cover image
        cover_image = Image.open(self.get_cover_filename(book))
        # Resizing cover image
        cover_image = self.resize_cover_image(cover_image)
        cover_size = Dimensions(
            cover_image.size[0], cover_image.size[1], unit="px", dpi=self.layout.dpi
        )
        # Adding the cover to the poster
        cover_position = self.layout.get_cover_position(col, row, cover_size)
        poster_image.paste(cover_image, cover_position.dim_px)

        # Additing an outline to the cover
        draw.rectangle(
            (
                cover_position.dim_px,
                tuple(cover_position.dim_px[i] + cover_image.size[i] for i in range(2)),
            ),
            fill=None,
            width=int(cover_image.size[H] / 200.0),
            outline="black",
        )

    def resize_cover_image(
        self, cover_image: Image.Image
    ) -> tuple[Image.Image, tuple[int, int]]:
        """Resampling the cover images with the appropriate resolution"""
        aspect_ratio = cover_image.size[H] / cover_image.size[V]
        # If the cover's aspect ratio is similar to the optimal aspect ratio, the cover is stretched.
        if (
            np.maximum(
                aspect_ratio / self.layout.book.default_aspect_ratio,
                self.layout.book.default_aspect_ratio / aspect_ratio,
            )
            < self.config.aspect_ratio_stretch_tolerance
        ):
            cover_image_size = self.layout.book.cover_area.dim_px
        elif self.layout.book.default_aspect_ratio < aspect_ratio:
            cover_image_size = (
                self.layout.book.cover_area.width_px,
                np.round(self.layout.book.cover_area.width_px / aspect_ratio).astype(
                    int
                ),
            )
        else:
            cover_image_size = (
                np.round(self.layout.book.cover_area.height_px() * aspect_ratio).astype(
                    int
                ),
                self.layout.book.cover_area.height_px(),
            )
        cover_image = cover_image.resize(cover_image_size, Image.BICUBIC)
        return cover_image



def check_python_version():
    if sys.version_info[0] != 3 or sys.version_info[1] < 12:
        warnings.warn("This script may require Python version 3.12.")

if __name__ == "__main__":
    main()

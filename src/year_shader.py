from datetime import datetime
import numpy as np
from PIL import ImageDraw
from typing import Tuple
import layout_generator
from constants import *


class Year_shader:
    def __init__(self, layout: layout_generator.PosterLayout) -> None:
        self.layout = layout

    def shade_years(self, books: np.ndarray, draw: ImageDraw) -> None:
        years, row_first_book_in_year, col_first_book_in_year = (
            self.get_grid_index_of_first_books_in_years(books)
        )
        for y in range(years.size - 1):
            for row in range(
                row_first_book_in_year[y], row_first_book_in_year[y + 1] + 1
            ):
                start_col, end_col = self.get_grid_col_indices_in_row(
                    row, y, row_first_book_in_year, col_first_book_in_year
                )
                if (
                    (row == row_first_book_in_year[y + 1])
                    and (end_col == self.layout.grid.n_books[H] - 1)
                ) or (row >= self.layout.grid.n_books[V]):
                    continue
                color = (
                    self.layout.year_shading.color1_hex
                    if y % 2 == 0
                    else self.layout.year_shading.color2_hex
                )
                if color != self.layout.poster.background_color_hex:
                    start_position = self.layout.get_shading_start_position(
                        start_col, row
                    )
                    end_position = self.layout.get_shading_end_position(end_col, row)
                    draw.rectangle(
                        (start_position.xy_px, end_position.xy_px),
                        fill=color,
                        outline=None,
                    )

    def get_grid_col_indices_in_row(
        self,
        row: int,
        y: int,
        row_first_book_in_year: np.ndarray,
        col_first_book_in_year: np.ndarray,
    ) -> Tuple[int, int]:
        if row == row_first_book_in_year[y]:
            start_col = col_first_book_in_year[y]
        else:
            start_col = 0
        if (
            row == row_first_book_in_year[y + 1]
            and start_col < col_first_book_in_year[y + 1]
        ):
            end_col = col_first_book_in_year[y + 1] - 1
        else:
            end_col = self.layout.grid.n_books[H] - 1
        return start_col, end_col

    def get_grid_index_of_first_books_in_years(
        self, books: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        # Add first book/year
        years = [
            int(
                datetime.strptime(
                    books[0]["user_read_at"], "%a, %d %b %Y %H:%M:%S %z"
                ).year
            ),
        ]
        row_first_book_in_year = [
            0,
        ]
        col_first_book_in_year = [
            0,
        ]
        for b, book in enumerate(books):
            if b == 0:  # already added
                continue
            current_year = int(
                datetime.strptime(book["user_read_at"], "%a, %d %b %Y %H:%M:%S %z").year
            )
            if years[-1] < current_year:  # New year
                years.append(current_year)
                # Grid position of the current cover
                row_first_book_in_year.append(b // self.layout.grid.n_books[H])
                col_first_book_in_year.append(b % self.layout.grid.n_books[H])
        # Dummy for the end of the grid
        b = b + 1
        years.append(current_year + 1)
        row_first_book_in_year.append(b // self.layout.grid.n_books[H])
        col_first_book_in_year.append(b % self.layout.grid.n_books[H])

        years = np.array(years, dtype=int)
        row_first_book_in_year = np.array(row_first_book_in_year, dtype=int)
        col_first_book_in_year = np.array(col_first_book_in_year, dtype=int)
        return years, row_first_book_in_year, col_first_book_in_year
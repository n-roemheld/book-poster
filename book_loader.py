from datetime import datetime
import numpy as np
import feedparser
import poster_config

class Book_loader:
    def __init__(self, config: poster_config.Config):
        self.config = config

    def get_list_of_books(self, rss_urls):
        # Loading feeds
        books = self.load_feeds(rss_urls)
        # Reordering books by read date
        books, read_at_list = self.sort_books(books)
        # Excluding books read before start_date
        books = self.filter_books_by_date(
            books, read_at_list, self.config.start_date, self.config.end_date
        )
        return books

    def load_feeds(self, rss_urls: list) -> np.ndarray:
        """Downloading the RSS feed and converting it to an array of books"""
        print("Loading feeds...")
        books = np.atleast_1d(np.array([]))
        for i, url in enumerate(rss_urls):
            feed = feedparser.parse(url)
            print(f"Feed {i}:", feed.feed.title)
            books_from_feed = np.array(feed.entries)
            books = np.concatenate((books, books_from_feed))
        books = np.array(
            list({b["book_id"]: b for b in books}.values())
        )  # removing duplicates
        if books.size == 0:
            exit("No books found in the feeds. Please check the feeds and try again.")
        return books

    def sort_books(self, books: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Reordering books by read date"""
        read_at_list = []
        for book in books:
            if book["user_read_at"] == "":  # no read date entered
                read_at_list.append(self.config.DEFAULT_READ_DATE)
            else:
                read_at_list.append(
                    datetime.strptime(book["user_read_at"], "%a, %d %b %Y %H:%M:%S %z")
                )
        read_at_list = np.array(read_at_list)
        order = np.argsort(read_at_list).astype(int)
        books = books[order]
        read_at_list = read_at_list[order]
        return books, read_at_list

    def filter_books_by_date(
        self,
        books: np.ndarray,
        read_at_list: np.ndarray,
        start_date: datetime,
        end_date: datetime,
    ) -> np.ndarray:
        """Excluding books read before start_date"""
        try:
            start_index = np.where(start_date <= read_at_list)[0][0]
            end_index = np.where(read_at_list <= end_date)[0][-1]
        except IndexError:
            exit(
                f"No books read between {start_date.date()} and {end_date.date()}. Please check the feeds and your date constraints and try again."
            )
        read_at_list = read_at_list[start_index : end_index + 1]
        books = books[start_index : end_index + 1]
        return books
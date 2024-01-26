from datetime import datetime, timezone
from dataclasses import dataclass

@ dataclass 
class Config():
    DEFAULT_READ_DATE = datetime(year=1900, month=1, day=1, tzinfo=timezone.utc)

    input_rss_file:         str                 = "rss_urls.txt"
    output_file:            str                 = "poster.jpg"

    # Start date
    # Only books read after this date are included  
    start_date = datetime(year=2015, month=1, day=1, tzinfo=timezone.utc)
    # End date
    # Only books read before this date are included  
    # end_date = datetime(year=2022, month=1, day=1, tzinfo=timezone.utc)
    end_date = datetime.now(timezone.utc).astimezone() # Now in local timezone

    credit_str = 'Created with the\nBook Poster Creator by N. Römheld'
    credit_url = 'https://github.com/n-roemheld/book-poster'

    def get_title_str(self):
        return f'Books read between {str(self.start_date.date())} and {str(self.end_date.date())}'
    
    def get_book_str(self, book: dict) -> tuple[str, str]:
        # Available information in book (examples): 
        # 'title', 'author_name', 'book_published', 'num_pages', 'average_rating', 'user_rating', 
        # 'user_read_at', 'user_date_created', 'user_date_added'
        read_date_str = str(datetime.strptime(book['user_read_at'], '%a, %d %b %Y %H:%M:%S %z').date()) if book['user_read_at'] else ''
        goodreads_rating =  f'{float(book["average_rating"]):.1f}' + u"\u2606"
        user_rating =  f'{book["user_rating"]}' + u"\u2605" if int(book['user_rating']) else ''
        rating_str = user_rating if int(book['user_rating']) else goodreads_rating
        n_pages_str = f'{book["num_pages"]} pages' if book['num_pages'] else ''
        book_str = f'Read {read_date_str}\n{n_pages_str} {goodreads_rating} {user_rating}'
        align_multiline = 'center'
        return book_str, align_multiline
    
    def get_num_book_text_lines(self) -> int:
        dummy_book = {
            'title':             '', 
            'author_name':       '', 
            'book_published':    'Sat, 1 Jan 2000 00:00:00 +0000', 
            'num_pages':         '0', 
            'average_rating':    '0', 
            'user_rating':       '0', 
            'user_read_at':      'Sat, 1 Jan 2000 00:00:00 +0000', 
            'user_date_created': 'Sat, 1 Jan 2000 00:00:00 +0000', 
            'user_date_added':   'Sat, 1 Jan 2000 00:00:00 +0000',
            }
        book_str, _ = self.get_book_str(dummy_book)
        num_lines = len(book_str.split('\n'))
        return num_lines



if __name__ == '__main__':
    from book_poster_creator import main
    main()
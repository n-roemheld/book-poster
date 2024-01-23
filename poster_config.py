from datetime import datetime, timezone
from dataclasses import dataclass

@ dataclass 
class Config():
    # Start date
    # Only books read after this date are included  
    start_date = datetime(year=2015, month=1, day=1, tzinfo=timezone.utc)
    # End date
    # Only books read before this date are included  
    # end_date = datetime(year=2022, month=1, day=1, tzinfo=timezone.utc)
    end_date = datetime.now(tz=timezone.utc)


    credit_str = 'Created with'
    credit_url = 'https://github.com/n-roemheld/book-poster'

    def get_title_str(self):
        title_str = f'Books read between {str(self.start_date.date())} and {str(self.end_date.date())}'
        return title_str


if __name__ == '__main__':
    from book_poster_creator import main
    main()
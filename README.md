# Create a Poster of Read Books from Goodreads
Create a poster with the book covers from your 'read' shelf on goodreads.com. 
General and personal information can be added beneath each cover, like the number of pages, average rating, your rating, and your read date.

![grafik](https://raw.githubusercontent.com/n-roemheld/book-poster/main/output/poster_test.jpg)

# How to use
Get a working [Python installation](https://realpython.com/installing-python/).

Paste the URL of your 'Read' shelf/shelves into the text file `input/shelf_urls_test.txt` and run the `run_windows.bat` on Windows or the `run_linux.sh` on Linux or Mac.
Alternatively, run the Python script directly with `$ Python3 src/book_poster_creator.py`.
In- and output files can be changed in `src/poster_config.py`.
The default output is `output/poster.jpg`.

The settings are located in the `src/poster_cofig.py` file.
Python code tolerance is required.

If you are unhappy with a cover or the number of pages, change the edition of the book on your shelf in Goodreads.

# Caution: Large book shelves
If your 'read' shelf contains more than 100 books, not all desired books may show up. 
This is because the Goodreads RSS feature, which this tool is based on, only supports the export of up to 100 books.
By default, the 100 books with the latest read date are used. 
You can try to change which 100 books are used by adding sorting commands, like `&sort=author`, to the end of the URLs but this is rarely useful.
The start and end dates chosen for the poster do not influence which 100 books are available.

If you want to use books read earlier or more than 100 books on your poster, some additional work is required.
You must copy the books into new book shelves on goodreads with up to 100 books and add them all to the input file.

Best practice: Start making the 100-book shelves with your oldest books. 
Keep your read shelf in the url list together with the others.
Only when there are >100 books in your read shelf that are not in the other shelves, create a new one. 
This way, your latest books are always available for the poster and you only have to create a new shelf every 100 books you read.


# Contributions
Contributions of any kind are welcome!

# Copyright disclaimer
 I do not own any copyrights for the fonts. Original copyrights apply.
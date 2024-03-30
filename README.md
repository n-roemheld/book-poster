# Create a Poster of Read Books from Goodreads
Create a poster with the book covers from your 'read' shelf on goodreads.com. 
General and personal information can be added beneath each cover, like the number of pages, average rating, your rating, and your read date.

![grafik](https://raw.githubusercontent.com/n-roemheld/book-poster/main/poster_test.jpg)

# How to use
Paste the URL of your 'Read' shelf/shelves into the text file `input/shelf_urls_test.txt` and run the `run_windows.bat` on Windows or the `run_linux.sh` on Linux or Mac.
Alternatively, run the `src/book_poster_creator.py` Python script directly.
In- and output files can be changed in `src/poster_config.py`.
The default output is `output/poster.jpg`.

The settings are located in the `src/poster_cofig.py` file.
Python code tolerance is required.

If you are unhappy with a cover or the number of pages, change the edition of the book on your shelf in Goodreads.

**Caution:** If you want to create a poster with more than 100 books, you should split your shelf into multiple shelves with up to 100 books.
This is annoying but necessary since the Goodreads RSS feature, which this tool is based on, only supports up to 100 books.
By default, the 100 books you read last are used. 
You can try to change which books are used by adding sorting commands, like `&sort=author`, to the end of the RSS URL.
The start and end dates chosen for the poster do not influence which 100 books are available.

**Disclaimer:** I do not own any copyrights for the fonts. Original copyrights apply.

# Contributions
Contributions of any kind are welcome!
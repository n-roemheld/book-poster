# Create a Poster of Read Books from Goodreads
Creates a poster with the book covers from your 'read' shelf on goodreads.com with your 'read' date printed beneath each cover.
![grafik](https://raw.githubusercontent.com/n-roemheld/book-poster/main/poster_test.jpg)

# How to use
Paste the URL of your 'Read' shelf/shelves into the text file shelf_urls_test.txt and run the book_poster_creator.py Python script.
In- and output files can be changed in poster_config.py.

Caution: If you want to create a poster with more than 100 books, you should split your shelf into multiple shelves with upto 100 books.
This is annoying but necessary since the Goodreads RSS feature, which this tool is based on, only supports upto 100 books.
By default, the 100 books you read last are used. 
You can try to change which books are used by adding sorting commands, like '&sort=author', to the end of the RSS URL.
The time interval chosen for the poster does not influence which 100 books are available.

The settings and parameters for the poster are located in the poster_cofig.py file.

Note: This was only tested with Python 3.12 yet. Compatibility with earlier Python versions is not guaranteed.
Required modules: feedparser, PIL, numpy

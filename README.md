# Create a Poster of Read Books from Goodreads
Creates a poster with the book covers from your 'read' shelf on goodreads.com with your 'read' date printed beneath each cover.
![grafik](https://raw.githubusercontent.com/n-roemheld/book-poster/main/poster_test.jpg)

# How to use
This tool is based on the goodreads feature to export your shelves as RSS feeds. You can find the button to get the URL for the RSS feed at the bottom of the shelf.
![grafik](https://github.com/n-roemheld/book-poster/assets/57660684/ef690191-168b-4502-9768-82c0bf69b158)
Paste the URL of the feed into the text file rss_urls.txt or rss_urls_test.txt and run the book_poster_creator.py.

However, if you want to create a poster with more than 100 book covers, you should split your shelf into multiple shelves with upto 100 books.
This is annoying but necessary since the RSS export only supports upto 100 books.
If you want to use the 100 books you reast last, you can add '&sort=user_read_at' to the end of the RSS URL.

The other parameters of the poster can be changed in the poster_cofig.py file.
![grafik](https://github.com/n-roemheld/book-poster/assets/57660684/e866df85-e8c6-4c4f-8508-b8eeae1812f9)

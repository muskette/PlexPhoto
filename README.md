# PlexPhoto
Scraper to download all the artwork of media items in a plex server

After switching my primary Plex client to a Chromecast from PlexHomeTheatre, I was disappointed by the minimal amount of screensaver art available on it.  
PHT had a slideshow of artwork and fanart for the TV Shows and Movies on the server, which allows for a large body of images with little repetition.

Chromecast does, however, allow you to use custom artwork if it's part of a Flickr or Google Images album.

Thus, this little script to scrape and download all the images it can from a plex server.
It's still in a very prototype phase.

Next steps:
1. Implement work with a Flickr or Google API to automatically upload the results.
2. Make it work in distinct chunks rather than all or nothing
3. Implement this as a Plex Plugin to reactively update an album when media items are added or removed

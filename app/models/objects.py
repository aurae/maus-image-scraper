from enum import Enum


class ImageFormat(Enum):
    SQUARE = "square"
    TALL = "tall"
    WIDE = "wide"

    @classmethod
    def values(cls):
        return [m.value for m in list(cls)]


class ScrapeRequest(object):

    def __init__(self, query, image_format, page):
        """
        :type query: str
        :type image_format: ImageFormat
        :type page: int
        """
        self.query = query
        self.image_format = image_format
        self.page = page


class ScrapeResponse(object):
    class Item(object):
        def __init__(self, full_url, thumb_url, description, width, height):
            self.full_url = full_url
            self.thumb_url = thumb_url
            self.description = description
            self.width = width
            self.height = height

    def __init__(self):
        self.results = []
        """ :type image_results: list[ScrapeResponse.Item] """


class Scraper(object):
    def scrape_images(self, request):
        """
        Performs a scrape request for Images.
        :type request: ScrapeRequest
        :rtype: ScrapeResponse
        """
        raise NotImplementedError()

from collections import OrderedDict
from urllib.parse import urlencode
import bs4
from flask import json
from frozendict import frozendict
import re

from app.models.objects import Scraper, ScrapeResponse, ImageFormat

BING_BASE_URL = "https://www.bing.com/images/async"

BING_RESULTS_PER_PAGE = 35

BING_IMAGEFORMAT_TO_ASPECTRATIO = frozendict({
    ImageFormat.SQUARE: "+filterui:aspect-square",
    ImageFormat.TALL: "+filterui:aspect-tall",
    ImageFormat.WIDE: "+filterui:aspect-wide",
})


class BingScraper(Scraper):
    """
    Scraper implementation for Bing Image Search results.
    """

    def __init__(self, http_client):
        """
        :type http_client: app.models.http.HttpClient 
        """
        self.http_client = http_client

    def scrape_images(self, request):
        """
        :type request: app.models.ScrapeRequest
        :rtype: ScrapeResponse
        """
        # Compose request to Bing's Image Service
        query_string = {
            "q": request.query,
            "first": 1 + (request.page - 1) * BING_RESULTS_PER_PAGE,
            "count": BING_RESULTS_PER_PAGE,
        }

        if request.image_format:
            query_string["qft"] = BING_IMAGEFORMAT_TO_ASPECTRATIO[request.image_format]

        bing_url = BING_BASE_URL + "?" + urlencode(OrderedDict(query_string))

        # Fire the request and obtain the response
        bing_response = self.http_client.get(bing_url)
        return self._parse_images_response(bing_response.data)

    def _parse_images_response(self, data):
        """
        :param data: Data from the Bing call 
        :rtype: ScrapeResponse
        """
        response = ScrapeResponse()

        # Bing images can be extracted by their container's class from the HTML
        soup = bs4.BeautifulSoup(data, "html.parser")
        image_tags = soup.find_all("a", class_="iusc")
        """:type: list[bs4.element.Tag]"""

        for image_tag in image_tags:
            # Aggregate each portion of an image from its different sources in the HTML source;
            # in case of malformed data, a ValueError is raised, and the item discarded
            try:
                media_url = self._extract_media_url(image_tag)
                thumbnail_url = self._extract_thumbnail_url(image_tag)
                description, width, height = self._extract_description_and_dimensions(image_tag)

                response.results.append(ScrapeResponse.Item(
                    full_url=media_url,
                    thumb_url=thumbnail_url or media_url,
                    description=description,
                    width=width,
                    height=height
                ))

            except ValueError as e:
                print(e)
                continue

        return response

    def _extract_media_url(self, image_tag):
        """
        :type image_tag: bs4.element.Tag
        :rtype: str
        :raises: ValueError
        """
        # The media URL is JSON-encoded inside the tag
        img_media_json = image_tag.get("m")
        if not img_media_json:
            # Discard images without a media blob
            raise ValueError()

        img_media = json.loads(img_media_json)
        img_full_url = img_media.get("murl", "")

        if not img_full_url:
            # Don't bother with malformed images
            raise ValueError()

        return img_full_url

    def _extract_thumbnail_url(self, image_tag):
        """
        :type image_tag: bs4.element.Tag
        :rtype: str
        :raises: ValueError
        """
        # Find thumbnail URL from a nested img tag
        img_thumb_tag = image_tag.find("img")
        if img_thumb_tag:
            img_thumb_url = img_thumb_tag.get("data-src", "")
        else:
            img_thumb_url = None

        return img_thumb_url

    def _extract_description_and_dimensions(self, image_tag):
        """
        :type image_tag: bs4.element.Tag
        :rtype: tuple[str, int, int]
        :raises: ValueError
        """
        # Obtain dimensions & description from neighboring tags.
        # Expect the first list item to hold the image's dimensions,
        # and the second one to hold the website
        img_info = image_tag.find_next("ul", class_="b_dataList")
        img_info_parts = img_info.find_all("li")
        """:type: list[bs4.element.Tag]"""

        if len(img_info_parts) > 0:
            img_dimen_text = img_info_parts[0].text
            img_dimen_match = re.match("(\d+) x (\d+).*", img_dimen_text)

            img_width = int(img_dimen_match.group(1))
            img_height = int(img_dimen_match.group(2))
        else:
            img_width = 0
            img_height = 0

        if len(img_info_parts) > 1:
            # Long websites get truncated, therefore make sure to unwrap a span, if any
            img_desc = img_info_parts[1]
            img_desc_span = img_desc.find("span")
            if img_desc_span:
                img_description = img_desc_span.get("title")
            else:
                img_description = img_desc.text
        else:
            img_description = ""

        return img_description, img_width, img_height

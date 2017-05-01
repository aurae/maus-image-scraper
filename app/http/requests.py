import requests
import requests_cache

from app.models.http import HttpClient, HttpResponse


class RequestsHttpClient(HttpClient):
    def __init__(self):
        requests_cache.install_cache()

    def post(self, url, data):
        response = requests.post(url, json=data)
        return self._convert(response)

    def get(self, url):
        response = requests.get(url)
        return self._convert(response)

    def _convert(self, response):
        """
        :type response: requests.Response
        :rtype: HttpResponse
        """
        return HttpResponse(data=response.content, code=response.status_code)

class HttpResponse(object):
    def __init__(self, data, code):
        self.data = data
        self.code = code


class HttpClient(object):
    def post(self, url, data):
        """
        :type url: str
        :type data: dict
        :rtype: HttpResponse
        """
        raise NotImplementedError()

    def get(self, url):
        """
        :type url: str
        :rtype: HttpResponse
        """
        raise NotImplementedError()

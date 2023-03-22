from urllib.parse import urlencode, urlunsplit

from django.urls import reverse


class ViewTestMixin:
    def get(self, *args, **kwargs):
        return self.make_request("get", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.make_request("post", *args, **kwargs)

    def make_request(
        self, request_method, url=None, *args, client=None, expected_status, **kwargs
    ):
        if client is None:
            client = self.client
        if url is None:
            url = self.get_url()
        response = getattr(client, request_method)(url, *args, **kwargs)
        self.assertEqual(response.status_code, expected_status)
        return response

    def get_url(self, *args, path=None, query=None, **kwargs):
        try:
            return self.url
        except AttributeError:
            pass
        if path is None:
            path = self.get_url_path(*args, **kwargs)
        path = str(path)
        if query is None:
            query = {}
        query_string = urlencode(query, doseq=True)
        return urlunsplit(["", "", path, query_string, ""])

    def get_url_path(self, *args, **kwargs):
        try:
            return self.url_path
        except AttributeError:
            pass
        return self.get_reversed_url(*args, **kwargs)

    def get_reversed_url(self, *args, pattern_name=None, reverse_kwargs=None, **kwargs):
        if pattern_name is None:
            pattern_name = self.get_url_pattern_name()
        args = self.get_url_pattern_args(*args) or None
        kwargs = self.get_url_pattern_kwargs(**kwargs) or None
        if reverse_kwargs is None:
            reverse_kwargs = {}
        return reverse(pattern_name, args=args, kwargs=kwargs, **reverse_kwargs)

    def get_url_pattern_name(self):
        return self.url_pattern_name

    def get_url_pattern_args(self, *args):
        return args

    def get_url_pattern_kwargs(self, **kwargs):
        return kwargs

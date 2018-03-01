import sys

from tornado import gen, ioloop
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.queues import Queue
import time
import httputil


class AsyncRequester():

    def __init__(self, destinations=None, transform=None, headers={}, max_clients=50, maxsize=50, connect_timeout=1200, request_timeout=600,
            result_queue=None):

        """Instantiate a tornado async http client to do multiple concurrent requests"""

        if None in [destinations, transform]:
            sys.stderr.write('You must pass both collection of URLS and a transform function')
            raise SystemExit

        self.max_clients = max_clients
        self.maxsize = maxsize
        self.connect_timeout = connect_timeout
        self.request_timeout = request_timeout
        self.result_queue = result_queue
        AsyncHTTPClient.configure("tornado.simple_httpclient.SimpleAsyncHTTPClient", max_clients=self.max_clients)

        self.http_client = AsyncHTTPClient()
        self.queue = Queue(maxsize=maxsize)
        self.destinations = destinations
        self.transform = transform

        self.headers = headers
        self.read(self.destinations)
        self.get()
        self.loop = ioloop.IOLoop.current()
        self.loop.spawn_callback(self.get)
        self.loop.spawn_callback(self.get)
        self.loop.spawn_callback(self.get)
        self.join_future = self.queue.join()

        def done(future):
            self.loop.stop()

        self.count = 1
        self.join_future.add_done_callback(done)
        self.loop.start()

    @gen.coroutine
    def read(self, destinations):
        for url in destinations:
            yield self.queue.put(url)

    @gen.coroutine
    def get(self):
        couterino = 1
        while True:
            url = yield self.queue.get()
            try:
                request = HTTPRequest(url, connect_timeout=self.connect_timeout, request_timeout=self.request_timeout, method="GET",
                                      headers=self.headers)
            except Exception as e:
                sys.stderr.write('Destination {0} returned error {1}'.format(url, str(e) + '\n'))

            future = self.http_client.fetch(request)

            def done_callback(future):
                url = future.result().effective_url
                try:
                    body = future.result().body

                    self.transform(body, url=url)
                    self.count = self.count + 1
                except Exception as e:
                    print(e)
                    print(url)
                self.queue.task_done()

            try:
                couterino += 1
                future.add_done_callback(done_callback)
            except Exception as e:
                sys.stderr.write(str(e))
                self.queue.put(url)


class CustomHTTPRequest(HTTPRequest):
    """We're going to subclass HTTPRequest"""

    _DEFAULTS = dict(connect_timeout=20.0, request_timeout=20.0, follow_redirects=True, max_redirects=5, decompress_response=True, proxy_password='',
            allow_nonstandard_methods=False, validate_cert=True)

    def __init__(self, url, method="GET", headers=None, body=None, auth_username=None, auth_password=None, auth_mode=None, connect_timeout=None,
                 request_timeout=None, if_modified_since=None, follow_redirects=None, max_redirects=None, user_agent=None, use_gzip=None,
                 network_interface=None, streaming_callback=None, header_callback=None, prepare_curl_callback=None, proxy_host=None, proxy_port=None,
                 proxy_username=None, proxy_password=None, proxy_auth_mode=None, allow_nonstandard_methods=None, validate_cert=None, ca_certs=None,
                 allow_ipv6=None, client_key=None, client_cert=None, body_producer=None, expect_100_continue=False, decompress_response=None,
                 ssl_options=None, key=None):

        self.headers = headers
        if if_modified_since:
            self.headers["If-Modified-Since"] = httputil.format_timestamp(if_modified_since)
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        self.proxy_auth_mode = proxy_auth_mode
        self.url = url
        self.method = method
        self.body = body
        self.body_producer = body_producer
        self.auth_username = auth_username
        self.auth_password = auth_password
        self.auth_mode = auth_mode
        self.connect_timeout = connect_timeout
        self.request_timeout = request_timeout
        self.follow_redirects = follow_redirects
        self.max_redirects = max_redirects
        self.user_agent = user_agent
        self.key = key
        if decompress_response is not None:
            self.decompress_response = decompress_response
        else:
            self.decompress_response = use_gzip
        self.network_interface = network_interface
        self.streaming_callback = streaming_callback
        self.header_callback = header_callback
        self.prepare_curl_callback = prepare_curl_callback
        self.allow_nonstandard_methods = allow_nonstandard_methods
        self.validate_cert = validate_cert
        self.ca_certs = ca_certs
        self.allow_ipv6 = allow_ipv6
        self.client_key = client_key
        self.client_cert = client_cert
        self.ssl_options = ssl_options
        self.expect_100_continue = expect_100_continue
        self.start_time = time.time()


class Scraper():

    def __init__(self, request_params=[{}], max_clients=100, maxsize=100, connect_timeout=9999999, request_timeout=9999999, auth_username=None,
            auth_password=None, method='GET', func=None, sleep=0, endpoint=None):
        self.sleep = sleep
        self.endpoint = endpoint
        """Instantiate a tornado async http client to do multiple concurrent requests"""
        self.max_clients = max_clients
        AsyncHTTPClient.configure("tornado.simple_httpclient.SimpleAsyncHTTPClient", max_clients=self.max_clients)
        self.request_params = request_params
        self.method = method

        self.maxsize = maxsize
        self.auth_username = auth_username
        self.auth_password = auth_password
        self.connect_timeout = connect_timeout
        self.request_timeout = request_timeout
        self.to_return = []

        self.http_client = AsyncHTTPClient()
        self.queue = Queue(maxsize=self.maxsize)
        self.func = func
        self.read(self.request_params)
        self.get(self.connect_timeout, self.request_timeout, self.http_client)
        self.loop = ioloop.IOLoop.current()
        self.join_future = self.queue.join()

        def done(future):
            self.loop.stop()

        self.join_future.add_done_callback(done)
        self.loop.start()

    @gen.coroutine
    def read(self, request_params):
        for request_param in request_params:
            yield self.queue.put(request_param)

    @gen.coroutine
    def get(self, connect_timeout, request_timeout, http_client):
        print("Getting Links")
        self.counter = 1
        while True:
            request_param = yield self.queue.get()
            url = request_param.get('url', self.endpoint)
            body = request_param.get('body', None)
            dictKey = request_param['dictKey']
            # request_param['headers']['dictKey'] = dictKey
            request = CustomHTTPRequest(url, method=self.method, headers=request_param['headers'], body=body, connect_timeout=connect_timeout,
                    request_timeout=request_timeout, auth_username=self.auth_username, auth_password=self.auth_password, key=dictKey)

            def handle_response(response):
                if not self.func:
                    if response.error:
                        self.to_return.append({'key': response.request.__dict__['key'], 'response': str(response.error)})
                    else:
                        self.to_return.append({'key': response.request.__dict__['key'], 'response': response.body})
                else:
                    try:
                        self.func(response.body, response.request.__dict__['key'])
                    except Exception as e:
                        pass
                # print(self.counter)
                self.counter += 1
                self.queue.task_done()

            future = self.http_client.fetch(request, handle_response)

            time.sleep(self.sleep)

    def return_results(self):
        return self.to_return

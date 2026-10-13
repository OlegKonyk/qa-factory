# -*- encoding: utf-8 -*-

import json
import os
import tempfile
import unittest

from werkzeug.wrappers import Response

from isso import Isso, core, config
from isso.utils import http

from fixtures import curl, loads, FakeIP, JSONClient

http.curl = curl


class TestNoCacheCommentViews(unittest.TestCase):
    """GET / and GET /id/<id> tell every cache not to store successful responses."""

    maxDiff = None

    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        conf = config.load(config.default_file())
        conf.set("general", "dbpath", self.path)
        conf.set("guard", "enabled", "off")
        conf.set("hash", "algorithm", "none")
        conf.set("general", "latest-enabled", "true")
        self.conf = conf

        class App(Isso, core.Mixin):
            pass

        self.app = App(conf)
        self.app.wsgi_app = FakeIP(self.app.wsgi_app, "192.168.1.1")

        self.client = JSONClient(self.app, Response)
        self.get = self.client.get
        self.put = self.client.put
        self.post = self.client.post
        self.delete = self.client.delete

    def tearDown(self):
        os.unlink(self.path)

    def postThread(self):
        """A root comment (id 1) and a reply to it (id 2) on /path/."""
        a = self.post(
            "/new?uri=%2Fpath%2F",
            data=json.dumps({"text": "Hello *world*", "author": "Ada", "website": "https://example.org/"}),
        )
        self.assertEqual(a.status_code, 201)
        b = self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "A reply", "parent": 1}))
        self.assertEqual(b.status_code, 201)

    def assertNoStore(self, rv):
        self.assertEqual(rv.headers.getlist("Cache-Control"), ["no-store"])

    def statusAndCacheControl(self, queries):
        """GET each query; map it to its status code and its Cache-Control values."""
        seen = {}
        for query in queries:
            rv = self.get(query)
            seen[query] = (rv.status_code, rv.headers.getlist("Cache-Control"))
        return seen

    def testListingOfThreadWithCommentIsNoStore(self):
        self.postThread()

        rv = self.get("/?uri=%2Fpath%2F")

        self.assertEqual(rv.status_code, 200)
        self.assertNoStore(rv)

    def testListingWithEachQueryParameterIsNoStore(self):
        self.postThread()

        queries = [
            "/?uri=%2Fpath%2F&sort=oldest",
            "/?uri=%2Fpath%2F&sort=newest",
            "/?uri=%2Fpath%2F&sort=upvotes",
            "/?uri=%2Fpath%2F&limit=1",
            "/?uri=%2Fpath%2F&limit=0",
            "/?uri=%2Fpath%2F&limit=1&offset=1",
            "/?uri=%2Fpath%2F&parent=1",
            "/?uri=%2Fpath%2F&nested_limit=0",
            "/?uri=%2Fpath%2F&nested_limit=1",
            "/?uri=%2Fpath%2F&plain=1",
            "/?uri=%2Fpath%2F&after=0",
            "/?uri=%2Fpath%2F&sort=newest&limit=1&offset=0&nested_limit=1&plain=1&after=0",
            "/?uri=%2Fempty%2F",
        ]

        self.assertEqual(self.statusAndCacheControl(queries), {query: (200, ["no-store"]) for query in queries})

    def testViewWithEditCookieIsNoStoreWithAndWithoutPlain(self):
        self.postThread()

        queries = ["/id/1", "/id/1?plain=1"]

        self.assertEqual(self.statusAndCacheControl(queries), {query: (200, ["no-store"]) for query in queries})

    def testErrorResponsesCarryNoCacheControl(self):
        self.postThread()

        rv = self.get("/?uri=%2Fpath%2F&sort=bogus")
        self.assertEqual(rv.status_code, 400)
        self.assertNotIn("Cache-Control", rv.headers)

        rv = self.get("/id/99")
        self.assertEqual(rv.status_code, 404)
        self.assertNotIn("Cache-Control", rv.headers)

        # a client that never posted holds no edit cookie for comment 1
        rv = JSONClient(self.app, Response).get("/id/1")
        self.assertEqual(rv.status_code, 403)
        self.assertNotIn("Cache-Control", rv.headers)

    def testListingAndViewBodiesAreUnchanged(self):
        self.postThread()

        rv = self.get("/?uri=%2Fpath%2F")
        self.assertEqual(rv.status_code, 200)
        listing = loads(rv.data)
        for key in ["id", "total_replies", "hidden_replies", "replies", "config"]:
            self.assertIn(key, listing)
        self.assertIsNone(listing["id"])
        self.assertEqual(listing["total_replies"], 2)
        self.assertEqual(listing["hidden_replies"], 0)
        self.assertEqual(len(listing["replies"]), 1)

        root = listing["replies"][0]
        for key in ["id", "parent", "text", "author", "website", "mode", "total_replies", "hidden_replies", "replies"]:
            self.assertIn(key, root)
        self.assertEqual(root["id"], 1)
        self.assertIsNone(root["parent"])
        self.assertEqual(root["text"], "<p>Hello <em>world</em></p>")
        self.assertEqual(root["author"], "Ada")
        self.assertEqual(root["website"], "https://example.org/")
        self.assertEqual(root["mode"], 1)
        self.assertEqual(root["total_replies"], 1)
        self.assertEqual(root["hidden_replies"], 0)
        self.assertEqual(len(root["replies"]), 1)

        reply = root["replies"][0]
        for key in ["id", "parent", "text"]:
            self.assertIn(key, reply)
        self.assertEqual(reply["id"], 2)
        self.assertEqual(reply["parent"], 1)
        self.assertEqual(reply["text"], "<p>A reply</p>")

        rv = self.get("/id/1")
        self.assertEqual(rv.status_code, 200)
        comment = loads(rv.data)
        for key in ["id", "parent", "text", "author", "website", "mode", "likes", "dislikes"]:
            self.assertIn(key, comment)
        self.assertEqual(comment["id"], 1)
        self.assertIsNone(comment["parent"])
        self.assertEqual(comment["text"], "<p>Hello <em>world</em></p>")
        self.assertEqual(comment["author"], "Ada")
        self.assertEqual(comment["website"], "https://example.org/")
        self.assertEqual(comment["mode"], 1)
        self.assertEqual(comment["likes"], 0)
        self.assertEqual(comment["dislikes"], 0)

        rv = self.get("/id/1?plain=1")
        self.assertEqual(rv.status_code, 200)
        comment = loads(rv.data)
        self.assertIn("text", comment)
        self.assertEqual(comment["text"], "Hello *world*")

    def testOtherRoutesDoNotGetNoStore(self):
        rv = self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Lorem ipsum ..."}))
        self.assertEqual(rv.status_code, 201)
        self.assertNotIn("Cache-Control", rv.headers)

        rv = self.put("/id/1", data=json.dumps({"text": "Edited"}))
        self.assertEqual(rv.status_code, 200)
        self.assertNotIn("Cache-Control", rv.headers)

        rv = self.post("/count", data=json.dumps(["/path/"]))
        self.assertEqual(rv.status_code, 200)
        self.assertNotIn("Cache-Control", rv.headers)

        rv = self.get("/latest?limit=5")
        self.assertEqual(rv.status_code, 200)
        self.assertNotIn("Cache-Control", rv.headers)

        rv = self.get("/config")
        self.assertEqual(rv.status_code, 200)
        self.assertNotIn("Cache-Control", rv.headers)

        # last: deleting clears the edit cookie
        rv = self.delete("/id/1")
        self.assertEqual(rv.status_code, 200)
        self.assertNotIn("Cache-Control", rv.headers)

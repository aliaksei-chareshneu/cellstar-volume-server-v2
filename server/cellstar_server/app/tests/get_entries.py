import unittest

import requests
from cellstar_server.app.tests._test_server_runner import ServerTestBase


class FetchEntriesTest(ServerTestBase):
    def test(self):
        try:
            with self.server.run_in_thread():
                # test limits
                for limit in range(0, 3):
                    r = requests.get(f"{self.serverUrl()}/v1/list_entries/{limit}")
                    self.assertEqual(r.status_code, 200)
                    body: dict = dict(r.json())
                    self.assertIsNotNone(body)
                    count = 0
                    for source in body.keys():
                        count += len(body[source])

                    self.assertGreaterEqual(limit, count)

                # test keywords
                # test annotation keyword
                keyword = "Drosophila"
                r = requests.get(f"{self.serverUrl()}/v1/list_entries/1000/{keyword}")
                self.assertEqual(r.status_code, 200)
                body: dict = dict(r.json())
                self.assertIsNotNone(body)
                count = 0
                for source in body.keys():
                    count += len(body[source])

                # at least one, but could be more
                self.assertGreaterEqual(count, 1)

                # test annotation keyword wrong case
                keyword = "drosophila"
                r = requests.get(f"{self.serverUrl()}/v1/list_entries/1000/{keyword}")
                self.assertEqual(r.status_code, 200)
                body: dict = dict(r.json())
                self.assertIsNotNone(body)
                count = 0
                for source in body.keys():
                    count += len(body[source])

                self.assertGreaterEqual(count, 1)

                # test entry keyword
                keyword = "emd"
                r = requests.get(f"{self.serverUrl()}/v1/list_entries/1/{keyword}")
                self.assertEqual(r.status_code, 200)
                body: dict = dict(r.json())
                self.assertIsNotNone(body)
                count = 0
                for source in body.keys():
                    count += len(body[source])

                self.assertGreaterEqual(count, 1)

        finally:
            pass


if __name__ == "__main__":
    unittest.main()

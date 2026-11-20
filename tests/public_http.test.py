"""A temporary outage may recover; persistent failures must still fail health."""
import io, sys, unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
sys.path.insert(0, str(Path(__file__).parents[1] / 'tools'))
from public_http import fetch_public

URL = 'https://www.evberegn.dk/example/'
class Response:
    status = 200
    headers = {'Content-Type': 'text/html'}
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return b'actual content'
    def geturl(self): return URL

class PublicHTTPTests(unittest.TestCase):
    def exercise(self, statuses, method='GET', headers=None):
        calls, waits = [], []
        def opener(request, timeout):
            calls.append(request.get_method())
            status = statuses[min(len(calls)-1, len(statuses)-1)]
            if status == 0: raise URLError('temporary connection failure')
            if status != 200: raise HTTPError(URL, status, 'error', headers or {}, io.BytesIO(b'error page'))
            return Response()
        return fetch_public(URL, method, opener=opener, pause=waits.append), calls, waits
    def test_transient_image_503_recovers_on_the_same_head_address(self):
        result, calls, waits = self.exercise([503, 200], 'HEAD')
        self.assertEqual((result['status'], result['body'], result['previous_statuses']), (200, b'', [503]))
        self.assertEqual(calls, ['HEAD', 'HEAD']); self.assertEqual(waits, [1])
    def test_permanent_503_is_never_reported_as_success(self):
        result, calls, waits = self.exercise([503])
        self.assertEqual(result['status'], 503); self.assertEqual(len(calls), 3)
        self.assertEqual(waits, [1, 2])
    def test_real_404_is_not_retried_or_changed_into_success(self):
        result, calls, waits = self.exercise([404, 200])
        self.assertEqual(result['status'], 404); self.assertEqual(len(calls), 1); self.assertFalse(waits)
    def test_control_url_can_recover_from_503_to_its_correct_404(self):
        result, calls, _ = self.exercise([503, 404])
        self.assertEqual(result['status'], 404); self.assertEqual(len(calls), 2)
    def test_network_recovery_keeps_actual_body(self):
        result, _, _ = self.exercise([0, 200])
        self.assertEqual(result['body'], b'actual content')
    def test_long_rate_limit_is_respected_without_blind_retries(self):
        result, calls, waits = self.exercise([429, 200], headers={'Retry-After': '60'})
        self.assertEqual(result['status'], 429); self.assertEqual(len(calls), 1); self.assertFalse(waits)
    def test_mutations_are_never_allowed(self):
        with self.assertRaises(ValueError): fetch_public(URL, 'POST')

if __name__ == '__main__': unittest.main()

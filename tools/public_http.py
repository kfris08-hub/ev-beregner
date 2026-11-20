"""Read-only public HTTP checks with short, bounded transient-error retries."""
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

RETRYABLE = {408, 429, 500, 502, 503, 504}

def fetch_public(url, method='GET', *, opener=urlopen, pause=time.sleep, attempts=3):
    if method not in {'GET', 'HEAD'} or not 1 <= attempts <= 3:
        raise ValueError('Only bounded read-only checks are supported')
    started = time.monotonic()
    previous = []
    for attempt in range(1, attempts + 1):
        try:
            with opener(Request(url, headers={'User-Agent': 'Mozilla/5.0 EVBeregnerTechnicalAudit/1.0'}, method=method), timeout=15) as response:
                result = {'url': url, 'status': response.status, 'final': response.geturl(),
                          'headers': {k.lower(): v for k, v in response.headers.items()},
                          'body': response.read() if method == 'GET' else b''}
        except HTTPError as error:
            result = {'url': url, 'status': error.code, 'final': error.geturl(),
                      'headers': {k.lower(): v for k, v in error.headers.items()},
                      'body': error.read() if method == 'GET' else b''}
        except (URLError, TimeoutError, OSError) as error:
            result = {'url': url, 'status': 0, 'error': str(error), 'headers': {}, 'body': b''}
        result.update(attempts=attempt, previous_statuses=list(previous), seconds=round(time.monotonic() - started, 3))
        if result['status'] not in RETRYABLE | {0} or attempt == attempts:
            return result
        # A long Retry-After is a real temporary block, not permission to hammer.
        retry_after = result['headers'].get('retry-after', '')
        if retry_after and (not retry_after.isdigit() or int(retry_after) > 5):
            return result
        previous.append(result['status'])
        pause(max(attempt, int(retry_after or 0)))
    return result

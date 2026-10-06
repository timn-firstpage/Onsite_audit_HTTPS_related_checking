"""Offline hostname evidence checks; no customer website requests."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from http.client import IncompleteRead
from urllib.error import URLError
from email.message import Message
from check_hostname_pairs import Checker, NetworkInterrupted, TextEvidence, build_pairs, compare, main


class Reply(io.BytesIO):
    def __init__(self, code=200, location=None, body=None):
        super().__init__((body or '<main>' + 'Specific service content. ' * 8 + '</main>').encode())
        self.code, self.headers = code, Message()
        self.headers['Content-Type'] = 'text/html; charset=utf-8'
        if location:
            self.headers['Location'] = location
        if code == 429:
            self.headers['Retry-After'] = '60'


class FakeOpener:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def open(self, req, timeout):
        self.calls.append(req.full_url)
        return Reply(**self.routes[req.full_url])


class HostnameTests(unittest.TestCase):
    def test_transport_failures_raise_immediately_without_retry(self):
        for error in [TimeoutError("timed out"), URLError("DNS failed"),
                      ConnectionResetError("connection reset"), IncompleteRead(b"partial", 100)]:
            with self.subTest(error=type(error).__name__):
                opener = FakeOpener({})
                with patch.object(opener, 'open', side_effect=error) as request:
                    usage = {}
                    checker = Checker(['example.org'], usage, delay=0, opener=opener)
                    with self.assertRaisesRegex(NetworkInterrupted, 'rerun the entire skill'):
                        checker.check('https://example.org/')
                    self.assertEqual(request.call_count, 1)
                    self.assertEqual(usage['live_requests'], 1)

    def test_interruption_after_completed_pair_marks_failed_and_blocks_report(self):
        from build_report import build
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            run = Path(directory)
            config = run / 'config.json'
            pages = run / 'pages.json'
            config.write_text(json.dumps({'site': {'start_url': 'https://example.org/'}}), encoding='utf-8')
            pages.write_text(json.dumps([{'url': u, 'content_type': 'text/html'} for u in
                                         ['https://example.org/a', 'https://www.example.org/a']]), encoding='utf-8')
            opener = FakeOpener({})
            with patch.object(opener, 'open', side_effect=[Reply(), Reply(), IncompleteRead(b'x', 100)]) as request:
                with patch('check_hostname_pairs.build_opener', return_value=opener), patch('check_hostname_pairs.time.sleep'), patch('sys.argv',
                         ['check_hostname_pairs.py', '--config', str(config), '--pages', str(pages), '--run-dir', str(run)]):
                    with self.assertRaises(NetworkInterrupted):
                        main()
                    self.assertEqual(request.call_count, 3)
            status = json.loads((run / 'run-status.json').read_text(encoding='utf-8'))
            self.assertEqual(status['status'], 'failed')
            self.assertEqual(status['completed_pairs'], 1)
            self.assertTrue(status['rerun_required'])
            self.assertEqual(json.loads((run / 'usage.json').read_text())['live_requests'], 3)
            self.assertTrue((run / 'error.log').is_file())
            self.assertFalse((run / 'hostname-observations.json').exists())
            data = {'overview': [{'check': c, 'result': 'Pass', 'coverage': 'Completed'} for c in ['9.1', '9.2', '9.3']]}
            with self.assertRaisesRegex(RuntimeError, 'no final Excel'):
                build(data, run / 'audit.xlsx')
            self.assertFalse((run / 'audit.xlsx').exists())
            with patch('sys.argv', ['check_hostname_pairs.py', '--config', str(config), '--pages', str(pages), '--run-dir', str(run)]):
                with self.assertRaisesRegex(RuntimeError, 'new run directory'):
                    main()

    def test_only_homepage_generated_and_observed_pairs(self):
        rows = [{'url': u, 'content_type': 'text/html'} for u in [
            'https://example.org/service?q=1#x', 'https://www.example.org/service?q=1',
            'https://example.org/unpaired', 'https://other.org/service',
            'https://www.example.org/service?q=2']]
        pairs, omitted = build_pairs('https://example.org/deep', rows)
        self.assertEqual(len(pairs), 2)
        self.assertEqual(pairs[0]['urls'], ['https://example.org/', 'https://www.example.org/'])
        self.assertEqual(pairs[1]['urls'], ['https://example.org/service?q=1', 'https://www.example.org/service?q=1'])
        self.assertEqual(omitted, 0)
        self.assertEqual(build_pairs('https://www.another.co.uk/', [])[0][0]['urls'],
                         ['https://another.co.uk/', 'https://www.another.co.uk/'])

    def test_explicit_limit_does_not_remove_homepage_or_hide_omissions(self):
        rows = [{'url': f'https://{host}/{path}', 'content_type': 'text/html'}
                for path in ['a', 'b'] for host in ['example.org', 'www.example.org']]
        pairs, omitted = build_pairs('https://example.org', rows, 1)
        self.assertEqual((len(pairs), omitted), (2, 1))

    def test_redirect_cache_and_cumulative_budget(self):
        opener = FakeOpener({'https://www.example.org/': {'code': 301, 'location': 'https://example.org/'},
                             'https://example.org/': {}})
        usage = {'live_requests': 8, 'mcp_calls': 3}
        checker = Checker(['example.org', 'www.example.org'], usage, max_requests=10, delay=0, opener=opener)
        a = checker.check('https://www.example.org/')
        b = checker.check('https://example.org/')
        self.assertEqual([h['status'] for h in a['chain']], [301, 200])
        self.assertEqual(compare(a, b)['observation'], 'converged')
        self.assertEqual(usage, {'live_requests': 10, 'mcp_calls': 3})
        self.assertEqual(len(opener.calls), 2)
        self.assertEqual(checker.check('https://example.org/new')['error'], 'budget')

    def test_identical_independent_content_is_not_convergence(self):
        checker = Checker(['example.org', 'www.example.org'], {}, delay=0,
                          opener=FakeOpener({'https://example.org/': {}, 'https://www.example.org/': {}}))
        a, b = [checker.check(u) for u in ['https://example.org/', 'https://www.example.org/']]
        self.assertEqual(compare(a, b)['observation'], 'identical_without_convergence')
        b['content']['main_text'] = 'Another unrelated service. ' * 8
        self.assertEqual(compare(a, b)['observation'], 'different_content_without_convergence')
        b['content']['main_text'] = 'JS shell'
        self.assertEqual(compare(a, b)['observation'], 'human_check')

    def test_loop_scope_and_hop_limit(self):
        opener = FakeOpener({'https://example.org/': {'code': 302, 'location': '/'}})
        checker = Checker(['example.org'], {}, delay=0, opener=opener)
        self.assertEqual(checker.check('https://example.org/')['error'], 'loop')
        opener = FakeOpener({'https://example.org/': {'code': 302, 'location': 'https://outside.org/'}})
        checker = Checker(['example.org'], {}, delay=0, opener=opener)
        self.assertEqual(checker.check('https://example.org/')['error'], 'out_of_scope')
        self.assertEqual(len(opener.calls), 1)
        opener = FakeOpener({'https://example.org/': {'code': 302, 'location': '/b'}})
        checker = Checker(['example.org'], {}, max_hops=0, delay=0, opener=opener)
        self.assertEqual(checker.check('https://example.org/')['error'], 'hop_limit')

    def test_rate_limit_preserved_and_stops_further_network(self):
        opener = FakeOpener({'https://example.org/': {'code': 429}})
        checker = Checker(['example.org'], {}, delay=0, opener=opener)
        a = checker.check('https://example.org/')
        self.assertEqual(a['error'], 'rate_limited')
        self.assertEqual(a['chain'][0]['retry_after'], '60')
        self.assertEqual(checker.check('https://example.org/b')['error'], 'deferred_after_errors')
        self.assertEqual(len(opener.calls), 1)

    def test_main_content_excludes_shared_navigation(self):
        parser = TextEvidence()
        parser.feed('<head><title>A</title></head><nav>Common links</nav><main><h1>Service</h1>Specific content</main><footer>Common footer</footer>')
        content = parser.evidence()
        self.assertEqual(content['title'], 'A')
        self.assertEqual(content['main_text'], 'Service Specific content')


if __name__ == '__main__':
    unittest.main()

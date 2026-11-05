import unittest
from listening import canonical, parse_feed, render
class Tests(unittest.TestCase):
    def test_urls(self):
        self.assertIsNone(canonical('https://instagram.com/michelin'))
        self.assertIsNone(canonical('https://instagram.com.evil.test/p/123'))
        self.assertEqual(canonical('https://www.instagram.com/p/abc/?utm_source=x'), 'https://instagram.com/p/abc')
        self.assertNotEqual(canonical('https://facebook.com/watch/?v=123'),canonical('https://facebook.com/watch/?v=456'))
    def test_feed(self):
        rows=parse_feed(b'<rss><channel><item><title>Reifen</title><link>https://linkedin.com/posts/test</link></item><item><link>https://example.com/article</link></item></channel></rss>')
        self.assertEqual(len(rows),1)
        self.assertIsNone(rows[0]['metrics'])
    def test_escape(self):
        result=render({'date':'today','items':[{'title':'<script>','excerpt':'<img>','url':'https://instagram.com/p/abc'}],'total_found':1,'errors':[]})
        self.assertNotIn('<script>',result)

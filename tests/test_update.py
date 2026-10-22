import sys
import unittest
from pathlib import Path
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as E
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from update import collect, validate, timestamp


class GuideTests(unittest.TestCase):
    def test_exact_mapping_and_expiry(self):
        now = datetime(2026, 10, 22, 12, tzinfo=timezone.utc)
        mapping = E.fromstring('<channels><channel site_id="PlutoTV/us#abc" xmltv_id="News.us@East"/></channels>')
        guide = E.fromstring('''<tv>
          <programme channel="abc" start="20261022110000 +0000" stop="20261022130000 +0000"><title>News</title></programme>
          <programme channel="abc" start="20261022090000 +0000" stop="20261022100000 +0000"><title>Expired</title></programme>
          <programme channel="abc" start="20261022130000 +0000" stop="20261022120000 +0000"><title>Invalid</title></programme>
        </tv>''')
        found = collect(mapping, guide, 'PlutoTV/us', {'News.us@East', 'News.us@West'}, now, now + timedelta(days=7))
        self.assertEqual(set(found), {'News.us@East'})
        self.assertEqual(len(found['News.us@East']), 1)
        self.assertEqual(found['News.us@East'][0].get('channel'), 'News.us@East')
        self.assertEqual(guide[0].get('channel'), 'abc')

    def test_refuse_empty_or_collapsed_coverage(self):
        with self.assertRaises(ValueError): validate({}, set())
        data = {str(i): [] for i in range(60)}
        with self.assertRaises(ValueError): validate(data, set(data), old_count=100)
        validate(data, set(data), old_count=70)

    def test_timezone(self):
        self.assertEqual(timestamp('20261022080000 -0400'), timestamp('20261022120000 +0000'))

    def test_plex_prefix_rotation_requires_id_and_name(self):
        now = datetime(2026, 10, 22, 12, tzinfo=timezone.utc)
        old = 'a' * 24 + '-' + 'c' * 24
        new = 'b' * 24 + '-' + 'c' * 24
        mapping = E.fromstring(f'<channels><channel site_id="Plex/us#{old}" xmltv_id="News.us@SD">News</channel></channels>')
        guide = E.fromstring(f'<tv><channel id="{new}"><display-name>News</display-name></channel><programme channel="{new}" start="20261022110000 +0000" stop="20261022130000 +0000"><title>News</title></programme></tv>')
        self.assertIn('News.us@SD', collect(mapping, guide, 'Plex/us', {'News.us@SD'}, now, now + timedelta(days=1)))
        guide.find('channel/display-name').text = 'Different channel'
        self.assertEqual({}, collect(mapping, guide, 'Plex/us', {'News.us@SD'}, now, now + timedelta(days=1)))

"""Build a matched US XMLTV guide. Python 3.11+, standard library only."""
import argparse
import copy
import gzip
import html
import json
import os
from pathlib import Path
import re
import time
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PLAYLIST = 'https://iptv-org.github.io/iptv/countries/us.m3u'
MAPPINGS = 'https://raw.githubusercontent.com/iptv-org/epg/master/sites/i.mjh.nz/'
FEEDS = 'https://raw.githubusercontent.com/matthuisman/i.mjh.nz/master/'
SOURCES = [('pluto', 'PlutoTV/us'), ('plex', 'Plex/us'), ('roku', 'Roku/all'),
           ('samsung', 'SamsungTVPlus/us'), ('pbs', 'PBS/all'), ('metv', 'MeTV/epg')]


def fetch(url):
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'personal-us-epg/1.0'}), timeout=60) as r:
                data = r.read(100 * 1024 * 1024 + 1)
            if len(data) > 100 * 1024 * 1024:
                raise ValueError('Response exceeds 100 MiB')
            return data
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def timestamp(value):
    return datetime.strptime(value, '%Y%m%d%H%M%S %z').astimezone(timezone.utc)


def playlist_ids(text):
    return set(re.findall(r'tvg-id="([^"]+)"', text))


def collect(mapping, guide, path, wanted, now, end):
    """Match exact IDs, including feed suffixes. Never guess from names."""
    ids = {}
    for channel in mapping.findall('channel'):
        feed, _, native = channel.get('site_id', '').partition('#')
        target = channel.get('xmltv_id', '')
        if feed == path and target in wanted and native:
            ids.setdefault(native, set()).add(target)
    result = {}
    for program in guide.findall('programme'):
        try:
            start, stop = timestamp(program.get('start', '')), timestamp(program.get('stop', ''))
        except ValueError:
            continue
        if stop <= now or start >= end or stop <= start or not program.findtext('title', '').strip():
            continue
        for target in ids.get(program.get('channel'), ()):
            p = copy.deepcopy(program)
            p.set('channel', target)
            result.setdefault(target, []).append(p)
    return result


def validate(programs, wanted, old_count=0):
    if not programs or len(programs) < 50:
        raise ValueError('Fewer than 50 matched channels with current/future programs; refusing publication')
    if not set(programs).issubset(wanted):
        raise ValueError('Unexpected channel IDs')
    if old_count and len(programs) < old_count * 0.7:
        raise ValueError('Coverage dropped more than 30%; retaining previously published guide')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--days', type=int, default=7, choices=range(1, 31), metavar='1..30')
    args = ap.parse_args()
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=args.days)
    playlist = fetch(PLAYLIST).decode('utf-8-sig')
    wanted = playlist_ids(playlist)
    if len(wanted) < 100:
        raise ValueError('Playlist is empty or unexpectedly small')
    programs, provenance, sources = {}, {}, []
    for name, path in SOURCES:
        try:
            mapping = ET.fromstring(fetch(MAPPINGS + f'i.mjh.nz_{name}.channels.xml'))
            guide = ET.fromstring(fetch(FEEDS + path + '.xml'))
            found = collect(mapping, guide, path, wanted, now, end)
            for cid, entries in found.items():
                if cid not in programs:  # Choose one source per channel; never mix schedules.
                    programs[cid], provenance[cid] = entries, path
            sources.append({'source': path, 'matched_channels': len(found)})
            print(f'{path}: {len(found)} matched channels', flush=True)
        except Exception as exc:
            sources.append({'source': path, 'error': str(exc)})
            print(f'WARNING {path}: {exc}', flush=True)
    output = ROOT / 'docs'
    old_count = 0
    if (output / 'status.json').exists():
        old_count = json.loads((output / 'status.json').read_text())['matched_channels']
    validate(programs, wanted, old_count)
    tv = ET.Element('tv', {'generator-info-name': 'personal-us-epg'})
    detail = {}
    total = 0
    for cid in sorted(programs):
        c = ET.SubElement(tv, 'channel', {'id': cid})
        ET.SubElement(c, 'display-name').text = cid
    for cid in sorted(programs):
        seen = set()
        entries = sorted(programs[cid], key=lambda p: timestamp(p.get('start')))
        for p in entries:
            key = (p.get('start'), p.get('stop'), p.findtext('title'))
            if key not in seen:
                seen.add(key)
                tv.append(p)
                total += 1
        detail[cid] = {'source': provenance[cid], 'programs': len(seen),
                       'through_utc': max(timestamp(p.get('stop')) for p in entries).isoformat()}
    xml = ET.tostring(tv, encoding='utf-8', xml_declaration=True)
    ET.fromstring(xml)  # Verify the actual serialized output before any replacement.
    report = {'generated_utc': now.isoformat(), 'requested_days': args.days,
              'playlist_unique_ids': len(wanted), 'matched_channels': len(programs),
              'coverage_percent': round(100 * len(programs) / len(wanted), 1),
              'programs': total, 'sources': sources, 'channels': detail,
              'unmatched_ids': sorted(wanted - set(programs))}
    output.mkdir(exist_ok=True)
    files = {'guide.xml': xml, 'guide.xml.gz': gzip.compress(xml, mtime=0),
             'status.json': json.dumps(report, indent=2).encode(), '.nojekyll': b''}
    # Also offer a playlist containing only channels with real guide entries.
    lines = playlist.splitlines()
    matched = ['#EXTM3U']
    keep = False
    for line in lines[1:]:
        if line.startswith('#EXTINF:'):
            keep = bool(playlist_ids(line) & set(programs))
        if keep:
            matched.append(line)
    files['matched-us.m3u'] = ('\n'.join(matched) + '\n').encode()
    summary = f'{len(programs)} of {len(wanted)} channel IDs ({report["coverage_percent"]}%), {total:,} programs'
    files['index.html'] = (f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        f'<title>My US EPG</title><body><h1>My US EPG</h1><p>{html.escape(summary)}</p>'
        f'<p>Updated {now.isoformat()}</p><p><a href="guide.xml">XMLTV guide</a> · '
        '<a href="guide.xml.gz">Compressed guide</a> · <a href="matched-us.m3u">Matched playlist</a> · '
        '<a href="status.json">Coverage report</a></p><p>Coverage is partial. Schedule depth varies by channel. '
        'Sources: iptv-org channel mappings and matthuisman/i.mjh.nz schedules.</p></body></html>').encode()
    for name, data in files.items():
        temp = output / (name + '.tmp')
        temp.write_bytes(data)
        os.replace(temp, output / name)
    print(summary, flush=True)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
            f.write('## EPG refresh\n' + summary + '\n\nSee docs/status.json for per-channel dates and missing IDs.\n')


if __name__ == '__main__':
    main()

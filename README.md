# My U.S. EPG

Personal XMLTV guide matched to the [iptv-org U.S. playlist](https://iptv-org.github.io/iptv/countries/us.m3u).

## Firestick setup

After the first successful workflow run, use this **EPG URL**:

https://raw.githubusercontent.com/ariel-figue/my-epg/main/docs/guide.xml

Keep the original U.S. playlist for all channels, including channels without guide data. Alternatively, the following playlist only includes channels with current/future guide entries at refresh time:

https://raw.githubusercontent.com/ariel-figue/my-epg/main/docs/matched-us.m3u

The XMLTV IDs preserve exact playlist IDs, including regional/feed suffixes. Configure your app to refresh its EPG at least daily. Computer uptime is not required.

## Refresh

GitHub Actions runs at 07:23 and 19:23 UTC. To refresh manually: **Actions → Refresh US EPG → Run workflow**. No secrets or paid services are needed. GitHub scheduling can be delayed; check Actions if the guide becomes stale. GitHub may disable scheduled workflows in inactive public repositories after 60 days; re-enable the workflow if necessary.

To run locally with Python 3.11 or later (no dependencies):

```sh
python scripts/update.py --days 7
```

To publish a local run from a cloned repository, commit the updated `docs` directory and push it to `main` using your own GitHub authentication. Generating files locally alone does not upload them.

## Coverage and validation

`docs/status.json` records the refresh time, exact covered/missing IDs, source errors, program counts, and each channel's last available schedule time. Coverage means at least one unexpired program, not a complete 24-hour or seven-day schedule. One source is chosen per channel to avoid combining conflicting schedules. Unmatched or blank IDs are not guessed from display names.

The updater downloads existing XMLTV schedules from [matthuisman/i.mjh.nz](https://github.com/matthuisman/i.mjh.nz) and applies [iptv-org/epg](https://github.com/iptv-org/epg) mappings for Pluto TV US, Plex US, Roku, Samsung TV Plus US, PBS and MeTV. This avoids downloading thousands of unrelated schedules one channel at a time. It does not use the previously suggested DIRECTV configuration, whose mappings were blank during setup.

`--days 30` sets an upper bound; it cannot produce 30 days when sources only publish a few days. Source availability and channel mappings can change. These upstream projects remain dependencies even though the final guide is hosted in your own repository. Stream playback and schedule accuracy are not guaranteed by a successful ID match.

A failed/empty run, fewer than 50 covered channels, or a coverage drop greater than 30% stops publication and keeps the previous files. Check Actions errors; retained schedules eventually expire. Guide timestamps preserve source time zones. No generated filler programs are used.

## Optional GitHub Pages website

The raw EPG URL works without Pages. For a website and the shorter `https://ariel-figue.github.io/my-epg/guide.xml` URL:

1. Settings → Pages → Source: **GitHub Actions**.
2. Settings → Secrets and variables → Actions → Variables: create repository variable `ENABLE_PAGES` with value `true`.
3. Run **Refresh US EPG** again. The optional Pages job publishes the same validated files.

Only enable this variable after configuring Pages. The raw URL continues working if Pages deployment fails. Hosting is subject to GitHub terms and limits; it is not guaranteed permanent.

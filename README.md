# My U.S. EPG

Personal XMLTV guide matched to the [iptv-org U.S. playlist](https://iptv-org.github.io/iptv/countries/us.m3u).

## Firestick setup

After enabling Pages and a successful deployment, use this **EPG URL**:

https://ariel-figue.github.io/my-epg/guide.xml

The website at https://ariel-figue.github.io/my-epg/ shows the last refresh time, coverage and download links. A compressed guide is also available at `guide.xml.gz`.

Keep the original U.S. playlist for all channels, including channels without guide data. Alternatively, the following playlist only includes channels with current/future guide entries at refresh time:

https://ariel-figue.github.io/my-epg/matched-us.m3u

If Pages is not yet enabled or a deployment fails, the existing fallback EPG URL remains:

https://raw.githubusercontent.com/ariel-figue/my-epg/main/docs/guide.xml

The XMLTV IDs preserve exact playlist IDs, including regional/feed suffixes. Configure your app to refresh its EPG at least daily. Computer uptime is not required.

Plex lineup-prefix rotations are accepted only when the stable channel identifier is unique and the display name also agrees; no name-only matching is used.

## Refresh

GitHub Actions is scheduled at 07:23 and 19:23 UTC daily. Each successful refresh commits the validated files, uploads an artifact, and deploys it to GitHub Pages. To refresh manually: **Actions → Refresh US EPG → Run workflow**. No secrets or paid services are needed. GitHub scheduling can be delayed; check Actions if the guide becomes stale. GitHub may disable scheduled workflows in inactive public repositories after 60 days; re-enable the workflow if necessary.

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

## One-time GitHub Pages activation

An administrator must enable Pages in the repository settings once:

1. Settings → Pages → Source: **GitHub Actions**.
2. Run **Refresh US EPG** again (or re-run the failed Pages job from the latest run).

No `ENABLE_PAGES` variable is needed. The deployment job now runs automatically after every successful refresh. If Pages has not been enabled, the configuration check fails with a setup error; guide generation and publication to the raw fallback URL still succeed. Hosting is subject to GitHub terms and limits; it is not guaranteed permanent.

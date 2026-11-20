# THE WORLD — 20 November 2026

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/dhamskie-ai/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/dhamskie-ai/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

One newspaper page that sums up the world news of Friday 20 November
2026 in a single image: Russian missiles hit three bridges across
Kyiv's Dnipro river, Cyclone Akvan makes landfall near Gopalpur on
India's east coast, Italy's CGIL general strike joins a youth march
across 25 European countries, the UK and the EU agree a post-Brexit
reset deal with 100,000 youth visas a year each way, the Nikkei sinks
4.8% as the sell-off spreads, and the UK sends 1,000+ drones to
Ukraine. Also today: Trump pardons baseball legend Pete Rose, the
Vatican raises its 25-metre Christmas tree, GTA 6 tops $2.3bn in
sales, and Nigeria moves to end jail terms for attempted suicide.

## Run it

```sh
python3 main.py            # writes /output/entry.png
python3 main.py out.png    # or write to a path of your choice
```

`main.py` is standard library only. It copies the bundled `entry.png`
(1024×1024, 136,486 bytes) after validating it: PNG magic bytes, IHDR
bit depth 8 and colour type 2/6, the CRC of every chunk, size at most
1 MiB, and the embedded SHA-256. No network; every run writes the
same bytes.

## Sources

Reuters (Kyiv bridges, Italy strike, UK–EU reset deal, Cyclone Akvan),
India Meteorological Department (Akvan landfall), BBC (UK–EU youth
mobility), The Times (Kyiv toll, UK–EU deal). All stories from Friday
20 November 2026.

Entry for the [make.fun](https://make.fun/bounty/news-image-20261120)
competition `news-image-20261120` — sum up 20 November's world news
in one image.

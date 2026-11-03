# Landing page performance and cache policy

Verified locally on 3 November 2026. These changes require a Hosting release to
affect production. The production HTML previously returned `max-age=3600`.

The public Hosting target now sends `no-cache, max-age=0, must-revalidate` for
page URLs and unversioned files. Browsers can reuse a response only after checking
it with the server. Content-hashed Next.js JavaScript, CSS and bundled fonts use
`public, max-age=31536000, immutable`; changed files get new URLs at build time.
The admin target keeps its existing `no-store` policy.

This cannot recall an old response that a browser already considers fresh, or
replace an already-open tab. During the first rollout, existing visitors may
need one hard refresh or to wait out the old one-hour lifetime. Sign-in storage
is preserved. No service worker is registered by this project.

Fonts retain Latin, punctuation, currencies and arrows. Exposure keeps the
`EXPO` range from -10 to 0 used by the UI. Other writing systems use system
fallbacks. Original font files remain in `public/poke`; the optimized files are
bundled from `src/app/fonts` so their URLs change with their contents. QR code
generation now loads separately after hydration. The scrolled header uses a
solid background instead of applying a blur to the content moving behind it.

One cold run per viewport, using installed Chrome, a 4× CPU slowdown, 1.6 Mbps
download and 150 ms network latency against the Firebase Hosting emulator:

| Measurement | Before | After |
| --- | ---: | ---: |
| Landing fonts | 1,200,500 bytes | 283,732 bytes |
| Initial JavaScript (Next build) | 114 KB | 105 KB |
| Captured resource transfer, desktop | 2,256,865 bytes | 1,340,105 bytes |
| Final font response, desktop | 11.18 s | 4.07 s |
| Largest contentful paint, desktop | 1.21 s | 1.22 s |
| Largest contentful paint, mobile | 1.24 s | 1.24 s |

These are lab observations, not field guarantees. The measured benefit is fewer
downloads and earlier final typography; this run did not improve LCP. Both
viewports had no horizontal overflow or JavaScript errors. The 410 KB paper
texture remains a further asset optimization opportunity.

Validation: `npm run build:sites` in `frontend`, then
`python3 -m unittest discover -s frontend/tests`. The output font budget fails
above 300 KB. The optional session browser checks also passed all three cases
with `ASTRA_ENTRY_URL` pointed at the Hosting emulator and
`PLAYWRIGHT_CHROME_PATH` pointed at installed Chrome. Actual emulator responses
were checked for `/`, `/index.html`, `/app`, `/app.html`, `/brands`, the texture,
a generated JavaScript chunk and a bundled font.

To regenerate the committed font subsets from the originals, run from `frontend`:
`uv run --with 'fonttools[woff]==4.68.0' python scripts/subset-fonts.py`.
FontTools is an optional authoring tool, not an application dependency.

References: [Firebase cache behavior](https://firebase.google.com/docs/hosting/manage-cache)
and [HTTP Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control).

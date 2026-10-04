#!/usr/bin/env python3
"""Mirror the official sandpack classic-sandbox build into ./www.

Downloads the same static files that https://2-19-8-sandpack.codesandbox.io
serves, so the whole in-browser bundler can be self-hosted (e.g. on GitHub
Pages at runtime.reactchallenges.com).

The version-pinned bundler URL (2-19-8-sandpack.codesandbox.io) is the classic
CodeSandbox sandbox: index.html + sandbox.js/chunks + web-worker transpilers +
vendored compiler libs + BrowserFS + branding assets. Only the webpack chunk
manifest is listed in file-manifest.json; the vendored libs and branding are
fetched from the known paths below.
"""
import json
import os
import re
import sys
import urllib.request

BASE = os.environ.get("BASE", "https://2-19-8-sandpack.codesandbox.io")
OUT = os.environ.get("OUT", "www")

VENDORED_STATIC = [
    "static/js/babel.6.26.min.js",
    "static/js/babel.7.21.8.js",
    "static/js/babel.7.21.8.min.js",
    "static/js/browserified-pug.0.1.0.min.js",
    "static/js/coffeescript.2.3.2.js",
    "static/js/eslint.4.1.0.min.js",
    "static/js/jsdom-16.3.0.min.js",
    "static/js/less-4.1.2.min.js",
    "static/js/less.min.js",
    "static/js/stylus.min.js",
    "static/js/prettier/1.15.1/standalone.js",
    "static/js/prettier/1.15.1/parser-angular.js",
    "static/js/prettier/1.15.1/parser-babylon.js",
    "static/js/prettier/1.15.1/parser-flow.js",
    "static/js/prettier/1.15.1/parser-glimmer.js",
    "static/js/prettier/1.15.1/parser-graphql.js",
    "static/js/prettier/1.15.1/parser-html.js",
    "static/js/prettier/1.15.1/parser-markdown.js",
    "static/js/prettier/1.15.1/parser-postcss.js",
    "static/js/prettier/1.15.1/parser-typescript.js",
    "static/js/prettier/1.15.1/parser-yaml.js",
    "static/js/prettier/1.16.4/standalone.js",
    "static/js/prettier/1.16.4/parser-angular.js",
    "static/js/prettier/1.16.4/parser-babylon.js",
    "static/js/prettier/1.16.4/parser-flow.js",
    "static/js/prettier/1.16.4/parser-glimmer.js",
    "static/js/prettier/1.16.4/parser-graphql.js",
    "static/js/prettier/1.16.4/parser-html.js",
    "static/js/prettier/1.16.4/parser-markdown.js",
    "static/js/prettier/1.16.4/parser-postcss.js",
    "static/js/prettier/1.16.4/parser-typescript.js",
    "static/js/prettier/1.16.4/parser-yaml.js",
    "static/js/prettier/2.0.5/standalone.js",
    "static/js/prettier/2.0.5/parser-angular.js",
    "static/js/prettier/2.0.5/parser-babel.js",
    "static/js/prettier/2.0.5/parser-flow.js",
    "static/js/prettier/2.0.5/parser-glimmer.js",
    "static/js/prettier/2.0.5/parser-graphql.js",
    "static/js/prettier/2.0.5/parser-html.js",
    "static/js/prettier/2.0.5/parser-markdown.js",
    "static/js/prettier/2.0.5/parser-postcss.js",
    "static/js/prettier/2.0.5/parser-typescript.js",
    "static/js/prettier/2.0.5/parser-yaml.js",
    "static/js/prettier/worker-1.15.1.js",
    "static/js/prettier/worker-1.16.4.js",
    "static/js/prettier/worker-2.0.5.js",
    "static/js/prettier/worker.js",
]

BRANDING = [
    "manifest.json",
    "csb-ios.svg",
    "favicon-16x16.png",
    "favicon-32x32.png",
    "favicon.ico",
    "apple-touch-icon-152x152.png",
    "apple-touch-icon-180x180.png",
    "apple-touch-icon.png",
    "site.webmanifest",
    "robots.txt",
    "safari-pinned-tab.svg",
    "codesandbox-512.png",
    "codesandbox-1024.png",
    "codesandbox-256.png",
    "codesandbox-128.png",
    "codesandbox-16.png",
    "codesandbox-32.png",
    "browserconfig.xml",
]

EXTRA = [
    "static/browserfs12/browserfs.min.js",
]


def fetch(url, timeout=90):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def download(path):
    dest = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    data = fetch(BASE + "/" + path)
    with open(dest, "wb") as f:
        f.write(data)
    print(f"  ok {path} ({len(data)} bytes)")


def main():
    manifest = json.loads(fetch(BASE + "/file-manifest.json"))
    paths = {v.lstrip("/") for k, v in manifest.items() if not k.endswith(".map")}
    paths |= set(EXTRA)
    paths |= set(BRANDING)
    paths |= set(VENDORED_STATIC)

    total = len(paths)
    ok = fail = 0
    for i, path in enumerate(sorted(paths), 1):
        try:
            download(path)
            ok += 1
        except Exception as e:
            fail += 1
            print(f"  FAIL {path}: {e}")
        if i % 20 == 0:
            print(f"  ... {i}/{total}")
    print(f"\nDONE: {ok} ok, {fail} fail")

    # index.html: strip Cloudflare challenge/beacon injection from the CDN
    idx = os.path.join(OUT, "index.html")
    html = open(idx).read()
    html = re.sub(r"<script>[^<]*?cdn-cgi[^<]*?</script>", "", html, flags=re.S)
    html = re.sub(
        r'<script[^>]*src="https://static\.cloudflareinsights\.com/[^"]*"[^>]*></script>',
        "",
        html,
    )
    # index.html: set on-prem env so the sandbox skips telemetry to col.csbops.io
    html = re.sub(
        r'<script>window\.process=BrowserFS\.BFSRequire\("process"\),window\.Buffer=BrowserFS\.BFSRequire\("buffer"\)\.Buffer</script>',
        r'<script>window.process=BrowserFS.BFSRequire("process"),window.Buffer=BrowserFS.BFSRequire("buffer").Buffer</script><script>window._env_={IS_ONPREM:"true"}</script>',
        html,
    )
    open(idx, "w").write(html)
    print("index.html cleaned; scripts:", re.findall(r'src="([^"]+)"', html))

    # record provenance
    version = "2-19-8-sandpack.codesandbox.io (official classic-sandbox build)"
    with open(os.path.join(OUT, "version.txt"), "w") as f:
        f.write(version + "\n")


if __name__ == "__main__":
    main()
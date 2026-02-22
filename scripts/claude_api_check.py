#!/usr/bin/env python3
import argparse
import json
import os
import sys
import textwrap
import requests

CF_TRACE = "https://cloudflare.com/cdn-cgi/trace"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
ANTHROPIC_VERSION = "2023-06-01"


def print_section(title: str):
    print("\n" + "=" * 8 + f" {title} " + "=" * 8)


def explain_status(code: int, text: str):
    msg = None
    if code == 200:
        msg = "OK: response received."
    elif code == 401:
        msg = "401 Unauthorized: API key is invalid or expired."
    elif code == 403:
        msg = (
            "403 Forbidden: Cloudflare or Anthropic rejected the request. "
            "Often this is a geo/ASN block or API access restriction."
        )
    elif code == 404:
        msg = "404 Not Found: incorrect endpoint path."
    elif code == 429:
        msg = "429 Too Many Requests: rate limit exceeded."
    elif 500 <= code <= 599:
        msg = "5xx Server Error: service-side failure."

    try:
        j = json.loads(text)
        if isinstance(j, dict) and "error" in j:
            detail = j["error"].get("message") or j["error"].get("type")
            if detail:
                msg = (msg or "") + f"\nDetails: {detail}"
    except Exception:
        pass
    return msg


def main():
    p = argparse.ArgumentParser(
        description="Anthropic API diagnostics",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument(
        "--api-key",
        help="Anthropic API key (sk-ant-...); can also be set via ANTHROPIC_API_KEY",
    )
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--message", default="ping")
    p.add_argument("--timeout", type=int, default=15)
    p.add_argument(
        "--no-verify", action="store_true", help="Disable TLS certificate verification"
    )
    p.add_argument(
        "--proxy", help="HTTP(S)/SOCKS5 proxy (example: socks5h://127.0.0.1:1080)"
    )
    args = p.parse_args()

    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("API key not found. Pass --api-key or set ANTHROPIC_API_KEY.")
        sys.exit(2)

    sess = requests.Session()
    if args.proxy:
        sess.proxies.update({"http": args.proxy, "https": args.proxy})

    verify = not args.no_verify

    # === Cloudflare trace ===
    print_section("Cloudflare trace")
    try:
        r = sess.get(CF_TRACE, timeout=8, verify=verify)
        print(r.text.strip())
    except Exception as e:
        print(f"Cloudflare request failed: {e}")

    # === Anthropic request ===
    print_section("POST /v1/messages")
    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }
    payload = {
        "model": args.model,
        "max_tokens": 16,
        "messages": [{"role": "user", "content": args.message}],
    }

    print("Sending request...")
    try:
        resp = sess.post(
            ANTHROPIC_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=args.timeout,
            verify=verify,
        )
        print(f"HTTP {resp.status_code}")
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
        msg = explain_status(resp.status_code, resp.text)
        if msg:
            print_section("Interpretation")
            print(textwrap.fill(msg, 100))
    except requests.exceptions.SSLError as e:
        print(f"SSL error: {e}")
        print("Try running with --no-verify.")
    except Exception as e:
        print(f"Network error: {e}")


if __name__ == "__main__":
    main()

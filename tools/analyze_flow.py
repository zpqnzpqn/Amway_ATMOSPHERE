#!/usr/bin/env python3
"""Analyze mitmproxy capture flow and format exact HTTP request sequence.

Usage:
    python3 tools/analyze_flow.py [.scratch/amway_android_login.flow]
"""

import json
import os
import sys
from mitmproxy import io
from mitmproxy.exceptions import FlowReadException


def analyze_flow(flow_path: str) -> None:
    if not os.path.exists(flow_path):
        print(f"File not found: {flow_path}")
        return

    print("=" * 70)
    print(f"📊 Analyzing Network Flow: {flow_path}")
    print("=" * 70)

    requests_sequence = []

    with open(flow_path, "rb") as f:
        reader = io.FlowReader(f)
        try:
            for flow in reader.stream():
                if not hasattr(flow, "request"):
                    continue
                req = flow.request
                resp = flow.response

                # Filter relevant auth domains
                host = req.pretty_host
                if not any(
                    k in host
                    for k in [
                        "amway",
                        "gluu",
                        "okta",
                        "conex",
                        "aws",
                    ]
                ):
                    continue

                item = {
                    "method": req.method,
                    "url": req.pretty_url,
                    "status_code": resp.status_code if resp else None,
                    "request_headers": dict(req.headers),
                    "request_body": req.get_text() if req.content else "",
                    "response_headers": dict(resp.headers) if resp else {},
                    "response_body": resp.get_text() if resp and resp.content else "",
                }
                requests_sequence.append(item)

                print(f"\n[{req.method}] {req.pretty_url}")
                if resp:
                    print(f"Status: {resp.status_code}")
                    loc = resp.headers.get("Location", "")
                    if loc:
                        print(f"Location: {loc}")
                    if "set-cookie" in resp.headers:
                        print(f"Set-Cookie: {resp.headers.get('set-cookie')[:80]}...")
                    if "application/json" in resp.headers.get("content-type", ""):
                        try:
                            data = json.loads(resp.get_text())
                            keys = list(data.keys())
                            print(f"JSON Response Keys: {keys}")
                            if "access_token" in data:
                                print(">>> [FOUND ACCESS TOKEN] <<<")
                            if "refresh_token" in data:
                                print(">>> [FOUND REFRESH TOKEN] <<<")
                        except Exception:
                            pass
        except FlowReadException as e:
            print(f"Flow read error: {e}")

    out_json = os.path.splitext(flow_path)[0] + "_summary.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(requests_sequence, f, indent=2)

    print("\n" + "=" * 70)
    print(f"✅ Total relevant requests analyzed: {len(requests_sequence)}")
    print(f"Saved complete sequence summary to: {out_json}")
    print("=" * 70)


if __name__ == "__main__":
    path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.path.join(
            os.path.dirname(__file__), "..", ".scratch", "amway_android_login.flow"
        )
    )
    analyze_flow(path)

#!/usr/bin/env python3
"""Demo script for Bid Exchange — end-to-end simulation.

Usage:
    python demo.py
    python demo.py --rounds 5 --scenario "luxury brands targeting affluent women"
"""

import argparse
import json
import sys
import time

import httpx

BASE_URL = "http://localhost:8000/api"


def main():
    parser = argparse.ArgumentParser(description="Bid Exchange Demo")
    parser.add_argument("--rounds", type=int, default=10, help="Number of auction rounds")
    parser.add_argument(
        "--scenario",
        type=str,
        default="Compare reach vs quality bidding strategies for sports brands targeting young males",
        help="Simulation scenario prompt",
    )
    parser.add_argument("--consumers", type=int, default=20)
    parser.add_argument("--websites", type=int, default=10)
    parser.add_argument("--campaigns", type=int, default=4)
    args = parser.parse_args()

    client = httpx.Client(base_url=BASE_URL, timeout=300.0)

    # Check health
    print("Checking API health...")
    resp = client.get("/health")
    if resp.status_code != 200:
        print(f"API not healthy: {resp.status_code}")
        sys.exit(1)
    print("API is healthy!\n")

    # Create simulation
    print(f"Creating simulation: {args.scenario[:80]}...")
    start = time.time()
    resp = client.post("/simulations", json={
        "scenario": args.scenario,
        "num_consumers": args.consumers,
        "num_websites": args.websites,
        "num_campaigns": args.campaigns,
    })
    if resp.status_code != 201:
        print(f"Failed to create simulation: {resp.text}")
        sys.exit(1)

    sim = resp.json()
    sim_id = sim["id"]
    elapsed = time.time() - start
    print(f"  Simulation {sim_id} created in {elapsed:.1f}s")
    print(f"  Consumers: {sim['consumer_count']}, Websites: {sim['website_count']}, Campaigns: {sim['campaign_count']}\n")

    # List campaigns
    print("Campaigns:")
    resp = client.get(f"/simulations/{sim_id}/campaigns")
    campaigns = resp.json()
    for c in campaigns:
        print(f"  - {c['campaign_name']} (goal: {c['goal']}, budget: ${c['total_budget']:.0f})")
    print()

    # Run auction rounds
    print(f"Running {args.rounds} auction rounds...")
    start = time.time()
    resp = client.post(f"/simulations/{sim_id}/run", json={"rounds": args.rounds})
    if resp.status_code != 200:
        print(f"Failed to run auctions: {resp.text}")
        sys.exit(1)

    auctions = resp.json()
    elapsed = time.time() - start
    print(f"  Completed {len(auctions)} auctions in {elapsed:.1f}s\n")

    # Show recent auctions
    print("Recent auctions:")
    resp = client.get(f"/simulations/{sim_id}/auctions")
    for a in resp.json()[:5]:
        feedback = a.get("consumer_feedback", "N/A")
        bid = f"${a['winning_bid']:.2f}" if a["winning_bid"] else "no bids"
        print(f"  - Auction {a['id'][:8]}... | Winner bid: {bid} | Feedback: {feedback}")
    print()

    # Dashboard
    print("Dashboard:")
    resp = client.get(f"/simulations/{sim_id}/dashboard")
    dash = resp.json()
    print(f"  Total auctions: {dash['total_auctions']}")
    print(f"  Total bids: {dash['total_bids']}")
    print(f"  Avg winning bid: ${dash['avg_winning_bid']:.2f}")
    print(f"  Like/Dislike: {dash['likes']}/{dash['dislikes']} ({dash['like_ratio']:.1f}%)")
    print(f"  Total budget spent: ${dash['total_budget_spent']:.2f}")
    print()

    # Campaign details + insights
    print("Campaign Results:")
    resp = client.get(f"/simulations/{sim_id}/campaigns")
    for c in resp.json():
        cid = c["id"]
        detail_resp = client.get(f"/simulations/{sim_id}/campaigns/{cid}")
        detail = detail_resp.json()
        stats = detail.get("stats", {})
        print(f"\n  {detail['campaign_name']} ({detail['goal']})")
        print(f"    Budget: ${detail['remaining_budget']:.0f} / ${detail['total_budget']:.0f}")
        print(f"    Bids: {stats.get('total_bids', 0)} | Wins: {stats.get('wins', 0)} ({stats.get('win_rate', 0):.1f}%)")
        print(f"    Likes: {stats.get('likes', 0)} | Dislikes: {stats.get('dislikes', 0)}")

        print(f"    Fetching AI insights...")
        insights_resp = client.get(f"/simulations/{sim_id}/campaigns/{cid}/insights")
        if insights_resp.status_code == 200:
            insights = insights_resp.json()
            print(f"    Summary: {insights['summary']}")
            for s in insights.get("suggestions", []):
                print(f"      -> {s}")

    print("\nDemo complete!")


if __name__ == "__main__":
    main()

import argparse, asyncio, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

async def main():
    p=argparse.ArgumentParser()
    p.add_argument("--query",required=True)
    p.add_argument("--limit",type=int,default=20)
    args=p.parse_args()
    if not 1 <= args.limit <= 100: p.error("limit must be 1..100")
    user=os.environ.get("X_USERNAME","")
    password=os.environ.get("X_PASSWORD","")
    email=os.environ.get("X_EMAIL","")
    email_password=os.environ.get("X_EMAIL_PASSWORD","")
    if not (user and password and email and email_password):
        print("ERROR: Missing X_USERNAME, X_PASSWORD, X_EMAIL or X_EMAIL_PASSWORD GitHub Actions secrets.",file=sys.stderr)
        return 2
    from twscrape import API, gather
    api=API()
    await api.pool.add_account(user,password,email,email_password)
    await api.pool.login_all()
    results=[]
    async for tweet in api.search(args.query,limit=args.limit):
        results.append({"id":str(tweet.id),"date":tweet.date.isoformat() if tweet.date else None,"author":tweet.user.username if tweet.user else None,"text":tweet.rawContent,"url":f"https://x.com/i/status/{tweet.id}"})
    Path("results").mkdir(exist_ok=True)
    data={"query":args.query,"retrieved_at_utc":datetime.now(timezone.utc).isoformat(),"count":len(results),"posts":results}
    Path("results/search.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# Percept X Search Results","",f"Query: `{args.query}`",f"Posts: {len(results)}",""]
    for t in results:
        lines.extend([f"## @{t['author'] or 'unknown'} — {t['date'] or 'unknown date'}",t["text"].replace("\n"," "),t["url"],""])
    Path("results/search.md").write_text("\n".join(lines),encoding="utf-8")
    print(f"Saved {len(results)} posts to results/search.json and results/search.md")
    return 0

if __name__=="__main__":
    try: sys.exit(asyncio.run(main()))
    except Exception as e:
        print(f"Search failed: {type(e).__name__}: {str(e)[:300]}",file=sys.stderr)
        sys.exit(1)

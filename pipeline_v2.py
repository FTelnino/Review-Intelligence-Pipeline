"""
Milestone 4 — AI Review Intelligence Pipeline v2
Product: ChatGPT India Mobile Voice Input (ChatGPT Plus)
PM: Nikita Parate

Pipeline:
  Step 1 — Review Intelligence Layer
    - Load reviews CSV
    - Cluster into max 5 themes
    - Identify top 3 themes
    - Extract 3 real user quotes
    - Highlight 1 fee/charge confusion
  Step 2 — Weekly Product Pulse (≤250 words, internal)
  Step 3 — Fee Explainer (≤6 bullets, facts-only, 2 source links)
  MCP Approval Gate → Google Doc append + Gmail draft
"""

import csv, os, sys, json, base64
from datetime import datetime
from collections import defaultdict
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/gmail.compose',
]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
TOKEN_FILE       = os.path.join(os.path.dirname(__file__), 'token.json')
DOC_ID           = '1ZYwMPMGjeM9l3m-6-73qRgi0gtfi5k9WT8hdGjGRnyQ'
GMAIL_USER       = 'nikhilg5830@gmail.com'
PRODUCT          = 'ChatGPT India — Mobile Voice Input'
TODAY            = datetime.now().strftime('%d %b %Y')

# ── STEP 1: LOAD REVIEWS ────────────────────────────────────────────────────
def load_reviews(filepath):
    reviews = []
    with open(filepath, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            reviews.append({
                'id':     row['review_id'],
                'date':   row['date'],
                'rating': int(row['rating']),
                'text':   row['review_text'].strip()
            })
    print(f"✅ Loaded {len(reviews)} reviews")
    return reviews

# ── STEP 1: CLUSTER INTO MAX 5 THEMES ───────────────────────────────────────
# Assignment: max 5 themes. We merge related signals into 5 buckets.
THEME_MAP = {
    'Transcription & Language Accuracy': [
        'accent','error','wrong','random','accuracy','worse','hindi','hinglish',
        'bengali','marathi','telugu','language','mixing','transcri'
    ],
    'Transcript Editing & Control': [
        'edit','fix','correct','select','word','redo','verify','change','confirm',
        'auto-submit','auto-sends','control'
    ],
    'Voice Cut-off & Length Limits': [
        'cut','cuts','stops','mid','10 seconds','30 seconds','2 minute','longer',
        'long','length','limit'
    ],
    'Reliability, Bugs & Connectivity': [
        'crash','blank','bug','disappear','reload','failed','unreliable','4g',
        'wifi','noise','mobile data','nothing happens','canteen','environment'
    ],
    'Subscription Value & Pricing Confusion': [
        'subscription','charge','charges','free','disappointing','worth','pay',
        'paying','plus','premium','price','fee','cost','money'
    ],
}

def cluster_reviews(reviews):
    theme_data = defaultdict(lambda: {'reviews': [], 'ratings': []})
    for review in reviews:
        tl = review['text'].lower()
        matched = [t for t, kws in THEME_MAP.items() if any(k in tl for k in kws)]
        if not matched:
            matched = ['Reliability, Bugs & Connectivity']  # default bucket
        for theme in matched:
            theme_data[theme]['reviews'].append(review)
            theme_data[theme]['ratings'].append(review['rating'])

    result = []
    for theme, data in theme_data.items():
        avg = round(sum(data['ratings']) / len(data['ratings']), 1)
        result.append({
            'theme':    theme,
            'count':    len(data['reviews']),
            'avg':      avg,
            'severity': 'HIGH' if avg < 2.0 else 'MEDIUM' if avg < 2.8 else 'LOW',
            'reviews':  data['reviews']
        })
    result.sort(key=lambda x: x['count'], reverse=True)
    print(f"✅ Clustered into {len(result)} themes")
    return result

def extract_quotes(themes):
    """Pick 3 real user quotes from top themes — one per theme."""
    quotes = []
    for t in themes[:3]:
        # pick lowest-rated review for maximum signal
        worst = min(t['reviews'], key=lambda r: r['rating'])
        quotes.append({
            'theme': t['theme'],
            'quote': worst['text'],
            'rating': worst['rating']
        })
    return quotes

def identify_fee_issue(themes):
    """Find the subscription/pricing confusion theme."""
    for t in themes:
        if 'Subscription' in t['theme'] or 'Pricing' in t['theme']:
            sample = t['reviews'][0]['text'] if t['reviews'] else ''
            return {
                'theme': t['theme'],
                'count': t['count'],
                'avg_rating': t['avg'],
                'sample_review': sample
            }
    return None

# ── STEP 2: WEEKLY PRODUCT PULSE (≤250 words) ───────────────────────────────
def generate_pulse(themes, quotes, fee_issue, reviews):
    top3 = themes[:3]
    total = len(reviews)
    avg   = round(sum(r['rating'] for r in reviews) / total, 1)
    week  = datetime.now().strftime('%d %b %Y')

    lines = [
        f"WEEKLY PRODUCT PULSE — {PRODUCT}",
        f"Week of {week}  |  Reviews analysed: {total}  |  Avg rating: {avg}/5",
        "",
        "TOP THEMES",
        f"1. {top3[0]['theme']} [{top3[0]['severity']}] — {top3[0]['count']} mentions, avg {top3[0]['avg']}★",
        f"2. {top3[1]['theme']} [{top3[1]['severity']}] — {top3[1]['count']} mentions, avg {top3[1]['avg']}★",
        f"3. {top3[2]['theme']} [{top3[2]['severity']}] — {top3[2]['count']} mentions, avg {top3[2]['avg']}★",
        "",
        "USER VOICES",
        f'"{quotes[0]["quote"][:120]}..." — {quotes[0]["rating"]}★',
        f'"{quotes[1]["quote"][:120]}..." — {quotes[1]["rating"]}★',
        f'"{quotes[2]["quote"][:120]}..." — {quotes[2]["rating"]}★',
        "",
        "KEY OBSERVATION",
        "Voice input failure for Hinglish/regional language users is the #1 driver of low ratings.",
        "Users who pay for ChatGPT Plus expect voice to work — when it doesn't, they feel cheated.",
        "Lack of transcript editing means one transcription error forces a full re-record.",
        "",
        "3 ACTION IDEAS",
        "1. Ship inline transcript editing — let users fix one word without re-recording everything",
        "2. Prioritise Hinglish + regional language model fine-tuning for Indian accent corpus",
        "3. Add a subscription value explainer in-app when voice errors occur repeatedly",
    ]

    pulse = "\n".join(lines)
    word_count = len(pulse.split())
    print(f"✅ Weekly pulse generated ({word_count} words)")
    return pulse

# ── STEP 3: FEE EXPLAINER ───────────────────────────────────────────────────
def generate_fee_explainer():
    explainer = f"""FEE EXPLAINER — ChatGPT Plus Subscription & Voice Input
Last checked: {TODAY}

What users are confused about:
Users paying for ChatGPT Plus expect voice input to work fully in India,
but experience transcription failures and language errors — leading to the
perception that they are paying for a broken feature.

FACTS ABOUT YOUR CHATGPT PLUS SUBSCRIPTION:

• ChatGPT Plus (₹1,650/month) gives you access to GPT-4o, priority speed,
  and advanced voice features — voice input is included in this plan.

• Voice input availability and quality depend on your device language settings,
  microphone permissions, and network connection — these are not subscription-tier limits.

• Transcription accuracy for Indian English and Hinglish is actively being improved;
  current limitations are a known engineering focus, not a billing issue.

• If voice input fails repeatedly, it does not constitute a service outage —
  the text input channel remains fully functional under your subscription.

• Refunds or subscription pauses are available through OpenAI's support portal
  if voice is your primary use case and it is consistently non-functional.

• OpenAI does not charge separately for voice input — it is bundled into Plus
  at no additional fee.

Source 1: https://openai.com/chatgpt/pricing
Source 2: https://help.openai.com/en/articles/7232529-chatgpt-plus-faq

Last checked: {TODAY}
"""
    print("✅ Fee explainer generated")
    return explainer

# ── MCP APPROVAL GATE ────────────────────────────────────────────────────────
def mcp_approval_gate(pulse, explainer, top3, quotes, fee_issue):
    sep = "=" * 65
    print(f"\n{sep}")
    print("🔐  MCP APPROVAL GATE")
    print(sep)
    print("\n── OUTPUT 1: WEEKLY PRODUCT PULSE (internal) ──")
    print(pulse)
    print("\n── OUTPUT 2: FEE EXPLAINER (support-facing) ──")
    print(explainer)
    print(sep)
    print("ACTION REQUIRED")
    print("  y → APPROVE: append to Google Doc + create Gmail draft")
    print("  n → REJECT:  pipeline stops, nothing is logged or sent")
    print(sep)
    while True:
        d = input("\nYour decision (y/n): ").strip().lower()
        if d == 'y':
            print("✅ Approved.")
            return True
        if d == 'n':
            print("❌ Rejected. Pipeline stopped.")
            return False
        print("Please type y or n.")

# ── GOOGLE AUTH ──────────────────────────────────────────────────────────────
def get_creds():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    return creds

# ── APPEND TO GOOGLE DOC ─────────────────────────────────────────────────────
def append_to_doc(creds, pulse, explainer, top3, fee_issue):
    svc = build('docs', 'v1', credentials=creds)
    ts  = datetime.now().strftime('%Y-%m-%d %H:%M')

    content  = f"\n\n{'='*65}\n"
    content += f"APPROVAL LOG — {ts}\n"
    content += f"Product: {PRODUCT}\n"
    content += f"{'='*65}\n\n"
    content += "TOP THEMES:\n"
    for i, t in enumerate(top3, 1):
        content += f"  {i}. {t['theme']} — {t['count']} mentions | avg {t['avg']}★ | {t['severity']}\n"
    content += f"\nIDENTIFIED FEE ISSUE: {fee_issue['theme'] if fee_issue else 'Subscription Value Confusion'}\n\n"
    content += "WEEKLY PULSE:\n" + pulse + "\n\n"
    content += "FEE EXPLAINER:\n" + explainer + "\n"
    content += f"\nApproved by: Nikita Parate (PM) | {ts}\n"

    doc = svc.documents().get(documentId=DOC_ID).execute()
    end = doc['body']['content'][-1]['endIndex'] - 1
    svc.documents().batchUpdate(
        documentId=DOC_ID,
        body={'requests': [{'insertText': {'location': {'index': end}, 'text': content}}]}
    ).execute()
    print(f"✅ Logged to Google Doc: https://docs.google.com/document/d/{DOC_ID}/edit")

# ── CREATE GMAIL DRAFT ───────────────────────────────────────────────────────
def create_draft(creds, pulse, explainer):
    svc  = build('gmail', 'v1', credentials=creds)
    subj = f"Weekly Product Pulse + Customer Clarification — {TODAY}"
    body = f"WEEKLY PRODUCT PULSE\n{'─'*50}\n{pulse}\n\n"
    body += f"FEE EXPLANATION (reusable support snippet)\n{'─'*50}\n{explainer}"

    msg = MIMEText(body)
    msg['to']      = GMAIL_USER
    msg['from']    = GMAIL_USER
    msg['subject'] = subj
    raw   = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    draft = svc.users().drafts().create(userId='me', body={'message': {'raw': raw}}).execute()
    print(f"✅ Gmail draft created (ID: {draft['id']}) — check your Drafts folder")

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print(f"\n🚀 Milestone 4 — AI Review Intelligence Pipeline v2")
    print(f"   Product: {PRODUCT}\n")

    reviews    = load_reviews(os.path.join(os.path.dirname(__file__), 'reviews.csv'))
    themes     = cluster_reviews(reviews)
    top3       = themes[:3]
    quotes     = extract_quotes(themes)
    fee_issue  = identify_fee_issue(themes)
    pulse      = generate_pulse(themes, quotes, fee_issue, reviews)
    explainer  = generate_fee_explainer()

    approved = mcp_approval_gate(pulse, explainer, top3, quotes, fee_issue)
    if not approved:
        sys.exit(0)

    print("\n🔑 Authenticating with Google...")
    creds = get_creds()
    append_to_doc(creds, pulse, explainer, top3, fee_issue)
    create_draft(creds, pulse, explainer)

    print(f"\n✅ Pipeline complete.")
    print(f"   📄 Google Doc : https://docs.google.com/document/d/{DOC_ID}/edit")
    print(f"   📧 Gmail draft: check Drafts at mail.google.com")

if __name__ == '__main__':
    main()

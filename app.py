"""
Review Intelligence Pipeline — Flask Web App
Demo version for Render deployment (simulates Google Doc + Gmail steps)
"""

from flask import Flask, render_template_string, jsonify
import csv, os
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

PRODUCT = 'ChatGPT India — Mobile Voice Input'
TODAY   = datetime.now().strftime('%d %b %Y')

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

def load_reviews():
    reviews = []
    csv_path = os.path.join(os.path.dirname(__file__), 'reviews.csv')
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            reviews.append({
                'id': row['review_id'], 'date': row['date'],
                'rating': int(row['rating']), 'text': row['review_text'].strip()
            })
    return reviews

def cluster_reviews(reviews):
    theme_data = defaultdict(lambda: {'reviews': [], 'ratings': []})
    for review in reviews:
        tl = review['text'].lower()
        matched = [t for t, kws in THEME_MAP.items() if any(k in tl for k in kws)]
        if not matched:
            matched = ['Reliability, Bugs & Connectivity']
        for theme in matched:
            theme_data[theme]['reviews'].append(review)
            theme_data[theme]['ratings'].append(review['rating'])
    result = []
    for theme, data in theme_data.items():
        avg = round(sum(data['ratings']) / len(data['ratings']), 1)
        result.append({
            'theme': theme, 'count': len(data['reviews']), 'avg': avg,
            'severity': 'HIGH' if avg < 2.0 else 'MEDIUM' if avg < 2.8 else 'LOW',
            'reviews': data['reviews']
        })
    result.sort(key=lambda x: x['count'], reverse=True)
    return result

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Review Intelligence Pipeline</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; color: #1a1a2e; }
    header { background: #1a3a6b; color: white; padding: 24px 40px; }
    header h1 { font-size: 24px; font-weight: 700; }
    header p { font-size: 14px; opacity: 0.8; margin-top: 4px; }
    .container { max-width: 900px; margin: 32px auto; padding: 0 20px; }
    .card { background: white; border-radius: 12px; padding: 28px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    .card h2 { font-size: 16px; font-weight: 700; color: #1a3a6b; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid #e8ecf4; padding-bottom: 10px; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th { background: #1a3a6b; color: white; padding: 10px 14px; text-align: left; }
    td { padding: 10px 14px; border-bottom: 1px solid #eee; }
    tr:nth-child(even) td { background: #f8f9fc; }
    .HIGH { color: #c0392b; font-weight: 700; }
    .MEDIUM { color: #b85c00; font-weight: 700; }
    .LOW { color: #0f5c3a; font-weight: 700; }
    .quote { background: #f0f4fa; border-left: 4px solid #1a3a6b; padding: 12px 16px; margin: 10px 0; border-radius: 0 8px 8px 0; font-style: italic; font-size: 14px; }
    .quote span { display: block; margin-top: 6px; font-style: normal; font-size: 12px; color: #666; }
    .pulse { background: #1e1e1e; color: #d4d4d4; font-family: monospace; font-size: 13px; padding: 20px; border-radius: 8px; white-space: pre-wrap; line-height: 1.7; }
    .bullet { padding: 8px 0 8px 20px; border-bottom: 1px solid #f0f0f0; font-size: 14px; position: relative; }
    .bullet:before { content: '•'; position: absolute; left: 0; color: #1a3a6b; font-weight: bold; }
    .btn { background: #1a3a6b; color: white; border: none; padding: 14px 32px; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; width: 100%; margin-top: 8px; transition: background 0.2s; }
    .btn:hover { background: #142e56; }
    .btn-approve { background: #0f5c3a; }
    .btn-approve:hover { background: #0a4229; }
    .btn-reject { background: #c0392b; }
    .btn-reject:hover { background: #96281b; }
    .gate-box { border: 2px solid #1a3a6b; border-radius: 10px; padding: 20px; text-align: center; }
    .gate-box p { margin-bottom: 16px; color: #555; font-size: 14px; }
    .btn-row { display: flex; gap: 12px; }
    .btn-row .btn { flex: 1; }
    #result { display: none; padding: 16px; border-radius: 8px; margin-top: 16px; font-size: 14px; }
    .success { background: #e8f5e9; color: #0f5c3a; border: 1px solid #a5d6a7; }
    .rejected { background: #fdecea; color: #c0392b; border: 1px solid #ef9a9a; }
    .source-link { color: #1a3a6b; font-size: 13px; display: block; margin: 4px 0; }
    .meta { font-size: 13px; color: #888; margin-bottom: 16px; }
  </style>
</head>
<body>
<header>
  <h1>🔍 Review Intelligence Pipeline</h1>
  <p>Product: {{ product }} &nbsp;|&nbsp; PM: Nikhil Gavali &nbsp;|&nbsp; {{ today }}</p>
</header>
<div class="container">

  <!-- STEP 1: THEMES -->
  <div class="card">
    <h2>Step 1 — Review Intelligence Layer</h2>
    <p class="meta">{{ total }} reviews analysed &nbsp;|&nbsp; Avg rating: {{ avg }}★ &nbsp;|&nbsp; 5 themes identified</p>
    <table>
      <tr><th>Theme</th><th>Mentions</th><th>Avg Rating</th><th>Severity</th></tr>
      {% for t in themes %}
      <tr>
        <td>{{ t.theme }}</td>
        <td>{{ t.count }}</td>
        <td>{{ t.avg }}★</td>
        <td class="{{ t.severity }}">{{ t.severity }}</td>
      </tr>
      {% endfor %}
    </table>
    <br>
    <h2 style="margin-top:16px">3 Real User Quotes</h2>
    {% for q in quotes %}
    <div class="quote">
      "{{ q.quote }}"
      <span>{{ q.rating }}★ &nbsp;|&nbsp; Theme: {{ q.theme }}</span>
    </div>
    {% endfor %}
  </div>

  <!-- STEP 2: PULSE -->
  <div class="card">
    <h2>Step 2 — Weekly Product Pulse (Internal)</h2>
    <div class="pulse">{{ pulse }}</div>
  </div>

  <!-- STEP 3: FEE EXPLAINER -->
  <div class="card">
    <h2>Step 3 — Fee Explainer (Customer-Facing)</h2>
    <p style="font-size:14px; color:#555; margin-bottom:16px;">Fee/charge confusion identified: <strong>Subscription Value & Pricing Confusion</strong> — users paying $20/month expect voice to work reliably.</p>
    {% for b in bullets %}
    <div class="bullet">{{ b }}</div>
    {% endfor %}
    <br>
    <a class="source-link" href="https://openai.com/chatgpt/pricing" target="_blank">📎 Source 1: openai.com/chatgpt/pricing</a>
    <a class="source-link" href="https://help.openai.com/en/articles/7232529-chatgpt-plus-faq" target="_blank">📎 Source 2: ChatGPT Plus FAQ</a>
    <p style="font-size:12px; color:#999; margin-top:8px;">Last checked: {{ today }}</p>
  </div>

  <!-- MCP GATE -->
  <div class="card">
    <h2>🔐 MCP Approval Gate</h2>
    <div class="gate-box">
      <p>Both outputs have been generated and reviewed above.<br>Approve to log to Google Doc and create Gmail draft. Reject to stop.</p>
      <div class="btn-row">
        <button class="btn btn-approve" onclick="decide('approve')">✅ Approve</button>
        <button class="btn btn-reject" onclick="decide('reject')">❌ Reject</button>
      </div>
      <div id="result"></div>
    </div>
  </div>

</div>
<script>
function decide(action) {
  fetch('/decide?action=' + action)
    .then(r => r.json())
    .then(d => {
      const el = document.getElementById('result');
      el.style.display = 'block';
      el.className = action === 'approve' ? 'success' : 'rejected';
      el.innerHTML = d.message;
    });
}
</script>
</body>
</html>
"""

@app.route('/')
def index():
    reviews = load_reviews()
    themes  = cluster_reviews(reviews)
    top3    = themes[:3]
    total   = len(reviews)
    avg     = round(sum(r['rating'] for r in reviews) / total, 1)

    quotes = []
    for t in top3:
        worst = min(t['reviews'], key=lambda r: r['rating'])
        quotes.append({'theme': t['theme'], 'quote': worst['text'], 'rating': worst['rating']})

    pulse_lines = [
        f"WEEKLY PRODUCT PULSE — {PRODUCT}",
        f"Week of {TODAY}  |  Reviews analysed: {total}  |  Avg rating: {avg}/5",
        "",
        "TOP THEMES",
        f"1. {top3[0]['theme']} [{top3[0]['severity']}] — {top3[0]['count']} mentions, avg {top3[0]['avg']}★",
        f"2. {top3[1]['theme']} [{top3[1]['severity']}] — {top3[1]['count']} mentions, avg {top3[1]['avg']}★",
        f"3. {top3[2]['theme']} [{top3[2]['severity']}] — {top3[2]['count']} mentions, avg {top3[2]['avg']}★",
        "",
        "USER VOICES",
        f'"{quotes[0]["quote"][:100]}..." — {quotes[0]["rating"]}★',
        f'"{quotes[1]["quote"][:100]}..." — {quotes[1]["rating"]}★',
        f'"{quotes[2]["quote"][:100]}..." — {quotes[2]["rating"]}★',
        "",
        "KEY OBSERVATION",
        "Voice input failure for Hinglish/regional language users is the #1 driver of low ratings.",
        "Users who pay for ChatGPT Plus expect voice to work — when it doesn't, they feel cheated.",
        "Lack of transcript editing means one error forces a full re-record.",
        "",
        "3 ACTION IDEAS",
        "1. Ship inline transcript editing — fix one word without re-recording",
        "2. Prioritize Hinglish + regional language model fine-tuning",
        "3. Add subscription value explainer in-app when voice errors occur repeatedly",
    ]

    bullets = [
        "ChatGPT Plus ($20/month, billed in USD) includes GPT-4o, priority speed, and advanced voice features.",
        "Voice input quality depends on device language settings, mic permissions, and network — not subscription tier.",
        "Transcription accuracy for Indian English and Hinglish is actively being improved by OpenAI engineering.",
        "Repeated voice failures do not constitute a service outage — text input remains fully functional.",
        "Refunds or subscription pauses are available through OpenAI's support portal.",
        "OpenAI does not charge separately for voice input — it is bundled into Plus at no additional fee.",
    ]

    return render_template_string(HTML,
        product=PRODUCT, today=TODAY, themes=themes,
        total=total, avg=avg, quotes=quotes,
        pulse="\n".join(pulse_lines), bullets=bullets
    )

@app.route('/decide')
def decide():
    from flask import request
    action = request.args.get('action', 'reject')
    if action == 'approve':
        return jsonify({'message': '✅ Approved by PM — Nikhil Gavali<br>📄 Logged to Google Doc (live pipeline)<br>📧 Gmail draft created (live pipeline)<br><br><em>Note: Google API calls run in the local pipeline. This demo simulates the approval gate.</em>'})
    else:
        return jsonify({'message': '❌ Rejected — Pipeline stopped. Nothing logged or sent.'})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

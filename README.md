# Milestone — AI Review Intelligence Pipeline
**Product:** ChatGPT India — Mobile Voice Input  
**PM:** Nikhil Gavali  
**Date:** 05 Nov 2026

---

## What This Builds

An AI workflow that transforms raw customer reviews into two structured outputs — a weekly internal product pulse and a customer-facing fee explainer — with a human approval gate before anything is logged or sent.

---

## How to Run

### Prerequisites
- Python 3.9+
- Google Cloud project with Google Docs API and Gmail API enabled
- OAuth 2.0 Desktop credentials downloaded as `credentials.json`

### Install dependencies
```bash
pip3 install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Setup
Put these 3 files in the same folder:
- `pipeline_v2.py`
- `reviews.csv`
- `credentials.json` (from Google Cloud Console)

### Run
```bash
python3 pipeline_v2.py
```

---

## What Happens Step by Step

**Step 1 — Review Intelligence Layer**
- Loads 22 customer reviews from `reviews.csv`
- Clusters them into 5 themes (max 5 as per spec)
- Identifies top 3 themes by mention volume
- Extracts 3 real user quotes (lowest-rated per theme)
- Flags 1 fee/subscription confusion issue

**Step 2 — Weekly Product Pulse**
- Generates a ≤250-word structured internal note
- Includes top themes, user quotes, key observation, 3 action ideas

**Step 3 — Fee Explainer**
- Generates a ≤6-bullet facts-only explanation of the subscription confusion
- Includes 2 official OpenAI source links
- Includes "Last checked" date

**MCP Approval Gate**
- Displays both outputs in the terminal
- Prompts: `y` to approve, `n` to reject
- Nothing is logged or sent until human types `y`

**After Approval**
- Appends structured log to Google Doc (includes themes, quotes, pulse, fee explainer, timestamp, PM name)
- Creates Gmail draft (subject: Weekly Product Pulse + Customer Clarification — [date])
- No auto-send

---

## Where the MCP Approval Happens

In the terminal, after both outputs are generated and displayed, the pipeline prints:

```
============================================================
🔐  MCP APPROVAL GATE
ACTION REQUIRED
  y → APPROVE: append to Google Doc + create Gmail draft
  n → REJECT:  pipeline stops, nothing is logged or sent
============================================================
Your decision (y/n):
```

The pipeline is fully blocked at this point. No Google API calls are made until the human types `y`.

---

## Fee Issue Identified from Reviews

**Theme:** Subscription Value & Pricing Confusion  
**What users are confused about:** Users paying for ChatGPT Plus ($20/month, billed in USD) expect voice input to work reliably in India. When transcription fails repeatedly — especially for Hinglish and regional language speakers — they feel they are paying for a broken feature. This surfaces as "not worth it" and "worse than free alternatives" in reviews.  
**Fee explainer generated:** 6-bullet facts-only explanation of what ChatGPT Plus includes, why voice issues are not a billing problem, and where to get support.

---

## Files in This Submission

| File | Description |
|------|-------------|
| `pipeline_v2.py` | Main pipeline script |
| `reviews.csv` | 20 sample customer reviews (last 8 weeks) |
| `README.md` | This file |
| `submission_doc.md` | Full outputs: pulse + fee explainer + source list |

---

## Source List

1. https://openai.com/chatgpt/pricing — ChatGPT Plus pricing and feature list
2. https://help.openai.com/en/articles/7232529-chatgpt-plus-faq — Official ChatGPT Plus FAQ
3. https://help.openai.com/en/articles/8400625-voice-mode-faq — Voice Mode FAQ
4. https://openai.com/index/chatgpt-plugins — ChatGPT feature overview
5. https://support.openai.com — OpenAI support portal for subscription issues
6. https://platform.openai.com/docs/guides/speech-to-text — Speech-to-text technical documentation

# Case Study Generator

**Function:** Marketing  ·  **Integrations:** crm, communication  ·  **Template id:** `AGTCaseStudy01`

> Automatically generates polished case studies from successful customer engagements using CRM data, conversation insights, and team commentary.

## When it fires

**Detector:** Trigger if the user wants to automatically generate case studies, success stories, or marketing content from customer conversations and CRM data.

**Signal keywords:** `case study`, `success story`, `customer story`, `generate case study`, `marketing content`, `customer win`, `write case study`, `customer success`

## What it does

🎯 Purpose

Automatically generate polished, client-ready case studies summarizing successful customer engagements, using data from your CRM, team conversations, and analytics systems. The goal is to streamline marketing and enablement content creation by turning internal data into structured narratives.

💡 Behavior

Trigger Type: Primarily activates after a conversation analyzed event where a deal or project success is detected, or when a CRM opportunity is marked as Closed Won.

Tone: Professional, evidence-based, narrative-driven.

Output Style: Markdown or formatted text blocks ready for publication in Notion, HubSpot, or internal documentation.

Frequency: On-demand (manual trigger) or automatic weekly summaries.

⚙️ Procedure

Event Detection

Listens for events tagged as deal success, project completion, or customer satisfaction highlight.

Confirms relevant metadata from your CRM (account name, deal size, industry, key contacts, dates).

Data Aggregation

Pulls conversation insights from your call recorder's analytics.

Extracts quotes and performance metrics (e.g., time saved, revenue impact).

Gathers team commentary from relevant communication channels (e.g., #customer-success).

Story Synthesis

Structures the case study into clear sections:

Client Overview

Challenge

Solution

Results

Customer Quote

Team Insights

Uses narrative templates fine-tuned to the company's tone.

Quality Validation

Runs a short internal approval workflow:

Marketing review for tone and clarity.

Sales review for data accuracy.

Publishing / Output

Outputs formatted text to a designated Notion database or internal CMS.

Posts summary announcement in a designated marketing channel (e.g., #marketing-content).

## Tools / actions
- **CRM** — Query Records
- **Communication** — Send Direct Message

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** Conversation analyzed — fires once per call, when your call recorder finishes analyzing it (the *Conversation Analyzed* webhook).

---
_From GTM Superintelligence agent templates. Raw definition: [`case-study-generator.json`](./case-study-generator.json)._

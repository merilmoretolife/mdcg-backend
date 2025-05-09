from flask import Flask, request, jsonify
from flask_cors import CORS
import re
from datetime import datetime
import uuid
import openai
import os
from openai import OpenAI

# Read the full MDCG guidance from the text file
with open("mdcg_2020_3.txt", "r", encoding="utf-8") as f:
    mdcg_text = f.read()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def assess_change_with_ai(change_description):
    prompt = f"""
You are a regulatory affairs expert evaluating changes to medical devices under the EU MDR.

Your job is to analyze the change below using the official MDCG 2020-3 Rev.1 guidance, and provide:

1. The change type (e.g., design, software, labeling)
2. Whether the change is significant (Yes/No)
3. Justification with reference to the guidance
4. Recommended regulatory actions

=== MDCG Guidance (Excerpt) ===
{mdcg_text[:12000]}
=== End Guidance ===

Change Description:
\"\"\"{change_description}\"\"\"

Respond in clear bullet point format.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content
    
@app.route('/assess', methods=['POST'])
def assess():
    data = request.get_json()
    text_input = data.get('change_description', '')

    # AI-based assessment using full MDCG guidance
    report = assess_change_with_ai(text_input)

    return jsonify({
        'report': report,
        'report_filename': f'change_assessment_{uuid.uuid4()}.txt'
    })

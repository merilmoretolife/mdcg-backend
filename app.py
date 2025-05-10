from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import uuid

openai.api_key = os.getenv("OPENAI_API_KEY")

with open("mdcg_2020_3.txt", "r", encoding="utf-8") as f:
    mdcg_text = f.read()[:12000]

app = Flask(__name__)
CORS(app)

def assess_change_with_ai(change_description):
    prompt = f"""
You are an EU medical device regulatory expert.

Your task is to assess whether the following change to a medical device is significant or not, using only the content provided from MDCG 2020-3 Rev.1 guidance (see below).

🔹 You MUST:
- Classify the change type (e.g., software, design, labeling, etc.)
- State whether the change is significant: Yes / No
- Cite the specific section and chart (e.g., "Section 4.3.2.3", "Chart C") that supports your assessment
- Quote the relevant line(s) from the MDCG guidance text if possible
- Use the chart mapping below to cite the chart based on the change type

🔸 Chart Mapping:
- Changes in the intended purpose → Chart A
- Changes in design → Chart B
- Software changes → Chart C
- Material or substance changes → Chart D
- Sterilization or packaging changes → Chart E

🔸 Use only the guidance text below for your assessment. Do not rely on prior model knowledge.

=== MDCG 2020-3 Rev.1 Guidance Text (truncated) ===
{mdcg_text}
=== End Guidance ===

🔸 Change Description:
\"\"\"{change_description}\"\"\"

Return the output in this exact structure:

1. **Change Type**
2. **Is the Change Significant?** (Yes/No)
3. **Cited Clause and Chart both**
4. **Supporting Text or Quote**
5. **Justification**
   Provide a detailed paragraph (100–200 words) explaining why the change is or isn’t significant.
   Your justification must:
   - Explain how the change affects intended purpose, design, safety, software, etc.
   - Clearly connect that impact to the definition of "significant change" from MDCG 2020-3 Rev.1
   - Cite specific sections (e.g., “Section 4.3.2.3”) and the correct Chart (A–E)

6. **Regulatory Action Required**
   - If MDR certified: what the manufacturer must do
   - If MDD certified (legacy): what the manufacturer must do under Article 120(3)

7. **Notification to Notified Body**
   Clearly state whether this change should be notified to the Notified Body or not, and why.
   - If significant → explain that it must be notified and why
   - If non-significant → explain why notification is not required
"""
    
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0]["message"]["content"]

@app.route('/assess', methods=['POST'])
def assess():
    data = request.get_json()
    text_input = data.get('change_description', '')
    report = assess_change_with_ai(text_input)
    return jsonify({
        'report': report,
        'report_filename': f'change_assessment_{uuid.uuid4()}.txt'
    })

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=True)

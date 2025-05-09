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
- Cite the specific section or chart (e.g., "Section 4.3.2.3", "Chart C") that supports your assessment
- Quote the relevant line(s) from the MDCG guidance text if possible
- Do NOT recommend MDR certification unless the guidance requires it as a consequence of a significant change
- Provide **two separate recommendations**:
   1. If the device is **MDR certified**
   2. If the device is still under **MDD certificate** (legacy device under Article 120(3) MDR)

🔹 Only use the text below for your response. Do not rely on prior model knowledge.

=== MDCG 2020-3 Rev.1 Guidance Text (truncated) ===
{mdcg_text}
=== End Guidance ===

🔸 Change Description:
\"\"\"{change_description}\"\"\"

Return the output in this structure:
1. **Change Type**
2. **Is the Change Significant?** (Yes/No)
3. **Cited Clause and Chart both**
4. **Supporting Text or Quote**
5. **Justification**  
   Provide a detailed paragraph (100–200 words) explaining why the change is or isn’t significant.  
   Your justification must:
   - Explain how the change affects intended purpose, design, safety, software, etc.
   - Clearly connect that impact to the definition of "significant change" from MDCG 2020-3 Rev.1
   - Cite specific MDCG sections (e.g., “Section 4.3.2.3”) or Charts (e.g., “Chart C”) when possible

6. **Regulatory Action Required**
   You MUST:
   - Clearly specify what the manufacturer should do if the device is **MDR certified**
   - Clearly specify what to do if the device is **MDD certified (legacy)** under Article 120(3)
   - Write a statement on whether the change should be notified to notifying body or not and why:
     
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

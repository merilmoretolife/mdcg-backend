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

CLAUSE_MAPPING = {
    "intended_purpose": "Section 4.3.2.2",
    "design": "Section 4.3.2.3",
    "software": "Section 4.3.2.3",
    "materials": "Section 4.3.2.3",
    "sterilization": "Section 4.3.2.3",
    "labeling": "Section 4.3.2.1",
    "editorial": "Section 4.3.2.1",
    "non_design": "Section 4.2",
    "general": "Section 4.1"
}

def classify_change_type(text):
    text = text.lower()
    if any(word in text for word in ["indication", "intended use", "intended purpose", "patient population"]):
        return "intended_purpose"
    if any(word in text for word in ["design", "control", "alarm", "sensor", "dimension"]):
        return "design"
    if any(word in text for word in ["software", "algorithm", "interface", "ui", "interoperability"]):
        return "software"
    if any(word in text for word in ["material", "substance", "coating", "polymer", "contact with body"]):
        return "materials"
    if any(word in text for word in ["sterilization", "eto", "gamma", "terminal sterilization", "sterile"]):
        return "sterilization"
    if any(word in text for word in ["ifu", "instructions", "user manual", "labeling", "label"]):
        return "labeling"
    if any(word in text for word in ["spelling", "clarification", "layout", "formatting"]):
        return "editorial"
    if any(word in text for word in ["supplier", "manufacturer", "production", "facility", "assembly"]):
        return "non_design"
    return "general"

def assess_change_with_ai(change_description):
    change_type = classify_change_type(change_description)
    mapped_clause = CLAUSE_MAPPING.get(change_type, "Section 4.1")

    prompt = f"""
You are an EU medical device regulatory expert.

Your task is to assess whether the following change to a medical device is significant or not, using only the content provided from MDCG 2020-3 Rev.1 guidance (see below).

🔹 You MUST:
- Classify the change type (e.g., software, design, labeling, etc.)
- State whether the change is significant: Yes / No
- Cite the specific section and chart (e.g., "Section 4.3.2.3", "Chart C") that supports your assessment
- Quote the relevant line(s) from the MDCG guidance text if possible
- Use the chart mapping below to cite the chart based on the change type

📌 Chart Mapping (only if applicable):
- Intended purpose → Chart A
- Design (Control, Alarms, Energy, UI) → Chart B
- Software → Chart C
- Material/Substance (Human, Animal, Medicinal) → Chart D
- Sterilization or packaging design → Chart E

For **labeling**, cite either **Section 4.3.2.1** or **4.3.2.2** (whichever is appropriate), and write **“No chart applicable”** in place of a chart reference.

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
State the exact clause used (e.g., “Section 4.3.2.1”) and, if applicable, the corresponding chart (e.g., “Chart B”).

- If the change type is labeling, IFU, user manual, or warning:
  → Cite the section only (4.3.2.1 or 4.3.2.2)
  → Write: “No chart applicable”


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

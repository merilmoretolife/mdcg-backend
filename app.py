from flask import Flask, request, jsonify
from flask_cors import CORS
import re
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)

# Basic NLP keyword matching for text analysis
def analyze_text_input(text, change_type):
    text = text.lower()
    details = {
        "extends_use": False,
        "reduces_use": False,
        "operating_principle": False,
        "adverse_safety": False,
        "new_software_algorithm": False,
        "new_material_contact": False,
        "new_supplier_critical": False,
        "text_insights": []
    }
    
    if change_type == "intended_use":
        if re.search(r"\b(add|extend|new indication|new user|new patient|broader use)\b", text):
            details["extends_use"] = True
            details["text_insights"].append("Text suggests extension of intended use or new indications.")
        if re.search(r"\b(reduce|remove|eliminate|restrict|narrow)\b", text):
            details["reduces_use"] = True
            details["text_insights"].append("Text suggests reduction or elimination of indications.")
    
    elif change_type == "design":
        if re.search(r"\b(operating principle|mechanism|functionality|algorithm|software)\b", text):
            details["operating_principle"] = True
            details["text_insights"].append("Text indicates change to operating principle or functionality.")
        if re.search(r"\b(safety|performance|risk|adverse|failure)\b", text):
            details["adverse_safety"] = True
            details["text_insights"].append("Text suggests potential adverse impact on safety/performance.")
        if re.search(r"\b(new algorithm|software update|software change)\b", text):
            details["new_software_algorithm"] = True
            details["text_insights"].append("Text indicates introduction of new software algorithm.")
    
    elif change_type == "materials":
        if re.search(r"\b(new material|material change|contact with body|biocompatibility)\b", text):
            details["new_material_contact"] = True
            details["text_insights"].append("Text suggests new material in contact with body.")
        if re.search(r"\b(new supplier|critical component|supply chain)\b", text):
            details["new_supplier_critical"] = True
            details["text_insights"].append("Text indicates new supplier for critical component.")
    
    return details

# Decision tree logic based on MDCG 2020-3 Rev.1
def evaluate_change(change_type, details):
    result = {"is_significant": False, "justification": [], "actions": []}
    
    if change_type == "intended_use":
        if details.get("extends_use"):
            result["is_significant"] = True
            result["justification"].append("Change extends intended use or adds indications/users.")
            result["actions"].append("Notify Notified Body for verification of EC certificate validity.")
        elif details.get("reduces_use"):
            result["justification"].append("Change reduces or eliminates indications; not significant.")
            result["actions"].append("Document decision with evidence; no notification required.")
        else:
            result["justification"].append("No significant change to intended use detected.")
            result["actions"].append("Document decision; no further action needed.")
    
    elif change_type == "design":
        if details.get("operating_principle") and details.get("adverse_safety"):
            result["is_significant"] = True
            result["justification"].append("Change to operating principle adversely affects safety/performance.")
            result["actions"].append("Submit change notification to Notified Body.")
        elif details.get("new_software_algorithm"):
            result["is_significant"] = True
            result["justification"].append("Introduction of new software algorithm is significant.")
            result["actions"].append("Notified Body verification required.")
        else:
            result["justification"].append("Design change does not affect safety, performance, or usability.")
            result["actions"].append("Document decision; no notification required.")
    
    elif change_type == "materials":
        if details.get("new_material_contact") or details.get("new_supplier_critical"):
            result["is_significant"] = True
            result["justification"].append("Change involves new material in contact with body or critical supplier.")
            result["actions"].append("Notify Notified Body for assessment.")
        else:
            result["justification"].append("Material change does not impact safety or performance.")
            result["actions"].append("Document decision; no further action needed.")
    
    if details.get("text_insights"):
        result["justification"].extend(details["text_insights"])
    
    return result

# Generate report as text
def generate_report(change_type, details, result, text_input):
    report = f"""
Change Notification Assessment Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
MDCG 2020-3 Rev.1 Compliance

Change Type: {change_type.capitalize()}
Text Description: {text_input}
Details Provided:
{chr(10).join([f'- {k}: {v}' for k, v in details.items() if k != 'text_insights'])}
Text Analysis Insights:
{chr(10).join([f'- {i}' for i in details.get('text_insights', [])]) or '- None'}

Assessment Outcome:
- Significant Change: {'Yes' if result['is_significant'] else 'No'}
- Justification:
{chr(10).join([f'  * {j}' for j in result['justification']])}
- Recommended Actions:
{chr(10).join([f'  * {a}' for a in result['actions']])}

Note: Ensure all decisions are documented and available for competent authority review.
"""
    return report

# API endpoint for change assessment
@app.route('/assess', methods=['POST'])
def assess():
    data = request.get_json()
    change_type = data.get('change_type')
    text_input = data.get('change_description', '')
    checkbox_details = data.get('details', {})
    
    # Analyze text input
    text_details = analyze_text_input(text_input, change_type)
    
    # Combine checkbox and text-based details (checkboxes take precedence)
    combined_details = text_details.copy()
    for key, value in checkbox_details.items():
        if value:
            combined_details[key] = True
            combined_details["text_insights"].append(f"Checkbox confirmed: {key.replace('_', ' ').title()}.")
    
    # Evaluate change
    result = evaluate_change(change_type, combined_details)
    report = generate_report(change_type, combined_details, result, text_input)
    
    return jsonify({
        "result": result,
        "report": report,
        "report_filename": f"change_assessment_{uuid.uuid4()}.txt"
    })

if __name__ == '__main__':
    app.run(debug=True)

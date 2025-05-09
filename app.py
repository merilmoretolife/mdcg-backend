from flask import Flask, request, jsonify
from flask_cors import CORS
import re
from datetime import datetime
import uuid
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
nltk.download('punkt')
nltk.download('stopwords')

app = Flask(__name__)
CORS(app)

# NLP-based change type classification
def classify_change_type(text):
    text = text.lower()
    keywords = {
        'intended_purpose': [
            'indication', 'intended use', 'intended purpose', 'patient population', 'clinical application',
            'target population', 'user', 'anatomical site', 'delivery pathway', 'deployment method'
        ],
        'design': [
            'design', 'specification', 'operating principle', 'control mechanism', 'energy source', 'alarm',
            'dimension', 'sensor', 'connector', 'housing', 'ergonomic', 'functionality', 'component'
        ],
        'software': [
            'software', 'algorithm', 'firmware', 'user interface', 'operating system', 'cybersecurity',
            'data format', 'interoperability', 'diagnostic feature', 'therapeutic feature'
        ],
        'materials': [
            'material', 'substance', 'component', 'supplier', 'biocompatibility', 'coating', 'polymer',
            'medicinal substance', 'human origin', 'animal origin'
        ],
        'manufacturing': [
            'manufacturing', 'production', 'assembly', 'quality control', 'process validation', 'scale-up',
            'subcontractor', 'facility'
        ],
        'labeling': [
            'labeling', 'label', 'instructions', 'user manual', 'packaging', 'warnings', 'precautions'
        ],
        'sterilization': [
            'sterilization', 'sterility', 'sterile', 'cleaning', 'disinfection', 'packaging integrity',
            'shelf life', 'sterilization cycle'
        ]
    }
    
    scores = {k: 0 for k in keywords}
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    tokens = [t for t in tokens if t not in stop_words]
    
    for token in tokens:
        for change_type, kws in keywords.items():
            if any(kw in token or token in kw for kw in kws):
                scores[change_type] += 1
    
    max_score = max(scores.values())
    if max_score == 0:
        return 'unknown'
    return max(k for k, v in scores.items() if v == max_score)

# Analyze text for MDCG 2020-3 Rev.1 details
def analyze_text_input(text):
    text = text.lower()
    details = {
        'extends_use': False,
        'reduces_use': False,
        'operating_principle': False,
        'adverse_safety': False,
        'new_software_algorithm': False,
        'new_material_contact': False,
        'new_supplier_critical': False,
        'clinical_data_required': False,
        'risk_profile_change': False,
        'labeling_change': False,
        'manufacturing_change': False,
        'sterilization_change': False,
        'terminal_sterilization_method': False,
        'sterility_assurance_impact': False,
        'editorial_labeling': False,
        'corrective_action': False,
        'eu_compliance': False,
        'text_insights': []
    }
    
    # General checks
    if re.search(r'\b(clinical data|usability data|new study|validation data)\b', text):
        details['clinical_data_required'] = True
        details['text_insights'].append('Mentions clinical or usability data requirement.')
    if re.search(r'\b(risk|adverse event|safety concern|hazard|performance issue)\b', text):
        details['risk_profile_change'] = True
        details['text_insights'].append('Indicates potential change to risk profile.')
    if re.search(r'\b(no impact|no effect|no safety concern|no risk)\b', text):
        details['text_insights'].append('Claims no impact on safety/performance.')
    if re.search(r'\b(corrective action|field safety)\b', text):
        details['corrective_action'] = True
        details['text_insights'].append('Mentions corrective action.')
    if re.search(r'\b(eu legislation|reach|clp regulation)\b', text):
        details['eu_compliance'] = True
        details['text_insights'].append('Mentions compliance with other EU legislation.')
    
    # Intended Purpose (Chart A)
    if re.search(r'\b(add|extend|new indication|new user|new patient|broader use|new clinical condition|new anatomical site|new delivery pathway|new deployment method)\b', text):
        details['extends_use'] = True
        details['text_insights'].append('Suggests extension of intended purpose or new users.')
    if re.search(r'\b(reduce|remove|restrict|narrow|delete indication|restrict population)\b', text):
        details['reduces_use'] = True
        details['text_insights'].append('Suggests limitation of indications or population.')
    
    # Design (Chart B)
    if re.search(r'\b(operating principle|control mechanism|energy source|alarm system|new sensor|new mechanism|digital control|software driven|new feature)\b', text):
        details['operating_principle'] = True
        details['text_insights'].append('Indicates change to operating principle, control, or alarms.')
    if re.search(r'\b(safety|performance|risk|adverse|failure|usability)\b', text):
        details['adverse_safety'] = True
        details['text_insights'].append('Suggests potential adverse safety/performance impact.')
    
    # Software (Chart C)
    if re.search(r'\b(new algorithm|software update|new feature|new operating system|new interface|interoperability|wireless communication|closed loop|data interpretation|diagnostic|therapeutic)\b', text):
        details['new_software_algorithm'] = True
        details['text_insights'].append('Indicates new software algorithm or feature.')
    if re.search(r'\b(bug fix|minor update|security update|user interface enhancement|language|layout|graphic)\b', text):
        details['text_insights'].append('Suggests minor software change (e.g., bug fix/UI enhancement).')
    
    # Materials (Chart D)
    if re.search(r'\b(new material|material change|contact with body|biocompatibility|human origin|animal origin|medicinal substance|excipient|carrier material)\b', text):
        details['new_material_contact'] = True
        details['text_insights'].append('Suggests new material in contact with body.')
    if re.search(r'\b(new supplier|critical component|supply chain)\b', text):
        details['new_supplier_critical'] = True
        details['text_insights'].append('Mentions new supplier for critical component.')
    
    # Manufacturing
    if re.search(r'\b(manufacturing process|production|assembly|quality control|scale-up|subcontractor|facility)\b', text):
        details['manufacturing_change'] = True
        details['text_insights'].append('Indicates manufacturing process change.')
    
    # Labeling
    if re.search(r'\b(labeling|instructions|user manual|packaging|warnings|precautions)\b', text):
        details['labeling_change'] = True
        details['text_insights'].append('Mentions labeling or instructions change.')
    if re.search(r'\b(spelling|editorial|clarification)\b', text):
        details['editorial_labeling'] = True
        details['text_insights'].append('Suggests editorial/clarification labeling change.')
    
    # Sterilization (Chart E)
    if re.search(r'\b(sterilization method|terminal sterilization|eto|gamma|parametric release|sterile label|packaging integrity|shelf life|storage condition|transportation condition)\b', text):
        details['sterilization_change'] = True
        details['text_insights'].append('Mentions sterilization or packaging change.')
    if re.search(r'\b(eto to gamma|gamma to eto|biological indicator|parametric release|non-sterile to sterile)\b', text):
        details['terminal_sterilization_method'] = True
        details['text_insights'].append('Suggests change to terminal sterilization method.')
    if re.search(r'\b(sterility assurance|seal integrity|microbiological state|sterilization residual)\b', text):
        details['sterility_assurance_impact'] = True
        details['text_insights'].append('Suggests impact on sterility assurance.')
    
    return details

# Evaluate significance per MDCG 2020-3 Rev.1
def evaluate_change(change_type, details):
    result = {"is_significant": False, "justification": [], "actions": []}
    
    # General checks
    if details.get('clinical_data_required'):
        result['is_significant'] = True
        result['justification'].append('Change requires clinical or usability data, indicating significance (MDCG 2020-3 Rev.1, Section 4.3.2).')
        result['actions'].append('Submit change notification to Notified Body with clinical data.')
    if details.get('risk_profile_change') and details.get('adverse_safety'):
        result['is_significant'] = True
        result['justification'].append('Change adversely affects safety/performance, negatively impacting risk/benefit ratio (MDCG 2020-3 Rev.1, Section 4.3.2).')
        result['actions'].append('Notify Notified Body for risk assessment.')
    if details.get('corrective_action'):
        result['justification'].append('Change related to corrective action assessed by competent authority is non-significant unless safety/performance is adversely affected (MDCG 2020-3 Rev.1, Section 4.3.2.1).')
        result['actions'].append('Verify with competent authority; document decision.')
    if details.get('eu_compliance'):
        result['justification'].append('Change to comply with other EU legislation is non-significant unless risk/benefit ratio is negatively affected (MDCG 2020-3 Rev.1, Section 4.3.2.1).')
        result['actions'].append('Document compliance with EU legislation; no notification required unless safety impacted.')
    
    # Chart A: Intended Purpose
    if change_type == 'intended_purpose':
        if details.get('extends_use'):
            result['is_significant'] = True
            result['justification'].append('Extension of intended purpose (e.g., new indications, users, or clinical applications) is significant per Chart A (MDCG 2020-3 Rev.1, Section 4.3.2.2).')
            result['actions'].append('Notify Notified Body to verify EC certificate validity.')
        elif details.get('reduces_use'):
            result['justification'].append('Limitation or deletion of indications/population is non-significant per Chart A (MDCG 2020-3 Rev.1, Section 4.3.2.2).')
            result['actions'].append('Document decision with evidence; no notification required.')
        else:
            result['justification'].append('No significant change to intended purpose detected per Chart A (MDCG 2020-3 Rev.1, Section 4.3.2.2).')
            result['actions'].append('Document decision; no further action needed.')
    
    # Chart B: Design
    elif change_type == 'design':
        if details.get('operating_principle') or details.get('adverse_safety'):
            result['is_significant'] = True
            result['justification'].append('Change to operating principle, control mechanism, energy source, or adverse safety/performance impact is significant per Chart B (MDCG 2020-3 Rev.1, Section 4.3.2.3).')
            result['actions'].append('Submit change notification to Notified Body.')
        else:
            result['justification'].append('Design change does not alter operating principle or adversely affect safety/performance per Chart B (MDCG 2020-3 Rev.1, Section 4.3.2.3).')
            result['actions'].append('Document decision; no notification required.')
    
    # Chart C: Software
    elif change_type == 'software':
        if details.get('new_software_algorithm'):
            result['is_significant'] = True
            result['justification'].append('New software algorithm, medical feature, or interoperability is significant per Chart C (MDCG 2020-3 Rev.1, Section 4.3.2.3).')
            result['actions'].append('Submit change for Notified Body verification.')
        elif 'minor software change' in ' '.join(details['text_insights']).lower():
            result['justification'].append('Minor software change (e.g., bug fix, UI enhancement) is non-significant per Chart C (MDCG 2020-3 Rev.1, Section 4.3.2.3).')
            result['actions'].append('Document decision; no notification required.')
        else:
            result['justification'].append('Software change does not affect safety, performance, or medical functionality per Chart C (MDCG 2020-3 Rev.1, Section 4.3.2.3).')
            result['actions'].append('Document decision; no further action needed.')
    
    # Chart D: Materials
    elif change_type == 'materials':
        if details.get('new_material_contact') or details.get('new_supplier_critical'):
            result['is_significant'] = True
            result['justification'].append('New material in contact with body or critical supplier change is significant per Chart D (MDCG 2020-3 Rev.1, Section 4.3.2.3).')
            result['actions'].append('Notify Notified Body for assessment.')
        else:
            result['justification'].append('Material change does not involve contact with body or critical components per Chart D (MDCG 2020-3 Rev.1, Section 4.3.2.3).')
            result['actions'].append('Document decision; no further action needed.')
    
    # Manufacturing (Section 4.2)
    elif change_type == 'manufacturing':
        if details.get('manufacturing_change') and details.get('risk_profile_change'):
            result['is_significant'] = True
            result['justification'].append('Manufacturing change adversely affects safety/performance, making it significant (MDCG 2020-3 Rev.1, Section 4.2).')
            result['actions'].append('Notify Notified Body for assessment.')
        else:
            result['justification'].append('Manufacturing change does not affect product safety/performance per Section 4.2 (MDCG 2020-3 Rev.1, Section 4.2).')
            result['actions'].append('Document decision; no notification required.')
    
    # Labeling (Section 4.3.2.1, 4.3.2.2)
    elif change_type == 'labeling':
        if details.get('labeling_change') and (details.get('clinical_data_required') or details.get('extends_use')):
            result['is_significant'] = True
            result['justification'].append('Labeling change requiring clinical data or extending intended purpose is significant (MDCG 2020-3 Rev.1, Section 4.3.2.2).')
            result['actions'].append('Notify Notified Body with supporting data.')
        elif details.get('editorial_labeling'):
            result['justification'].append('Editorial or clarification labeling change is non-significant per Section 4.3.2.1 (MDCG 2020-3 Rev.1).')
            result['actions'].append('Document decision; no notification required.')
        else:
            result['justification'].append('Labeling change is minor or administrative, non-significant per Section 4.3.2.2 (MDCG 2020-3 Rev.1).')
            result['actions'].append('Document decision; no notification required.')
    
    # Chart E: Sterilization
    elif change_type == 'sterilization':
        if details.get('terminal_sterilization_method') or details.get('sterility_assurance_impact'):
            result['is_significant'] = True
            result['justification'].append('Change to terminal sterilization method or sterility assurance is significant per Chart E (MDCG 2020-3 Rev.1, Section 4.3.2.3).')
            result['actions'].append('Notify Notified Body for assessment.')
        else:
            result['justification'].append('Sterilization change does not affect method or sterility assurance per Chart E (MDCG 2020-3 Rev.1, Section 4.3.2.3).')
            result['actions'].append('Document decision; no notification required.')
    
    # Unknown change type
    else:
        result['justification'].append('Change type could not be determined; assumed non-significant unless clinical data or risk profile is affected (MDCG 2020-3 Rev.1, Section 4.1).')
        result['actions'].append('Document decision and consult Notified Body if uncertain.')
    
    if details.get('text_insights'):
        result['justification'].extend([f'Text analysis: {i}' for i in details['text_insights']])
    
    return result

# Generate detailed report
def generate_report(change_type, details, result, text_input):
    report = f"""
MDCG 2020-3 Rev.1 Change Assessment Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

1. Change Description:
   {text_input}

2. Detected Change Type:
   {change_type.replace('_', ' ').title()}

3. Text Analysis Insights:
   {chr(10).join([f'   - {i}' for i in details.get('text_insights', [])]) or '   - None'}

4. Assessment Outcome:
   - Significant Change: {'Yes' if result['is_significant'] else 'No'}
   - Justifications:
   {chr(10).join([f'     * {j}' for j in result['justification']])}
   - Recommended Actions:
   {chr(10).join([f'     * {a}' for a in result['actions']])}

5. Notes:
   - This assessment is based on MDCG 2020-3 Rev.1 guidance for legacy devices under Article 120(3c) MDR.
   - Manufacturers must document all changes and ensure compliance with AIMDD/MDD requirements.
   - For significant changes, the device may not be placed on the market under AIMDD/MDD without MDR certification (MDCG 2020-3 Rev.1, Section 4.1).
   - Consult Notified Body and competent authority for complex cases.
"""
    return report

# API endpoint for change assessment
@app.route('/assess', methods=['POST'])
def assess():
    data = request.get_json()
    text_input = data.get('change_description', '')
    
    # Classify change type
    change_type = classify_change_type(text_input)
    
    # Analyze text input
    details = analyze_text_input(text_input)
    
    # Evaluate change
    result = evaluate_change(change_type, details)
    report = generate_report(change_type, details, result, text_input)
    
    return jsonify({
        'change_type': change_type,
        'result': result,
        'report': report,
        'report_filename': f'change_assessment_{uuid.uuid4()}.txt'
    })

if __name__ == '__main__':
    app.run(debug=True)

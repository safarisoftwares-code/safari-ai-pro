import re

path = 'app/services/ai_service.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = '    def _clean_response(self, text: str) -> str:'
end_marker = '    def _hardcoded_response(self, message: str):'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
    new_method = '''    def _clean_response(self, text: str) -> str:
        """Light cleanup - remove LaTeX commands but keep all content."""
        if not text:
            return text
        
        # Replace common LaTeX commands with Unicode
        text = text.replace('\\\\text{', '').replace('\\\\frac{', '').replace('\\\\dfrac{', '')
        text = text.replace('\\\\times', '×').replace('\\\\cdot', '·')
        text = text.replace('\\\\rightarrow', '→').replace('\\\\longrightarrow', '⟶')
        text = text.replace('\\\\leftarrow', '←').replace('\\\\leftrightarrow', '↔')
        text = text.replace('\\\\rightleftharpoons', '⇌')
        text = text.replace('\\\\infty', '∞').replace('\\\\approx', '≈')
        text = text.replace('\\\\leq', '≤').replace('\\\\geq', '≥')
        text = text.replace('\\\\neq', '≠').replace('\\\\pm', '±')
        text = text.replace('\\\\alpha', 'α').replace('\\\\beta', 'β')
        text = text.replace('\\\\gamma', 'γ').replace('\\\\delta', 'δ')
        text = text.replace('\\\\lambda', 'λ').replace('\\\\mu', 'μ')
        text = text.replace('\\\\pi', 'π').replace('\\\\theta', 'θ')
        text = text.replace('\\\\psi', 'ψ').replace('\\\\phi', 'φ')
        text = text.replace('\\\\hbar', 'ℏ').replace('\\\\Delta', 'Δ')
        text = text.replace('\\\\sum', 'Σ').replace('\\\\int', '∫')
        text = text.replace('\\\\sqrt', '√').replace('\\\\partial', '∂')
        text = text.replace('\\\\nabla', '∇').replace('\\\\propto', '∝')
        text = text.replace('\\\\langle', '⟨').replace('\\\\rangle', '⟩')
        text = text.replace('\\\\boxed', '').replace('\\\\mathrm', '').replace('\\\\mathbf', '')
        text = text.replace('\\\\left', '').replace('\\\\right', '')
        text = text.replace('\\\\overline', '').replace('\\\\underline', '')
        text = text.replace('_{', '').replace('^{', '').replace('}', '')
        text = text.replace('\\\\;', ' ').replace('\\\\,', ' ')
        
        # Remove any remaining backslash commands
        text = re.sub(r'\\\\[a-zA-Z]+', '', text)
        
        # Remove standalone backslashes
        text = text.replace('\\\\', '')
        
        return text.strip()

'''
    content = content[:start_idx] + new_method + content[end_idx:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('CLEANER REPLACED')
else:
    print('ERROR: Method not found')

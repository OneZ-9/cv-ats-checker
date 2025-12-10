import fitz  # PyMuPDF
import io

import re

class CVAnalyzer:
    def __init__(self, file_content: bytes):
        self.doc = fitz.open(stream=file_content, filetype="pdf")
        self.text = ""
        self.word_count = 0
        self.image_count = 0
        self.page_count = len(self.doc)
        self.layout_issues = []
        self.recommendations = []
        self.ats_score = 100
        
        # v2 Attributes
        self.contact_info = {"email": None, "phone": None}
        self.missing_sections = []
        self.text_quality_score = 100

    def analyze(self):
        self._extract_text()
        self._check_images()
        self._check_layout()
        self._check_contact_info()
        self._check_sections()
        self._check_text_quality()
        self._calculate_score()
        
        return {
            "word_count": self.word_count,
            "page_count": self.page_count,
            "has_images": self.image_count > 0,
            "image_count": self.image_count,
            "layout_issues": self.layout_issues,
            "text_extractability_score": self.text_quality_score,
            "ats_friendly_score": self.ats_score,
            "status": self._get_status(),
            "recommendations": self.recommendations,
            "contact_info_found": bool(self.contact_info["email"]),
            "missing_sections": self.missing_sections,
            "suggested_data": self._get_suggested_data()
        }

    def _extract_text(self):
        full_text = []
        for page in self.doc:
            full_text.append(page.get_text())
        self.text = "\n".join(full_text)
        print(f"DEBUG: Extracted text length: {len(self.text)}")
        print(f"DEBUG: First 100 chars: {self.text[:100]}")
        self.word_count = len(self.text.split())
        print(f"DEBUG: Word count: {self.word_count}")

    def _check_images(self):
        for page in self.doc:
            self.image_count += len(page.get_images())
        
        if self.image_count > 0:
            self.recommendations.append(f"Found {self.image_count} images. ATS parsers often ignore images.")
            # Penalty applied in _calculate_score

    def _check_layout(self):
        multi_column_detected = False
        for page in self.doc:
            blocks = page.get_text("blocks")
            blocks.sort(key=lambda b: (b[1], b[0]))
            
            for i in range(len(blocks)):
                for j in range(i + 1, len(blocks)):
                    b1 = blocks[i]
                    b2 = blocks[j]
                    if b2[1] > b1[3]: break
                    if b2[0] > b1[2] and b2[1] < b1[3] and b2[3] > b1[1]:
                        if b1[6] == 0 and b2[6] == 0:
                            multi_column_detected = True
                            break
                if multi_column_detected: break
            if multi_column_detected: break
        
        if multi_column_detected:
            self.layout_issues.append("Multi-column layout detected.")
            self.recommendations.append("Use a single-column layout for better ATS parsing.")

    def _check_contact_info(self):
        # Email regex
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', self.text)
        if email_match:
            self.contact_info["email"] = email_match.group(0)
        else:
            self.recommendations.append("No email address detected. Ensure it's in standard text format.")

        # Phone regex (simple)
        phone_match = re.search(r'(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}', self.text)
        if phone_match:
            self.contact_info["phone"] = phone_match.group(0)

    def _check_sections(self):
        # v3: Regex-based section detection to avoid false positives
        # Looks for lines that are likely headers (short, standalone)
        # Patterns allow for some variation like "Work Experience", "Professional Experience"
        
        # v5 & v6: Expand regex to include "Professional Skills", "Educational Qualifications", "Employment History"
        section_patterns = {
            "Experience": r'(?i)^\s*(work|professional|relevant|employment)?\s*(experience|history|background)\s*$',
            "Education": r'(?i)^\s*(educational|academic)?\s*(education|qualifications|background|history)\s*$',
            "Skills": r'(?i)^\s*(technical|core|professional|soft)?\s*skills\s*$'
        }
        
        # v5 & v8: Check for Intern/Trainee/Undergraduate/Student in the first 3000 chars
        # If found, make Experience section optional
        intro_text = self.text[:3000].lower()
        is_early_career = any(keyword in intro_text for keyword in ["intern", "trainee", "undergraduate", "student"])
        
        if is_early_career:
            # Remove Experience from required checks if it's an early career CV
            if "Experience" in section_patterns:
                del section_patterns["Experience"]
        
        # Split text into lines for regex matching
        lines = self.text.split('\n')
        
        for section, pattern in section_patterns.items():
            found = False
            for line in lines:
                if re.match(pattern, line.strip()):
                    found = True
                    break
            
            if not found:
                self.missing_sections.append(section)
                self.recommendations.append(f"Missing section: '{section}'. Ensure you have a clear header for this.")

    def _check_text_quality(self):
        if not self.text:
            self.text_quality_score = 0
            return

        # Calculate ratio of alphanumeric characters + spaces vs total
        clean_chars = len(re.findall(r'[a-zA-Z0-9\s\.,]', self.text))
        total_chars = len(self.text)
        
        if total_chars == 0:
            self.text_quality_score = 0
            return

        ratio = clean_chars / total_chars
        
        if ratio < 0.8: # More than 20% garbage/symbols
            self.text_quality_score = 40
            self.recommendations.append("High noise detected in text (possible bad OCR or special fonts). Use standard fonts.")
        else:
            # Also check word count for extractability
            if self.word_count > 50:
                self.text_quality_score = 100
            else:
                self.text_quality_score = 50

    def _calculate_score(self):
        # Base Score
        score = 100
        
        # 1. Image Penalty
        if self.image_count > 0:
            score -= min(20, self.image_count * 5)
            
        # 2. Layout Penalty
        if self.layout_issues:
            score -= 15
            
        # 3. Contact Info Penalty
        if not self.contact_info["email"]:
            score -= 20
            
        # 4. Missing Sections Penalty
        for section in self.missing_sections:
            if section == "Experience": score -= 15
            elif section == "Education": score -= 15
            elif section == "Skills": score -= 10
            
        # 5. Word Count Penalty
        if self.word_count < 200:
            score -= 20
            self.recommendations.append("Word count is too low (< 200 words).")
        elif self.word_count > 2000:
            score -= 10
            self.recommendations.append("CV is too long (> 2000 words).")
            
        # 6. Text Quality Penalty
        if self.text_quality_score < 60:
            score -= 30
            
        self.ats_score = max(0, min(100, score))

    def _get_status(self):
        # v4: Updated status labels
        # ATS Optimized: ATS >= 75 AND Extractability >= 75
        # Needs Improvement: 50 <= ATS < 75
        # Not ATS Friendly: ATS < 50
        
        if self.ats_score >= 75 and self.text_quality_score >= 75:
            return "ATS Optimized"
        elif self.ats_score >= 50:
            return "Needs Improvement"
        else:
            return "Not ATS Friendly"

    def _get_suggested_data(self):
        return {
            "summary": f"Found {self.word_count} words. Contact info: {'Found' if self.contact_info['email'] else 'Missing'}.",
            "details": "Ensure standard fonts, single column layout, and clear section headers."
        }

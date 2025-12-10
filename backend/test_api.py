import requests
import fitz

def create_sample_pdf(filename, text, add_image=False, multi_column=False):
    doc = fitz.open()
    page = doc.new_page()
    y = 50
    
    if multi_column:
        # Column 1
        page.insert_text((50, 50), text[:len(text)//2], fontsize=10)
        # Column 2 (distinct X, overlapping Y)
        page.insert_text((300, 50), text[len(text)//2:], fontsize=10)
    else:
        lines = text.split('\n')
        for line in lines:
            if y > 800:
                page = doc.new_page()
                y = 50
            page.insert_text((50, y), line, fontsize=10)
            y += 12
        
    if add_image:
        # Create a dummy image (black square)
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 100), 0)
        # Just insert it, it will be black
        if y > 700: # Ensure space for image
             page = doc.new_page()
             y = 50
        page.insert_image(fitz.Rect(100, y, 200, y+100), pixmap=pix)

    doc.save(filename)
    doc.close()

def test_api():
    base_url = "http://127.0.0.1:8001"
    
    # 1. Create a "Good" PDF (Complete)
    good_text = "Name: John Doe\nEmail: john@example.com\nPhone: 123-456-7890\n"
    good_text += "Experience\nWorked at Google as a Software Engineer. Developed backend systems using Python and FastAPI.\n" * 30
    good_text += "Education\nBS Computer Science from University of Tech.\n"
    good_text += "Skills\nPython, React, Docker, Kubernetes, AWS, SQL, NoSQL.\n"
    create_sample_pdf("good_cv.pdf", good_text)
    
    # 2. Create a "Bad" PDF (Image + Low Word Count + No Email)
    create_sample_pdf("bad_cv.pdf", "Short CV.", add_image=True)

    # 3. Create a Multi-column PDF
    create_sample_pdf("multicolumn_cv.pdf", "Column 1 text.\n" * 50 + "Column 2 text.\n" * 50, multi_column=True)
    
    # 4. Create a "Missing Sections" PDF (Text mentions sections but no headers)
    # This should fail the regex check for headers
    missing_sections_text = "Name: Jane\nEmail: jane@example.com\n"
    missing_sections_text += "I have a lot of experience in Python. My education was good. I have skills in React.\n" * 20
    create_sample_pdf("missing_sections.pdf", missing_sections_text)

    # 5. Create an "Intern" PDF (No Experience section, but has "Intern" keyword)
    # Should NOT fail for missing Experience
    intern_text = "Name: Intern User\nEmail: intern@example.com\nSummary: Seeking an Intern position.\n"
    intern_text += "Education\nBS CS.\n"
    intern_text += "Skills\nPython.\n" * 20 # Add content to pass word count
    create_sample_pdf("intern_cv.pdf", intern_text)

    # 6. Create a "Professional Skills" PDF (Uses "Professional Skills" header)
    # Should pass the Skills check
    skills_text = "Name: Pro User\nEmail: pro@example.com\n"
    skills_text += "Experience\nWorked at Google.\n" * 20
    skills_text += "Education\nBS CS.\n"
    skills_text += "Professional Skills\nPython, React.\n"
    create_sample_pdf("pro_skills_cv.pdf", skills_text)

    # 7. Create a "Varied Headers" PDF
    # Uses "Employment History" and "Educational Qualifications"
    varied_text = "Name: Varied User\nEmail: varied@example.com\n"
    varied_text += "Employment History\nWorked at Amazon.\n" * 20
    varied_text += "Educational Qualifications\nBS CS.\n"
    varied_text += "Technical Skills\nPython.\n"
    create_sample_pdf("varied_headers_cv.pdf", varied_text)

    # 8. Create an "ALL CAPS" PDF
    # Uses "EXPERIENCE", "EDUCATION", "SKILLS"
    all_caps_text = "Name: Caps User\nEmail: caps@example.com\n"
    all_caps_text += "EXPERIENCE\nWorked at Apple.\n" * 20
    all_caps_text += "EDUCATION\nBS CS.\n"
    all_caps_text += "SKILLS\nSwift.\n"
    create_sample_pdf("all_caps_cv.pdf", all_caps_text)

    files = [
        ("all_caps_cv.pdf", "All Caps CV")
    ]
    
    # 9. Create a "Hidden Undergraduate" PDF
    # User reported: "KalutaraFINAL YEAR COMPUTER ENGINEERING UNDERGRADUATE" failed to trigger exception
    hidden_undergrad_text = "Name: Student\nAddress: Kalutara\n"
    hidden_undergrad_text += "FINAL YEAR COMPUTER ENGINEERING UNDERGRADUATE\n"
    hidden_undergrad_text += "Education\nBS CS.\n"
    hidden_undergrad_text += "Skills\nPython.\n" * 20
    create_sample_pdf("hidden_undergrad.pdf", hidden_undergrad_text)
    
    files.append(("hidden_undergrad.pdf", "Hidden Undergraduate CV"))

    # 10. Create a "Student" PDF
    # Uses "Student" keyword to skip Experience check
    student_text = "Name: New Student\nSummary: I am a final year Student.\n"
    student_text += "Education\nBS CS.\n"
    student_text += "Skills\nPython.\n" * 20
    create_sample_pdf("student_cv.pdf", student_text)
    
    files = [
        ("student_cv.pdf", "Student CV")
    ]
    
    for filename, desc in files:
        print(f"\nTesting {desc}...")
        with open(filename, "rb") as f:
            response = requests.post(f"{base_url}/analyze", files={"file": (filename, f, "application/pdf")})
            
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data['status']}")
            print(f"Word Count: {data['word_count']}")
            print(f"Score: {data['ats_friendly_score']}")
            print(f"Recommendations: {data['recommendations']}")
            print(f"Contact Info: {data['contact_info_found']}")
            print(f"Missing Sections: {data['missing_sections']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_api()

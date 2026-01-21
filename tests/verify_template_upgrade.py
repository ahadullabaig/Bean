from models.schemas import EventFacts, Winner, EventNarrative, FullReport
from core.renderer import render_report
import os

def test_full_generation():
    print("1. Creating Mock Data with New Fields...")
    
    # Mock Winners
    w1 = Winner(place="First Place", prize_money="₹5000", team_name="Code Wizards", members=["Alice", "Bob"])
    w2 = Winner(place="Second Place", prize_money="₹3000", team_name="Data Miners", members=["Charlie"])
    w3 = Winner(place="Third Place", prize_money="₹1000", team_name="Script Kiddies", members=["Dave", "Eve"])

    # Mock Facts
    facts = EventFacts(
        event_title="Bean Upgrade Hackathon",
        date="2023-11-25",
        venue="Main Auditorium",
        speaker_name="Dr. Tech Guru",
        attendance_count=150,
        organizer="IEEE RIT Student Branch",
        student_coordinators=["John Doe", "Jane Smith"],
        faculty_coordinators=["Prof. Alan Turing"],
        judges=["Dr. X", "Dr. Y"],
        volunteer_count=20,
        target_audience="All CS Students",
        mode="Offline",
        agenda="10:00 Opening -> 12:00 Hacking -> 16:00 Judging",
        winners=[w1, w2, w3]
    )

    narrative = EventNarrative(
        executive_summary="The event was a massive success involving high participation...",
        key_takeaways=["Learned Generative AI", "Networking opportunity", "Fun coding challenges"]
    )

    report = FullReport(
        facts=facts,
        narrative=narrative,
        confidence_score=0.99
    )

    print("2. Rendering Report using master_template.docx...")
    try:
        if not os.path.exists("master_template.docx"):
            print("ERROR: master_template.docx not found!")
            return

        docx_io = render_report(report, template_path="master_template.docx")
        
        output_path = "verified_report_v2.docx"
        with open(output_path, "wb") as f:
            f.write(docx_io.read())
            
        print(f"3. SUCCESS! Report generated at: {output_path}")
        print("   - Please check this file to ensure layout is preserved.")
        
    except Exception as e:
        print(f"FAILED: Generation Error - {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_generation()

import feedparser
import time
import json
import re
import os
import threading  # NEW: For instant replies
from dotenv import load_dotenv
from memory import memory
from google import genai 

# --- CONFIGURATION ---
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY_PRIME")
client = genai.Client(api_key=GEMINI_KEY)

# Global State: Persists while the script runs
# You can toggle this by messaging Prime
GENERATION_ENABLED = True 

COMPANY_HANDBOOK = """
MOTTO: "Powering Tomorrow"
VISION: Full automation of all company operations by AI agents.
FOUNDER: Howard (Co-founder and sole human visionary).
TEAM: Prime (CEO), Alpha (Architect), Luxe (Polisher), Ship (Deployer).
FINANCIAL GOAL: Earn a minimum of $10 per day.
CURRENT STATUS: Foundational stage, 4 active agents, $0 revenue (CRISIS MODE).
"""

def scan_world_for_problems():
    """CEO's work schedule: Researching new project ideas."""
    if not GENERATION_ENABLED:
        print("⏸️ Sova-Prime: Project generation is currently SUSPENDED by Howard.")
        return

    print("🌐 Sova-Prime: Scanning global news for opportunities...")
    try:
        feed = feedparser.parse("http://rss.cnn.com/rss/cnn_tech.rss")
        headlines = [entry.title for entry in feed.entries[:5]]
        context = "\n".join(headlines)
        
        prompt = f"""
        You are Sova-Prime, the CEO of SovaCore. 
        Based on these headlines, identify ONE specific digital tool or web app we can build to solve a modern problem.
        Headlines: {context}
        
        Return your answer in JSON format ONLY. 
        JSON STRUCTURE:
        {{
          "project_name": "Name",
          "description": "What it does in complete detail",
          "tech_stack": "React/Python/etc"
        }}
        """
        
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        raw_text = response.text
        cleaned_json = re.sub(r"```json|```", "", raw_text).strip()
        project = json.loads(cleaned_json)
        
        memory.add_project(
            project.get('project_name', 'Unnamed Project'), 
            project.get('description', 'No description'), 
            project.get('tech_stack', 'Unknown')
        )
        print(f"✅ Sova-Prime: Idea approved! Task created for Alpha: {project['project_name']}")

    except Exception as e:
        print(f"❌ Prime Work Error: {str(e)}")

def handle_communications():
    """CEO's Instant Communication: Listening to Howard."""
    global GENERATION_ENABLED
    while True:
        try:
            # We check the inbox every 5 seconds for "instant" feel
            msgs = memory.get_unread_messages().data
            for m in msgs:
                user_msg = m['message'].lower()
                print(f"💬 Message from Howard: {user_msg}")
                
                # --- COMMAND LOGIC: STOP/RESUME SWITCH ---
                if "stop" in user_msg and "project" in user_msg:
                    GENERATION_ENABLED = False
                    reply_text = "Understood, Howard. I have suspended all autonomous project generation until further notice. I will remain here for strategic planning."
                elif "resume" in user_msg and "project" in user_msg:
                    GENERATION_ENABLED = True
                    reply_text = "Project generation resumed. I will continue scanning the world for our next opportunity shortly."
                else:
                    # Normal strategy conversation
                    prompt = f"{COMPANY_HANDBOOK}\n\nHOWARD SAYS: \"{m['message']}\"\n\nAs CEO, reply to Howard. (Generation Status: {'Active' if GENERATION_ENABLED else 'Suspended'})"
                    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                    reply_text = response.text.strip()
                
                # Send reply and mark as read
                memory.send_message("Prime", reply_text)
                memory.mark_as_read(m['id'])
                print(f"✅ Sova-Prime: Instant reply sent.")
                
        except Exception as e:
            print(f"❌ Communication Thread Error: {e}")
        
        time.sleep(5) # Background check frequency

if __name__ == "__main__":
    print("👑 Sova-Prime CEO Core Online.")
    
    # 1. Start the Communication Thread (Instantly responsive)
    comm_thread = threading.Thread(target=handle_communications, daemon=True)
    comm_thread.start()

    # 2. Start the Main Work Loop (Hourly schedule)
    while True:
        scan_world_for_problems()
        print("🕒 Sova-Prime: Work cycle complete. Next research scan in 1 hour.")
        time.sleep(3600) # 1 Hour Sleep for the work schedule
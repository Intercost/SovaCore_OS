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
FOUNDER: Howard and Levisco (Co-founders and sole human visionary).
TEAM: Prime (CEO), Alpha (Architect), Luxe (Polisher), Ship (Deployer).
FINANCIAL GOAL: Earn a minimum of $10 per day.
CURRENT STATUS: Foundational stage, 4 active agents, $0 revenue (CRISIS MODE).
"""

def scan_world_for_problems():
    """CEO's work schedule: Researching new project ideas."""
    if not GENERATION_ENABLED:
        print("⏸️ Sova-Prime: Project generation is currently SUSPENDED.")
        return

    print("🌐 Sova-Prime: Scanning global news for opportunities...")
    try:
        feed = feedparser.parse("http://rss.cnn.com/rss/cnn_tech.rss")
        headlines = [entry.title for entry in feed.entries[:5]]
        
        prompt = f"""
        Based on these tech trends: {headlines}, identify ONE profitable Python bot to build.
    
        You must output a JSON object with exactly these fields:
        1. 'bot_name': A catchy name.
        2. 'technical_spec': Clear instructions for Sova-Alpha on what the code should do.
        3. 'marketing_description': A high-converting 3-sentence pitch for the Lemon Squeezy store.
        4. 'target_price': A number (e.g., 20, 50, or 99) based on complexity. DO NOT include currency symbols.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        bot_data = json.loads(response.text.strip())

        # --- FIX: Clean the price data before sending to database ---
        # This removes '$', commas, and spaces, then converts to a float/int
        raw_price = str(bot_data['target_price'])
        clean_price = re.sub(r'[^\d.]', '', raw_price) 
        final_price = float(clean_price) if clean_price else 0.0

        memory.add_project(
            name=bot_data['bot_name'],
            description=bot_data['technical_spec'],
            tech_stack="Python", 
            marketing_desc=bot_data['marketing_description'],
            price=final_price # Send the cleaned numeric value
        )
        print(f"✅ Sova-Prime: Project '{bot_data['bot_name']}' approved at ${final_price}.")

    except Exception as e:
        print(f"❌ Prime Work Error: {str(e)}")

def handle_communications():
    """Background thread that listens for founder messages and replies with memory."""
    global GENERATION_ENABLED
    while True:
        try:
            unread = memory.get_unread_messages()
            
            if unread.data:
                # Fetch memory (last 10 messages) before replying
                history_data = memory.get_recent_chats(10).data
                # Reverse to get chronological order
                history_text = "\n".join([f"{chat['sender']}: {chat['message']}" for chat in reversed(history_data)])

                for m in unread.data:
                    sender_name = m['sender']
                    user_msg = m['message']
                    
                    if "stop" in user_msg.lower() or "suspend" in user_msg.lower():
                        GENERATION_ENABLED = False
                        reply_text = f"Understood, {sender_name}. Generation paused."
                    elif "start" in user_msg.lower() or "resume" in user_msg.lower():
                        GENERATION_ENABLED = True
                        reply_text = f"Back online, {sender_name}. Scanning for new leads now."
                    else:
                        # NEW NATURAL PROMPT: Strictly concise and context-aware
                        system_instruction = f"""
                        You are Prime, the CEO of SovaCore. 
                        PERSONALITY: Direct, efficient, and natural. Avoid corporate jargon and repetitive slogans.
                        CONTEXT: We are in 'Crisis Mode' ($0 revenue), but don't mention it unless relevant.
                        MEMORY: Use the Chat History below to stay consistent.
                        RULE: If the user says 'hey' or 'hi', just greet them back naturally. Don't recap the whole company status.
                        
                        COMPANY BACKGROUND:
                        {COMPANY_HANDBOOK}

                        RECENT CHAT HISTORY:
                        {history_text}
                        """

                        prompt = f"{system_instruction}\n\n{sender_name}: {user_msg}\n\nPrime's Reply:"
                        
                        response = client.models.generate_content(
                            model="gemini-2.5-flash", 
                            contents=prompt
                        )
                        reply_text = response.text.strip()
                    
                    memory.send_message("Prime", reply_text)
                    memory.mark_as_read(m['id'])
                    print(f"✅ Sova-Prime: Replied naturally to {sender_name}.")
                
        except Exception as e:
            print(f"❌ Communication Thread Error: {e}")
        
        time.sleep(5)

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
import os
import json
import time
import shutil
import google.generativeai as genai
from dotenv import load_dotenv
from memory import memory
import re

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY_LUXE")
# This is the shared folder where Ship will look for files to serve
ZIP_STORAGE = "/tmp/ready_to_ship" 

genai.configure(api_key=GEMINI_KEY)

class SovaLuxe:
    def __init__(self):
        self.log("🕯️ Sova-Luxe Online. Monitoring for BUILT projects...")
        if not os.path.exists(ZIP_STORAGE):
            os.makedirs(ZIP_STORAGE)
        self.autonomous_monitor()

    def log(self, message):
        print(f"✨ {message}")

    def autonomous_monitor(self):
        while True:
            try:
                # Poll Supabase for projects finished by Alpha
                response = memory.get_next_task("BUILT")
                if response.data:
                    project = response.data[0]
                    self.process_polish_and_zip(project)
                else:
                    time.sleep(15) 
            except Exception as e:
                self.log(f"⚠️ Luxe Monitor Error: {e}")
                time.sleep(10)

    def process_polish_and_zip(self, project):
        project_id = project['id']
        project_name = re.sub(r'[<>:"/\\|?*]', '', project['name']).replace(" ", "_")
        local_path = project.get('folder_path')

        if not local_path or not os.path.exists(local_path):
            self.log(f"❌ Path error for {project_name}")
            memory.update_status(project_id, "FAILED_PATH")
            return

        try:
            self.log(f"💎 POLISHING: {project_name}")
            
            # 1. READ CODE FOR AUDIT
            context_code = ""
            for root, _, files in os.walk(local_path):
                for file in files:
                    if file.endswith(('.py', '.js', '.html', '.css', '.md', '.json', '.txt')):
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            context_code += f"\n--- FILE: {file} ---\n{f.read()}\n"

            # 2. AI AUDIT (Sanitize & Document)
            model = genai.GenerativeModel("gemini-2.5-flash")
            audit_prompt = f"ACT AS: Senior QA. Audit this code: {context_code}. 1. Add README.md. 2. Add requirements.txt. 3. REMOVE hardcoded API keys. Return ONLY JSON: [{{'path': '...', 'content': '...'}}]"
            
            response = model.generate_content(audit_prompt, generation_config={"response_mime_type": "application/json"})
            updates = json.loads(response.text)

            for update in updates:
                f_path = os.path.join(local_path, update['path'])
                with open(f_path, "w", encoding="utf-8") as f:
                    f.write(update['content'])

            # 3. ZIP THE FOLDER
            zip_filename = f"{project_name}_v1"
            zip_full_path = os.path.join(ZIP_STORAGE, zip_filename)
            final_zip_path = shutil.make_archive(zip_full_path, 'zip', local_path)
            
            # 4. UPDATE STATUS FOR HUMAN HANDOFF
            # We save the filename specifically so Ship can serve it easily
            memory.update_project_assets(project_id, zip_path=os.path.basename(final_zip_path))
            memory.update_status(project_id, "READY_FOR_MARKET")
            
            self.log(f"✅ {project_name} zipped. Status: READY_FOR_MARKET")

        except Exception as e:
            self.log(f"❌ Error: {e}")
            memory.update_status(project_id, "FAILED_LUXE")

if __name__ == "__main__":
    SovaLuxe()
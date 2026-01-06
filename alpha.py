import os
import json
import threading
import google.generativeai as genai
from dotenv import load_dotenv
import re
import subprocess  
import time
from memory import memory 

# --- CONFIGURATION ---
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY_ALPHA")
# In Railway, /tmp is writable. Ensure this matches your .env
DESKTOP_PATH = os.getenv("PROJECT_DESKTOP_PATH", "/tmp/projects")

genai.configure(api_key=GEMINI_KEY) 

class UniversalArchitect:
    def __init__(self):
        print("🤖 Sova-Alpha Headless Online (Railway Mode). Monitoring Supabase...")
        self.autonomous_monitor()

    def log(self, message):
        print(f"> {message}")

    def autonomous_monitor(self):
        while True:
            try:
                # Changed to "pending" to match Prime's initial status
                response = memory.get_next_task("pending")
                if response.data:
                    project = response.data[0]
                    self.log(f"⚡ NEW JOB: {project['name']}")
                    self.build_project(project)
                else:
                    time.sleep(10) 
            except Exception as e:
                self.log(f"⚠️ Monitor Error: {e}")
                time.sleep(10)

    def run_command(self, command, cwd):
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, 
            shell=True,
            text=True,
            cwd=cwd
        )
        for line in process.stdout:
            self.log(line.strip())
        process.wait()
        return process.returncode

    def build_project(self, project):
        project_id = project['id']
        # Fixed key mapping to match your memory.py schema
        description = project['technical_spec'] 
        tech_stack = project.get('tech_stack', 'Python')

        # Sanitize project name for folder creation
        project_name = re.sub(r'[<>:"/\\|?*]', '', project['name']).replace(" ", "_")
        
        try:
            model = genai.GenerativeModel("gemini-2.5-flash") # Updated to current flash model
            
            system_prompt = f"""
            You are Sova-Alpha.
            ACT AS: Senior Software Architect.
            PROJECT: {project_name}
            TASK: Build a complete, functional code repository for: {description}
            REQUIRED TECH STACK: {tech_stack}
            
            RULES:
            1. Output ONLY valid JSON.
            2. Do not use Markdown code blocks.
            3. Include a 'start_command'.

            JSON STRUCTURE:
            {{
                "project_name": "name",
                "tech_stack": "languages",
                "start_command": "command_to_run",
                "files": [ {{"path": "file.ext", "content": "code"}} ]
            }}
            """

            response = model.generate_content(system_prompt)
            
            # Clean JSON response
            clean_json = re.sub(r"```json|```", "", response.text).strip()
            data = json.loads(clean_json)
            
            full_project_path = os.path.join(DESKTOP_PATH, project_name)
            os.makedirs(full_project_path, exist_ok=True)

            # --- FILE CREATION ---
            for file_info in data['files']:
                f_path = os.path.join(full_project_path, file_info['path'])
                os.makedirs(os.path.dirname(f_path), exist_ok=True)
                with open(f_path, "w", encoding="utf-8") as f:
                    f.write(file_info['content'])
                self.log(f"✅ Created: {file_info['path']}")

            # --- INSTALLATION PHASE ---
            self.log("\n📦 --- INSTALLATION PHASE ---")
            if os.path.exists(os.path.join(full_project_path, "package.json")):
                self.run_command("npm install", full_project_path)
            elif os.path.exists(os.path.join(full_project_path, "requirements.txt")):
                self.run_command("pip install -r requirements.txt", full_project_path)

            # --- UPDATE SHARED MEMORY FOR LUXE ---
            # 1. Save the folder path so Luxe knows where to look
            memory.update_project_assets(project_id, folder_path=full_project_path)
            
            # 2. Update status to "BUILT" so Luxe picks it up
            memory.update_status(project_id, "BUILT")
            
            self.log(f"✅ Project {project_name} built at {full_project_path}. Handing over to Luxe.")

        except Exception as e:
            self.log(f"❌ ERROR: {str(e)}")
            memory.update_status(project_id, "FAILED")

if __name__ == "__main__":
    agent = UniversalArchitect()
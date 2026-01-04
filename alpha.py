import os
import json
import threading
import google.generativeai as genai
from dotenv import load_dotenv  # New: For security
import re
import subprocess  
import time
from memory import memory 

# --- CONFIGURATION ---
load_dotenv()
# Get API key and Path from .env
GEMINI_KEY = os.getenv("GEMINI_API_KEY_ALPHA")
DESKTOP_PATH = os.getenv("PROJECT_DESKTOP_PATH", "C:\\AI_Projects")

genai.configure(api_key=GEMINI_KEY) 

class UniversalArchitect:
    def __init__(self):
        print("🤖 Sova-Alpha Headless Online. Monitoring Supabase...")
        self.autonomous_monitor()

    def log(self, message):
        print(f"> {message}")

    def autonomous_monitor(self):
        while True:
            try:
                response = memory.get_next_task("QUEUED")
                if response.data:
                    project = response.data[0]
                    self.log(f"⚡ NEW JOB: {project['project_name']}")
                    self.build_project(project)
                else:
                    time.sleep(10) 
            except Exception as e:
                self.log(f"⚠️ Monitor Error: {e}")
                time.sleep(10)

    def run_command(self, command, cwd):
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                   shell=True, text=True, cwd=cwd)
        for line in process.stdout:
            self.log(line.strip())
        process.wait()
        return process.returncode

    def build_project(self, project):
        project_id = project['id']
        description = project['description']
        tech_stack = project.get('tech_stack', 'Any suitable stack')

        # FIX: Sanitize project name for Windows file systems
        project_name = re.sub(r'[<>:"/\\|?*]', '', project['project_name']).replace(" ", "_")
        
        try:
            # FIX: Using 'gemini-1.5-flash' for maximum compatibility
            model = genai.GenerativeModel("gemini-2.5-flash") 
            
            system_prompt = f"""
            You are Sova-Alpha.
            ACT AS: Senior Software Architect.
            PROJECT: {project_name}
            TASK: Build a complete, functional code repository for: {description}
            REQUIRED TECH STACK: {tech_stack}
            
            RULES:
            1. Output ONLY valid JSON.
            2. Do not use Markdown code blocks (no ```json).
            3. Include a 'start_command'.

            JSON STRUCTURE:
            {{
                "project_name": "name",
                "tech_stack": "languages",
                "start_command": "command_to_run",
                "files": [ {{"path": "file.ext", "content": "code"}} ]
            }}

            When generating code for new SovaCore agents:
            1. Use the 'google-genai' library.
            2. Hardcode the model as 'gemini-2.5-flash' for maximum reliability.
            3. Use the environment variable 'GEMINI_API_KEY_ALPHA' for the API key.
            4. Ensure the agent connects to the existing SovaCore Supabase database via 'memory.py'.
            """

            response = model.generate_content(system_prompt)
            
            # --- ROBUST JSON PARSE ---
            raw_text = response.text
            # Remove any accidental markdown backticks the AI might add
            clean_json = re.sub(r"```json|```", "", raw_text).strip()
            data = json.loads(clean_json)
            
            full_project_path = os.path.join(DESKTOP_PATH, project_name)
            os.makedirs(full_project_path, exist_ok=True)

            # --- FILE CREATION ---
            for file_info in data['files']:
                f_path = os.path.join(full_project_path, file_info['path'])
                # Ensure subdirectories exist
                os.makedirs(os.path.dirname(f_path), exist_ok=True)
                
                with open(f_path, "w", encoding="utf-8") as f:
                    f.write(file_info['content'])
                self.log(f"✅ Created: {file_info['path']}")

            # --- INSTALLATION PHASE ---
            self.log("\n📦 --- INSTALLATION PHASE ---")
            if os.path.exists(os.path.join(full_project_path, "package.json")):
                self.run_command("npm install", full_project_path)
            
            # --- GITHUB UPLOAD ---
            repo_url = self.git_push_to_github(full_project_path, project_name)

            # --- UPDATE SUPABASE ---
            memory.client.table("projects").update({
                "status": "BUILT",
                "github_url": repo_url
            }).eq("id", project_id).execute()
            
            self.log(f"✅ Project {project_name} status set to BUILT.")

        except Exception as e:
            self.log(f"❌ ERROR: {str(e)}")
            memory.update_status(project_id, "FAILED")

    def git_push_to_github(self, project_path, repo_name):
        self.log(f"Pushing {repo_name} to GitHub...")
        # Note: Ensure 'gh auth status' passes in your terminal first
        commands = [
            "git init",
            "git add .",
            'git commit -m "Initial build by Sova-Alpha"',
            f"gh repo create {repo_name} --public --source=. --remote=origin --push"
        ]
        for cmd in commands:
            self.run_command(cmd, project_path)
        
        # Replace 'Intercost' with your actual GitHub username from your .env if needed
        return f"[https://github.com/Intercost/](https://github.com/Intercost/){repo_name}"

if __name__ == "__main__":
    # Start the agent without creating a Tkinter window
    agent = UniversalArchitect()
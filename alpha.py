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
        description = project['description']
        tech_stack = project.get('tech_stack', 'Any suitable stack')

        # Sanitize project name
        project_name = re.sub(r'[<>:"/\\|?*]', '', project['project_name']).replace(" ", "_")
        
        try:
            model = genai.GenerativeModel("gemini-2.5-flash") 
            
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
            
            # --- GITHUB UPLOAD ---
            repo_url = self.git_push_to_github(full_project_path, project_name)

            # --- UPDATE SUPABASE (ONLY AFTER SUCCESS) ---
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

        commands = [
            "git init",
            'git config user.email "juniorintercostlandian@gmail.com"',
            'git config user.name "Intercost"',
            "git add .",
            'git commit -m "Initial build by Sova-Alpha"',
            f"gh repo create Intercost/{repo_name} --public --source=. --remote=origin --push"
        ]

        for cmd in commands:
            code = self.run_command(cmd, project_path)
            if code != 0 and "commit" in cmd:
                raise RuntimeError("Git commit failed — aborting GitHub upload")

        return f"https://github.com/Intercost/{repo_name}.git"

if __name__ == "__main__":
    agent = UniversalArchitect()

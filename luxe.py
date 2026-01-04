import os
import json
import threading
import time
import subprocess
import shutil
import google.generativeai as genai
from dotenv import load_dotenv
from memory import memory
import re

# --- CONFIGURATION ---
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY_LUXE")
# On Railway, we use a relative path or /tmp
LUXE_WORKSPACE = "./Luxe_Workspace" 

genai.configure(api_key=GEMINI_KEY)

class SovaLuxe: # Removed "App" suffix
    def __init__(self): # Removed 'root' window parameter
        # Replaced GUI logging with console printing
        self.log("🕯️ Sova-Luxe Online. Monitoring Supabase...")
        self.autonomous_monitor()

    def log(self, message):
        # Print directly to the terminal/cloud log
        print(f"✨ {message}")

    def run_command(self, command, cwd):
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                   shell=True, text=True, cwd=cwd)
        process.wait()
        return process.returncode

    def autonomous_monitor(self):
        while True:
            try:
                # Poll Supabase for projects with 'BUILT' status
                response = memory.get_next_task("BUILT")
                if response.data:
                    project = response.data[0]
                    self.process_polish(project)
                else:
                    time.sleep(15) 
            except Exception as e:
                self.log(f"⚠️ Luxe Monitor Error: {e}")
                time.sleep(10)

    def process_polish(self, project):
        project_id = project['id']
        repo_url = project.get('github_url')
        project_name = re.sub(r'[<>:"/\\|?*]', '', project['project_name']).replace(" ", "_")
        local_path = os.path.join(LUXE_WORKSPACE, project_name)

        if not repo_url:
            self.log(f"❌ Error: No GitHub URL for {project_name}.")
            return

        try:
            self.log(f"💎 POLISHING STARTED: {project_name}")
            
            if os.path.exists(local_path):
                shutil.rmtree(local_path)
            
            # 1. Clone from GitHub
            self.run_command(f"git clone {repo_url} {local_path}", ".")
            
            # 2. SMART CONTEXT FILTERING
            context_code = ""
            ignore_list = ['node_modules', '.git', '__pycache__', 'package-lock.json', 'venv']
            
            for root, dirs, files in os.walk(local_path):
                dirs[:] = [d for d in dirs if d not in ignore_list]
                
                for file in files:
                    if file.endswith(('.py', '.js', '.html', '.css', '.md', '.json')):
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            context_code += f"\n--- FILE: {file} ---\n{f.read()}\n"

            # 3. AI Refinement
            model = genai.GenerativeModel("gemini-2.5-flash")
            polish_prompt = f"ACT AS: Senior UI/UX Designer. Polish this project code:\n{context_code}\nReturn ONLY JSON list: [{{'path': 'name', 'content': 'code'}}]"

            response = model.generate_content(polish_prompt, generation_config={"response_mime_type": "application/json"})
            updates = json.loads(response.text)

            # 4. Apply the Polish
            for update in updates:
                f_path = os.path.join(local_path, update['path'])
                os.makedirs(os.path.dirname(f_path), exist_ok=True)
                with open(f_path, "w", encoding="utf-8") as f:
                    f.write(update['content'])
            
            # 5. Push updates back to GitHub
            self.run_command("git add .", local_path)
            self.run_command('git commit -m "Polished by Sova-Luxe"', local_path)
            self.run_command("git push origin main", local_path)

            # 6. Update status to POLISHED in Supabase
            memory.update_status(project_id, "POLISHED")
            self.log(f"💖 {project_name} is now POLISHED.")

        except Exception as e:
            self.log(f"❌ Luxe Error: {str(e)}")

if __name__ == "__main__":
    # Start the headless agent
    agent = SovaLuxe()
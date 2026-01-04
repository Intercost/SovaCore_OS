import os
import threading
import time
import subprocess
import re
import shutil
from dotenv import load_dotenv
from memory import memory

# --- CONFIGURATION ---
load_dotenv()
# On Railway/Cloud, we use a relative path
SHIP_WORKSPACE = "./Ship_Workspace"

if not os.path.exists(SHIP_WORKSPACE):
    os.makedirs(SHIP_WORKSPACE)

class SovaShip: 
    def __init__(self): 
        self.log("🚢 Sova-Ship Headless Online. Awaiting POLISHED projects...")
        self.autonomous_monitor()

    def log(self, message):
        print(f"🚢 {message}")

    # --- MODIFIED CHANGE 1: IMPROVED RUN_COMMAND ---
    def run_command(self, command, cwd, env=None):
        self.log(f"🛠️ Running: {command}")
        current_env = os.environ.copy()
        if env:
            current_env.update(env)
            
        # Using subprocess.run with check=True forces the script to WAIT for completion
        # and raises an error if the command fails, preventing "Directory not found" loops.
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                    shell=True, text=True, cwd=cwd, env=current_env, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            self.log(f"❌ Command Failed: {e.stderr}")
            return ""

    def autonomous_monitor(self):
        while True:
            try:
                # Poll Supabase for projects with 'POLISHED' status
                response = memory.get_next_task("POLISHED")
                if response.data:
                    project = response.data[0]
                    project_id = project['id']
                    project_name = project['project_name']
                    
                    self.log(f"🚀 MISSION RECEIVED: Deploying {project_name}...")
                    
                    # --- MODIFIED CHANGE 2: ROBUST CLONE & WAIT LOGIC ---
                    local_path = os.path.join(SHIP_WORKSPACE, project_name)
                    gh_token = os.getenv("GH_TOKEN")
                    
                    if not os.path.exists(local_path):
                        self.log(f"🚢 📥 Folder missing in Ship container. Cloning from GitHub...")

                        safe_project_name_url = project_name.replace(" ", "%20")
                        repo_url = f"https://{gh_token}@github.com/Intercost/{safe_project_name_url}.git"
                        
                        # Explicitly clone into a directory named project_name inside SHIP_WORKSPACE
                        self.run_command(f'git clone "{repo_url}" "{project_name}"', SHIP_WORKSPACE)
                        
                        # Double-check that the directory actually exists now
                        if not os.path.exists(local_path):
                            self.log(f"🚢 ❌ Ship Error: Directory not found after clone: {local_path}")
                            time.sleep(10)
                            continue

                    # 1. Update status to SHIPPING in Supabase
                    memory.update_status(project_id, "SHIPPING")

                    # 2. Deployment Logic (Vercel for Frontends)
                    vercel_token = os.getenv("VERCEL_TOKEN")
                    if vercel_token:
                        vercel_cmd = f"vercel --prod --yes --token {vercel_token}"
                    else:
                        vercel_cmd = "vercel --prod --yes"
                        
                    vercel_output = self.run_command(vercel_cmd, f'"{local_path}"')
                    
                    # Extract live URL from output
                    live_url = "Pending..."
                    urls = re.findall(r'https://[a-zA-Z0-9.-]+\.vercel\.app', vercel_output)
                    if urls:
                        live_url = urls[-1] 

                    # 3. Deployment Logic (Railway for Backends)
                    tech_stack = project.get('tech_stack', '')
                    if any(tech in tech_stack for tech in ["Python", "Node", "Backend"]):
                        self.log("⚙️ Backend detected. Deploying to Railway...")
                        railway_token = os.getenv("RAILWAY_TOKEN")
                        self.run_command("railway up --detach", f'"{local_path}"', {"RAILWAY_TOKEN": railway_token})

                    # 4. Finalize in Supabase
                    memory.client.table("projects").update({
                        "status": "COMPLETE",
                        "live_url": live_url
                    }).eq("id", project_id).execute()
                    
                    self.log(f"✅ MISSION ACCOMPLISHED: {project_name} is LIVE at {live_url}")

                else:
                    time.sleep(15) # Wait for new polished projects

            except Exception as e:
                self.log(f"❌ Ship Error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    SovaShip()
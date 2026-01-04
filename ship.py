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

class SovaShip: # Removed "App" suffix
    def __init__(self): # Removed 'root' window parameter
        self.log("🚢 Sova-Ship Headless Online. Awaiting POLISHED projects...")
        self.autonomous_monitor()

    def log(self, message):
        # Print directly to the terminal/cloud log
        print(f"🚢 {message}")

    def run_command(self, command, cwd, env=None):
        # Pass environment variables (like RAILWAY_TOKEN) if provided
        current_env = os.environ.copy()
        if env:
            current_env.update(env)
            
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                   shell=True, text=True, cwd=cwd, env=current_env)
        output = ""
        for line in process.stdout:
            output += line
        process.wait()
        return output

    def autonomous_monitor(self):
        while True:
            try:
                # Poll Supabase for projects with 'POLISHED' status
                response = memory.get_next_task("POLISHED")
                if response.data:
                    project = response.data[0]
                    self.process_deployment(project)
                else:
                    time.sleep(30) 
            except Exception as e:
                self.log(f"⚠️ Ship Monitor Error: {e}")
                time.sleep(10)

    def process_deployment(self, project):
        project_id = project['id']
        repo_url = project.get('github_url')
        project_name = re.sub(r'[<>:"/\\|?*]', '', project['project_name']).replace(" ", "_")
        local_path = os.path.join(SHIP_WORKSPACE, project_name)

        if not repo_url:
            self.log(f"❌ Error: No GitHub URL for {project_name}.")
            return

        try:
            self.log(f"🚀 DEPLOYMENT STARTED: {project_name}")
            
            if os.path.exists(local_path):
                shutil.rmtree(local_path)
            
            # 1. Clone the Polished repo
            self.run_command(f"git clone {repo_url} {local_path}", SHIP_WORKSPACE)

            # 2. Deployment Logic (Vercel for Frontends)
            self.log("📦 Deploying Frontend to Vercel...")
            
            # Use VERCEL_TOKEN for non-interactive login in the cloud
            vercel_token = os.getenv("VERCEL_TOKEN")
            if vercel_token:
                vercel_cmd = f"vercel --prod --yes --token {vercel_token}"
            else:
                vercel_cmd = "vercel --prod --yes"
                
            vercel_output = self.run_command(vercel_cmd, local_path)
            
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
                # CLI automatically uses RAILWAY_TOKEN if set in env
                self.run_command("railway up --detach", local_path, {"RAILWAY_TOKEN": railway_token})

            # 4. Finalize in Supabase
            memory.client.table("projects").update({
                "status": "COMPLETE",
                "live_url": live_url
            }).eq("id", project_id).execute()
            
            self.log(f"✅ MISSION ACCOMPLISHED: {project_name} is LIVE at {live_url}")

        except Exception as e:
            self.log(f"❌ Ship Error: {str(e)}")

if __name__ == "__main__":
    # Start the headless agent
    agent = SovaShip()
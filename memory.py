import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class SovaMemory:
    def __init__(self):
        # Initialize Supabase client using env variables
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def add_project(self, name, description, tech_stack):
        """Prime uses this to hire the team for a new job."""
        data = {
            "project_name": name,
            "description": description,
            "tech_stack": tech_stack,
            "status": "QUEUED" 
        }
        return self.client.table("projects").insert(data).execute()

    def get_next_task(self, role_status):
        """Agents use this to see if there is work for them."""
        return self.client.table("projects").select("*").eq("status", role_status).order("id").limit(1).execute()

    def update_status(self, project_id, new_status):
        """Allows agents to move a project to the next stage."""
        return self.client.table("projects").update({"status": new_status}).eq("id", project_id).execute()
    
    def get_staff(self):
        """FIXED INDENTATION: Prime uses this to see who is currently working."""
        return self.client.table("staff").select("*").execute()

    def update_staff_status(self, staff_id, status):
        """FIXED INDENTATION: Prime uses this to hire or fire."""
        return self.client.table("staff").update({"status": status}).eq("id", staff_id).execute()

    def get_unread_messages(self):
        """Prime checks for new messages from Howard."""
        return self.client.table("communications").select("*").eq("is_read", False).eq("sender", "Howard").execute()

    def send_message(self, sender, message):
        """Used by both Howard (from dashboard) and Prime."""
        return self.client.table("communications").insert({"sender": sender, "message": message}).execute()

    def mark_as_read(self, msg_id):
        return self.client.table("communications").update({"is_read": True}).eq("id", msg_id).execute()

# Initialize global memory instance
memory = SovaMemory()
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class SovaMemory:
    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def add_project(self, name, description, tech_stack, marketing_desc, price):
        """Modified: Prime now adds marketing info and pricing strategy."""
        data = {
            "name": name,
            "technical_spec": description, # Used by Alpha
            "tech_stack": tech_stack,
            "marketing_description": marketing_desc, # Used by Lemon Squeezy
            "price": price,
            "status": "pending" # Initial state for Alpha
        }
        return self.client.table("bots").insert(data).execute()

    def get_next_task(self, status):
        """Agents fetch work based on the status (pending, building, zipped, etc)."""
        return self.client.table("bots").select("*").eq("status", status).order("created_at").limit(1).execute()

    def update_status(self, project_id, new_status):
        """Moves the bot through the assembly line."""
        return self.client.table("bots").update({"status": new_status}).eq("id", project_id).execute()

    def update_project_assets(self, project_id, folder_path=None, zip_path=None):
        """Luxe uses this to store the location of the code and the final zip."""
        update_data = {}
        if folder_path: update_data["folder_path"] = folder_path
        if zip_path: update_data["zip_path"] = zip_path
        
        return self.client.table("bots").update(update_data).eq("id", project_id).execute()

    def save_deployment_link(self, project_id, checkout_url):
        """Ship uses this to save the final Lemon Squeezy URL."""
        return self.client.table("bots").update({
            "checkout_url": checkout_url,
            "status": "deployed"
        }).eq("id", project_id).execute()

    # --- Communication Methods (Keep these as they were) ---
    # In memory.py
    def get_unread_messages(self):
        """Fetches unread messages from both Howard and Levisco."""
        # OLD: .eq("sender", "Howard")
        # NEW: Fetches if sender is either Howard or Levisco
        return self.client.table("communications") \
            .select("*") \
            .eq("is_read", False) \
            .in_("sender", ["Howard", "Levisco"]) \
            .execute()
    
    def get_recent_chats(self, limit=10):
        """Retrieves the last N messages for context/memory."""
        return self.client.table("communications") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()

    def send_message(self, sender, message):
        return self.client.table("communications").insert({"sender": sender, "message": message}).execute()

    def mark_as_read(self, msg_id):
        return self.client.table("communications").update({"is_read": True}).eq("id", msg_id).execute()

memory = SovaMemory()
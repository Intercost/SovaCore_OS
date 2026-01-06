import os
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from memory import memory
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app) 

# This must match where Luxe saves the zips
ZIP_STORAGE = "/tmp/ready_to_ship"

@app.route('/download/<filename>')
def download_file(filename):
    """Triggered when you click 'Download Zip' in your dashboard."""
    return send_from_directory(ZIP_STORAGE, filename, as_attachment=True)

@app.route('/finalize', methods=['POST'])
def finalize():
    """Triggered when you paste the Lemon Squeezy link and hit 'Ship It'."""
    try:
        data = request.json
        project_id = data.get('id')
        checkout_url = data.get('url')
        
        if not project_id or not checkout_url:
            return jsonify({"status": "error", "message": "Missing info"}), 400

        # Update Supabase: status -> 'deployed', save the link
        memory.save_deployment_link(project_id, checkout_url)
        
        print(f"🚀 MISSION ACCOMPLISHED: Project {project_id} is LIVE.")
        return jsonify({"status": "success", "message": "Bot is now in the Marketplace!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    if not os.path.exists(ZIP_STORAGE):
        os.makedirs(ZIP_STORAGE)
    # Defaulting to 5001 to avoid common Mac/Windows conflicts on 5000
    app.run(host='0.0.0.0', port=5001)

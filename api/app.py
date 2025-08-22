# api/app.py
import os
import json
import random
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'warhammer_data.json')

try:
    groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
except Exception as e:
    print(f"Error initializing Groq client: {e}")
    groq_client = None

# --- Helper Functions to Read/Write to JSON file ---
def read_db():
    with open(DB_PATH, 'r') as f:
        return json.load(f)

def write_db(data):
    with open(DB_PATH, 'w') as f:
        json.dump(data, f, indent=2)

# --- API Endpoints ---
@app.route('/api/add_unit_to_roster', methods=['POST'])
def add_unit_to_roster():
    data = request.get_json()
    roster_name = data.get('roster_name', 'default_roster')
    unit_name = data.get('unit_name')
    
    if not unit_name:
        return jsonify({"error": "Missing 'unit_name' field"}), 400
        
    db_data = read_db()
    
    if roster_name not in db_data['rosters']:
        db_data['rosters'][roster_name] = []

    db_data['rosters'][roster_name].append({"unit_name": unit_name})
    write_db(db_data)
    
    return jsonify({"message": f"Unit '{unit_name}' added to roster '{roster_name}'."})

@app.route('/api/view_roster', methods=['GET'])
def view_roster():
    roster_name = request.args.get('roster_name', 'default_roster')
    db_data = read_db()
    roster = db_data['rosters'].get(roster_name, [])
    
    if roster:
        return jsonify({roster_name: roster})
    else:
        return jsonify({"error": f"Roster '{roster_name}' not found or is empty."}), 404

@app.route('/api/simulate_combat', methods=['POST'])
def simulate_combat():
    data = request.get_json()
    attacks = data.get('attacks') # Number of dice
    skill = data.get('skill')     # e.g., 3+ to hit
    strength = data.get('strength')
    toughness = data.get('toughness')
    save = data.get('save')       # e.g., 4+ to save
    
    try:
        # --- Hit Rolls ---
        hits = 0
        for _ in range(attacks):
            roll = random.randint(1, 6)
            if roll >= skill:
                hits += 1
        
        # --- Wound Rolls ---
        wounds = 0
        wound_roll_target = 4  # Default S vs T
        if strength > toughness: wound_roll_target = 3
        if strength < toughness: wound_roll_target = 5
        if strength >= toughness * 2: wound_roll_target = 2
        if strength * 2 <= toughness: wound_roll_target = 6
        
        for _ in range(hits):
            roll = random.randint(1, 6)
            if roll >= wound_roll_target:
                wounds += 1
                
        # --- Save Rolls ---
        failed_saves = 0
        for _ in range(wounds):
            roll = random.randint(1, 6)
            if roll < save:
                failed_saves += 1 # This is the damage that goes through

        return jsonify({
            "simulation_result": {
                "hits": hits,
                "wounds": wounds,
                "successful_saves": wounds - failed_saves,
                "damage_dealt": failed_saves
            }
        })
    except Exception as e:
        return jsonify({"error": f"Failed to simulate combat. Check input values. Error: {e}"}), 400

if __name__ == '__main__':
    app.run(debug=True)
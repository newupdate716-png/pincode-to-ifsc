from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

BASE_URL = "https://api.postalpincode.in/pincode/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json"
}


def get_pincode_info(pincode):
    """Fetch pincode details from official postal API."""
    try:
        r = requests.get(f"{BASE_URL}{pincode}", headers=HEADERS, timeout=5)
        r.raise_for_status()
        data = r.json()
        if not data or data[0].get("Status") != "Success":
            return None

        po_data = data[0].get("PostOffice", [])
        if not po_data:
            return None

        first = po_data[0]
        return {
            "pincode": pincode,
            "district": first.get("District"),
            "state": first.get("State"),
            "post_offices": [p["Name"].lower() for p in po_data]
        }
    except Exception:
        return None


def get_ifsc_suggestions(state, district):
    """Suggest sample IFSC codes based on known state/district."""
    known_ifsc = {
        ("ANDHRA PRADESH", "EAST GODAVARI"): [
            {"BANK": "STATE BANK OF INDIA", "IFSC": "SBIN0004843", "BRANCH": "NAGARAM"},
            {"BANK": "CANARA BANK", "IFSC": "CNRB0003331", "BRANCH": "NAGARAM"},
            {"BANK": "INDIAN BANK", "IFSC": "IDIB000N029", "BRANCH": "NAGARAM"},
        ]
    }
    return known_ifsc.get((state.upper(), district.upper()), [])


@app.route("/info", methods=["GET"])
def info_lookup():
    """Endpoint: /info?pincode=533247"""
    pincode = request.args.get("pincode")
    if not pincode:
        return jsonify({"error": "Missing ?pincode= parameter"}), 400

    data = get_pincode_info(pincode)
    if not data:
        return jsonify({"error": "Invalid or unavailable pincode"}), 404

    all_banks = get_ifsc_suggestions(data["state"], data["district"])
    available_banks = [
        b for b in all_banks
        if any(b["BRANCH"].lower() in po for po in data["post_offices"])
    ]

    return jsonify({
        "pincode": data["pincode"],
        "district": data["district"],
        "state": data["state"],
        "available_banks": available_banks or "No matching bank branches found"
    })


@app.route("/", methods=["GET"])
def home():
    """Root endpoint."""
    return jsonify({
        "message": "Pincode to IFSC Info API",
        "usage": "/info?pincode=533247"
    })


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
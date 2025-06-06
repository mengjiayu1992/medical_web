from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from collections import defaultdict
import json
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Load configuration
with open("config.json") as f:
    config = json.load(f)

ADMIN_PASSWORD = config.get("admin_password", "admin123")
CPT_MAP = config.get("cpt_map", {})

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            coinsurance = float(request.form.get("coinsurance", 0))
            deductible_remaining = float(request.form.get("deductible", 0))
            balance_due = float(request.form.get("balance", 0))
            entries = []
            grand_total = 0
            today_total = 0
            service_summary = defaultdict(float)

            for code in CPT_MAP:
                use = request.form.get(f"use_{code}")
                if not use:
                    continue

                deductible_checked = request.form.get(f"deductible_{code}")
                coinsurance_checked = request.form.get(f"coinsurance_{code}")
                copay_checked = request.form.get(f"copay_{code}")
                today_checked = request.form.get(f"today_{code}")

                name, charge = CPT_MAP[code]
                deductible_amt = float(request.form.get("deduct_amt", 0)) if deductible_checked else 0
                copay_amt = float(request.form.get("copay_amt", 0)) if copay_checked else 0

                deductible_paid = min(deductible_amt, deductible_remaining)
                deductible_remaining -= deductible_paid
                charge_after_deductible = charge - deductible_paid

                coinsurance_paid = charge_after_deductible * (coinsurance / 100) if coinsurance_checked else 0
                total_due = deductible_paid + coinsurance_paid + copay_amt
                grand_total += total_due
                if today_checked:
                    today_total += total_due

                service_summary[name] += total_due
                entries.append((f"{name} ({code})", total_due))

            return render_template("result.html", entries=entries, service_summary=service_summary,
                                   grand_total=grand_total + balance_due,
                                   today_total=today_total + balance_due)
        except Exception as e:
            return f"Error: {e}"

    return render_template("index.html", cpt_map=CPT_MAP)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('edit'))
        else:
            return render_template("admin.html", error="Invalid password")
    return render_template("admin.html")

@app.route("/edit", methods=["GET", "POST"])
def edit():
    if not session.get("admin"):
        return redirect(url_for('admin'))

    if request.method == "POST":
        for code in CPT_MAP:
            new_charge = request.form.get(code)
            try:
                CPT_MAP[code][1] = float(new_charge)
            except:
                pass
        config['cpt_map'] = CPT_MAP
        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)
        return redirect(url_for('edit'))

    return render_template("edit.html", cpt_map=CPT_MAP)

if __name__ == "__main__":
    app.run(debug=True)

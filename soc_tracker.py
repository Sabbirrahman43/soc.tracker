#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║       SOC L1 INCIDENT TRACKER v1.0           ║
║       Built for the trenches 🛡️              ║
╚══════════════════════════════════════════════╝
Usage: python3 soc_tracker.py
"""

import json
import os
import csv
import sys
import uuid
from datetime import datetime

# ─── ANSI Colors ────────────────────────────────────────────────────────────
R  = "\033[0m"          # Reset
B  = "\033[1m"          # Bold
DIM= "\033[2m"          # Dim

RED    = "\033[91m"
YEL    = "\033[93m"
GRN    = "\033[92m"
BLU    = "\033[94m"
CYN    = "\033[96m"
MAG    = "\033[95m"
WHT    = "\033[97m"
GREY   = "\033[90m"

BG_RED = "\033[41m"
BG_YEL = "\033[43m"
BG_BLU = "\033[44m"
BG_GRN = "\033[42m"

# ─── Config ─────────────────────────────────────────────────────────────────
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "soc_incidents.json")
EXPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "soc_export.csv")

SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
STATUSES   = ["NEW", "IN_PROGRESS", "ESCALATED", "RESOLVED", "CLOSED"]
CATEGORIES = [
    "Malware", "Phishing", "Brute Force", "Unauthorized Access",
    "Data Exfiltration", "DDoS", "Ransomware", "Insider Threat",
    "Vulnerability Exploit", "Suspicious Activity", "Other"
]

SEV_COLOR = {
    "CRITICAL": f"{B}{BG_RED} CRITICAL {R}",
    "HIGH":     f"{B}{RED} HIGH     {R}",
    "MEDIUM":   f"{B}{YEL} MEDIUM   {R}",
    "LOW":      f"{B}{GRN} LOW      {R}",
}

STATUS_COLOR = {
    "NEW":         f"{B}{BLU}NEW{R}",
    "IN_PROGRESS": f"{B}{YEL}IN_PROGRESS{R}",
    "ESCALATED":   f"{B}{RED}ESCALATED{R}",
    "RESOLVED":    f"{B}{GRN}RESOLVED{R}",
    "CLOSED":      f"{GREY}CLOSED{R}",
}

# ─── DB Helpers ─────────────────────────────────────────────────────────────
def load_db():
    if not os.path.exists(DB_FILE):
        return {"incidents": [], "counter": 0}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

# ─── Utility ────────────────────────────────────────────────────────────────
def clear():
    os.system("clear" if os.name == "posix" else "cls")

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def prompt(label, options=None, default=None, allow_empty=False):
    """Generic input prompt with optional numbered options."""
    if options:
        for i, opt in enumerate(options, 1):
            print(f"  {GREY}{i}.{R} {opt}")
        while True:
            val = input(f"  {CYN}▶ {label}{R} [{default or ''}]: ").strip()
            if not val and default:
                return default
            if val.isdigit() and 1 <= int(val) <= len(options):
                return options[int(val) - 1]
            # Allow direct string match
            matches = [o for o in options if o.upper() == val.upper()]
            if matches:
                return matches[0]
            print(f"  {RED}✗ Invalid choice.{R}")
    else:
        while True:
            val = input(f"  {CYN}▶ {label}{R}: ").strip()
            if val or allow_empty:
                return val
            if default is not None:
                return default
            print(f"  {RED}✗ Cannot be empty.{R}")

def divider(char="─", color=GREY, width=70):
    print(f"{color}{char * width}{R}")

def header(title):
    clear()
    divider("═", CYN)
    print(f"{B}{CYN}  🛡️  SOC L1 INCIDENT TRACKER  ·  {WHT}{title}{R}")
    divider("═", CYN)
    print()

# ─── Dashboard ──────────────────────────────────────────────────────────────
def show_dashboard(db):
    header("DASHBOARD")
    incidents = db["incidents"]
    total = len(incidents)

    # Stats
    by_status = {s: 0 for s in STATUSES}
    by_sev    = {s: 0 for s in SEVERITIES}
    for inc in incidents:
        by_status[inc["status"]] = by_status.get(inc["status"], 0) + 1
        by_sev[inc["severity"]]  = by_sev.get(inc["severity"], 0) + 1

    open_count = sum(by_status[s] for s in ["NEW", "IN_PROGRESS", "ESCALATED"])

    print(f"  {B}{WHT}📊 SUMMARY{R}")
    divider()
    print(f"  Total Incidents : {B}{WHT}{total}{R}    "
          f"Open : {B}{RED}{open_count}{R}    "
          f"Resolved/Closed : {B}{GRN}{by_status['RESOLVED'] + by_status['CLOSED']}{R}")
    print()

    print(f"  {B}BY SEVERITY{R}              {B}BY STATUS{R}")
    divider()
    rows = max(len(SEVERITIES), len(STATUSES))
    for i in range(rows):
        left = right = ""
        if i < len(SEVERITIES):
            s = SEVERITIES[i]
            cnt = by_sev[s]
            bar = "█" * cnt
            left = f"  {SEV_COLOR[s]:>28}  {B}{WHT}{cnt:>3}{R}  {RED if s in ('CRITICAL','HIGH') else YEL if s=='MEDIUM' else GRN}{bar[:20]}{R}"
        if i < len(STATUSES):
            s = STATUSES[i]
            cnt = by_status[s]
            right = f"    {STATUS_COLOR[s]:>30} {B}{WHT}{cnt:>3}{R}"
        print(f"{left:<50}{right}")

    print()
    # Recent 5
    if incidents:
        active = [i for i in incidents if i["status"] not in ("CLOSED","RESOLVED")]
        active.sort(key=lambda x: x["created"], reverse=True)
        recent = active[:5]
        if recent:
            print(f"\n  {B}{YEL}⚡ OPEN / ACTIVE INCIDENTS{R}")
            divider()
            _print_incident_table(recent)

def _print_incident_table(incidents):
    print(f"  {B}{GREY}{'ID':<8} {'SEVERITY':<10} {'STATUS':<14} {'CATEGORY':<20} {'TITLE':<28} {'ASSIGNED':<12} {'CREATED'}{R}")
    divider(char="·")
    for inc in incidents:
        sev_plain = inc["severity"]
        sev_col = {"CRITICAL": RED+B, "HIGH": RED, "MEDIUM": YEL, "LOW": GRN}.get(sev_plain, R)
        sta_col = {"NEW": BLU+B, "IN_PROGRESS": YEL+B, "ESCALATED": RED+B, "RESOLVED": GRN, "CLOSED": GREY}.get(inc["status"], R)
        print(
            f"  {CYN}{inc['id']:<8}{R} "
            f"{sev_col}{sev_plain:<10}{R} "
            f"{sta_col}{inc['status']:<14}{R} "
            f"{inc['category']:<20} "
            f"{inc['title'][:26]:<28} "
            f"{inc.get('assignee','—')[:10]:<12} "
            f"{GREY}{inc['created'][:16]}{R}"
        )
    print()

# ─── List Incidents ──────────────────────────────────────────────────────────
def list_incidents(db, filter_status=None, filter_sev=None):
    header("ALL INCIDENTS")
    incidents = db["incidents"]

    if filter_status:
        incidents = [i for i in incidents if i["status"] == filter_status]
    if filter_sev:
        incidents = [i for i in incidents if i["severity"] == filter_sev]

    if not incidents:
        print(f"  {GREY}No incidents found.{R}\n")
        return

    incidents_sorted = sorted(incidents, key=lambda x: (
        SEVERITIES.index(x["severity"]),
        STATUSES.index(x["status"]),
        x["created"]
    ))
    _print_incident_table(incidents_sorted)

# ─── Add Incident ────────────────────────────────────────────────────────────
def add_incident(db):
    header("NEW INCIDENT")
    db["counter"] = db.get("counter", 0) + 1
    inc_id = f"INC-{db['counter']:04d}"

    print(f"  {B}{WHT}Creating {CYN}{inc_id}{R}\n")

    title    = prompt("Title (short description)")
    print(f"\n  {B}Severity:{R}")
    severity = prompt("Select severity", options=SEVERITIES, default="MEDIUM")
    print(f"\n  {B}Category:{R}")
    category = prompt("Select category", options=CATEGORIES, default="Suspicious Activity")
    assignee = prompt("Assignee (your name / leave blank for unassigned)", allow_empty=True) or "Unassigned"
    source   = prompt("Alert source (e.g. SIEM, EDR, Email)", allow_empty=True) or "—"
    desc     = prompt("Description / initial notes", allow_empty=True) or ""

    incident = {
        "id":        inc_id,
        "title":     title,
        "severity":  severity,
        "status":    "NEW",
        "category":  category,
        "assignee":  assignee,
        "source":    source,
        "description": desc,
        "created":   now_str(),
        "updated":   now_str(),
        "timeline":  [
            {"ts": now_str(), "author": assignee, "note": f"Incident created. Source: {source}. {desc}"}
        ]
    }

    db["incidents"].append(incident)
    save_db(db)
    print(f"\n  {GRN}{B}✔ Incident {inc_id} created successfully!{R}")
    input(f"\n  {GREY}Press ENTER to continue…{R}")

# ─── View Incident ───────────────────────────────────────────────────────────
def view_incident(db):
    header("VIEW INCIDENT")
    inc_id = input(f"  {CYN}▶ Enter Incident ID (e.g. INC-0001){R}: ").strip().upper()
    inc = next((i for i in db["incidents"] if i["id"] == inc_id), None)
    if not inc:
        print(f"\n  {RED}✗ Incident {inc_id} not found.{R}")
        input(f"  {GREY}Press ENTER…{R}")
        return

    sev_col = {"CRITICAL": BG_RED+B, "HIGH": RED+B, "MEDIUM": YEL+B, "LOW": GRN+B}.get(inc["severity"], R)
    print()
    divider("═", CYN)
    print(f"  {B}{CYN}{inc['id']}{R}  {sev_col} {inc['severity']} {R}  {STATUS_COLOR[inc['status']]}")
    divider("═", CYN)
    print(f"  {B}Title    :{R} {WHT}{inc['title']}{R}")
    print(f"  {B}Category :{R} {inc['category']}")
    print(f"  {B}Assignee :{R} {inc.get('assignee','—')}")
    print(f"  {B}Source   :{R} {inc.get('source','—')}")
    print(f"  {B}Created  :{R} {GREY}{inc['created']}{R}")
    print(f"  {B}Updated  :{R} {GREY}{inc['updated']}{R}")
    if inc.get("description"):
        print(f"\n  {B}Description:{R}")
        print(f"  {inc['description']}")

    print(f"\n  {B}{YEL}📋 TIMELINE{R}")
    divider()
    for entry in inc.get("timeline", []):
        print(f"  {GREY}{entry['ts']}{R}  {CYN}[{entry['author']}]{R}  {entry['note']}")

    print()
    input(f"  {GREY}Press ENTER to continue…{R}")

# ─── Update Incident ─────────────────────────────────────────────────────────
def update_incident(db):
    header("UPDATE INCIDENT")
    inc_id = input(f"  {CYN}▶ Enter Incident ID{R}: ").strip().upper()
    inc = next((i for i in db["incidents"] if i["id"] == inc_id), None)
    if not inc:
        print(f"\n  {RED}✗ Incident {inc_id} not found.{R}")
        input(f"  {GREY}Press ENTER…{R}")
        return

    sev_col = {"CRITICAL": BG_RED+B, "HIGH": RED+B, "MEDIUM": YEL+B, "LOW": GRN+B}.get(inc["severity"], R)
    print(f"\n  {B}{CYN}{inc['id']}{R}  {sev_col} {inc['severity']} {R}  {STATUS_COLOR[inc['status']]}  {WHT}{inc['title']}{R}\n")

    print(f"  {B}What to update?{R}")
    action = prompt("Choose action", options=[
        "Update status",
        "Update severity",
        "Update assignee",
        "Add timeline note",
        "Cancel"
    ])

    if action == "Cancel":
        return

    author = input(f"  {CYN}▶ Your name (for timeline){R}: ").strip() or inc.get("assignee", "SOC")

    if action == "Update status":
        print(f"\n  {B}New Status:{R}")
        new_val = prompt("Select status", options=STATUSES, default=inc["status"])
        old = inc["status"]
        inc["status"] = new_val
        inc["timeline"].append({"ts": now_str(), "author": author,
                                 "note": f"Status changed: {old} → {new_val}"})
        print(f"\n  {GRN}✔ Status updated to {new_val}{R}")

    elif action == "Update severity":
        print(f"\n  {B}New Severity:{R}")
        new_val = prompt("Select severity", options=SEVERITIES, default=inc["severity"])
        old = inc["severity"]
        inc["severity"] = new_val
        inc["timeline"].append({"ts": now_str(), "author": author,
                                 "note": f"Severity changed: {old} → {new_val}"})
        print(f"\n  {GRN}✔ Severity updated to {new_val}{R}")

    elif action == "Update assignee":
        new_val = prompt("New assignee name")
        old = inc.get("assignee", "—")
        inc["assignee"] = new_val
        inc["timeline"].append({"ts": now_str(), "author": author,
                                 "note": f"Reassigned: {old} → {new_val}"})
        print(f"\n  {GRN}✔ Assignee updated to {new_val}{R}")

    elif action == "Add timeline note":
        note = prompt("Enter note / findings")
        inc["timeline"].append({"ts": now_str(), "author": author, "note": note})
        print(f"\n  {GRN}✔ Note added.{R}")

    inc["updated"] = now_str()
    save_db(db)
    input(f"\n  {GREY}Press ENTER to continue…{R}")

# ─── Search ──────────────────────────────────────────────────────────────────
def search_incidents(db):
    header("SEARCH")
    query = input(f"  {CYN}▶ Search (title / category / assignee / ID){R}: ").strip().lower()
    results = [
        i for i in db["incidents"]
        if query in i["id"].lower()
        or query in i["title"].lower()
        or query in i["category"].lower()
        or query in i.get("assignee", "").lower()
        or query in i.get("description", "").lower()
    ]
    print()
    if results:
        print(f"  {GRN}Found {len(results)} result(s):{R}\n")
        _print_incident_table(results)
    else:
        print(f"  {GREY}No results for '{query}'.{R}\n")
    input(f"  {GREY}Press ENTER to continue…{R}")

# ─── Export CSV ──────────────────────────────────────────────────────────────
def export_csv(db):
    header("EXPORT")
    incidents = db["incidents"]
    if not incidents:
        print(f"  {GREY}No incidents to export.{R}")
        input(f"  {GREY}Press ENTER…{R}")
        return

    fields = ["id","title","severity","status","category","assignee","source","created","updated","description"]
    with open(EXPORT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(incidents)

    print(f"  {GRN}{B}✔ Exported {len(incidents)} incidents to:{R}")
    print(f"  {CYN}{EXPORT_FILE}{R}")
    input(f"\n  {GREY}Press ENTER to continue…{R}")

# ─── Filter Menu ─────────────────────────────────────────────────────────────
def filter_menu(db):
    header("FILTER INCIDENTS")
    print(f"  {B}Filter by:{R}")
    choice = prompt("Choose filter", options=["By Status", "By Severity", "Show All", "Back"])
    if choice == "Back":
        return
    elif choice == "Show All":
        list_incidents(db)
    elif choice == "By Status":
        print(f"\n  {B}Select Status:{R}")
        status = prompt("Status", options=STATUSES)
        list_incidents(db, filter_status=status)
    elif choice == "By Severity":
        print(f"\n  {B}Select Severity:{R}")
        sev = prompt("Severity", options=SEVERITIES)
        list_incidents(db, filter_sev=sev)
    input(f"  {GREY}Press ENTER to continue…{R}")

# ─── Main Menu ───────────────────────────────────────────────────────────────
MENU_OPTIONS = [
    ("📊", "Dashboard"),
    ("📋", "List All Incidents"),
    ("➕", "New Incident"),
    ("🔍", "View Incident (by ID)"),
    ("✏️ ", "Update Incident"),
    ("🔎", "Search"),
    ("🗂️ ", "Filter Incidents"),
    ("📤", "Export to CSV"),
    ("🚪", "Exit"),
]

def main():
    db = load_db()
    while True:
        clear()
        divider("═", CYN)
        print(f"{B}{CYN}  🛡️  SOC L1 INCIDENT TRACKER  {GREY}·  {WHT}{now_str()}{R}")
        open_cnt = sum(1 for i in db["incidents"] if i["status"] not in ("RESOLVED","CLOSED"))
        crit_cnt = sum(1 for i in db["incidents"] if i["severity"] == "CRITICAL" and i["status"] not in ("RESOLVED","CLOSED"))
        print(f"  {GREY}DB: {DB_FILE}{R}   "
              f"Open: {B}{RED}{open_cnt}{R}   "
              f"Critical: {B}{BG_RED if crit_cnt else ''} {crit_cnt} {R}")
        divider("═", CYN)
        print()
        for idx, (icon, label) in enumerate(MENU_OPTIONS, 1):
            if label == "Exit":
                print(f"  {GREY}{idx}. {icon}  {label}{R}")
            elif label in ("New Incident",):
                print(f"  {GRN}{B}{idx}. {icon}  {label}{R}")
            elif label == "Dashboard":
                print(f"  {CYN}{B}{idx}. {icon}  {label}{R}")
            else:
                print(f"  {WHT}{idx}. {icon}  {label}{R}")
        print()

        choice = input(f"  {CYN}▶ Select option [1-{len(MENU_OPTIONS)}]{R}: ").strip()

        if not choice.isdigit() or not (1 <= int(choice) <= len(MENU_OPTIONS)):
            continue

        choice = int(choice)
        label = MENU_OPTIONS[choice - 1][1]

        db = load_db()  # Reload fresh on every action
        if label == "Dashboard":          show_dashboard(db)
        elif label == "List All Incidents": list_incidents(db)
        elif label == "New Incident":     add_incident(db)
        elif label == "View Incident (by ID)": view_incident(db)
        elif label == "Update Incident":  update_incident(db)
        elif label == "Search":           search_incidents(db)
        elif label == "Filter Incidents": filter_menu(db)
        elif label == "Export to CSV":    export_csv(db)
        elif label == "Exit":
            clear()
            print(f"\n  {CYN}{B}Stay safe out there. 🛡️{R}\n")
            sys.exit(0)

        if label in ("List All Incidents", "Dashboard"):
            input(f"  {GREY}Press ENTER to continue…{R}")

if __name__ == "__main__":
    main()

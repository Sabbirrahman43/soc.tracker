
# 1. Go to your folder
cd ~/tools/soc_tracker

# 2. Initialize git
git init

# 3. Add a .gitignore so your test data doesn't get committed
echo "soc_incidents.json" >> .gitignore
echo "soc_export.csv" >> .gitignore

# 4. Stage and commit
git add soc_tracker.py .gitignore
git commit -m "feat: SOC L1 incident tracker v1.0"

# 5. Create a new repo on GitHub (github.com → New Repository)
#    Name it something like: soc-incident-tracker
#    Set it Public or Private — your call

# 6. Link and push
git remote add origin https://github.com/YOUR_USERNAME/soc-incident-tracker.git
git branch -M main
git push -u origin main

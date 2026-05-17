# VPS Deployment

The FastAPI app lives at `content-automation-system/main.py` and is exposed to
Vercel, systemd, and Gunicorn through `api/index.py`.

## Why the VPS clone was empty

The parent repository currently tracks `content-automation-system` as a gitlink
(`160000`) instead of normal files, but there is no `.gitmodules` file telling
Git where that nested repository should come from. A normal clone therefore does
not receive the application files, leaving `content-automation-system` empty or
unusable on the VPS.

Fix this by committing `content-automation-system` as regular files in the parent
repository, or by converting it into a proper submodule with a real remote URL.
For this project, regular files are simpler.

## Convert nested repo to regular tracked files

Run these commands locally, then commit and push:

```bash
cd "/Users/macbook/Downloads/automation articles dashboard"

# Back up the nested repo metadata, then remove the broken gitlink from the
# parent index without deleting the working tree.
mv content-automation-system/.git content-automation-system/.git.backup
git rm --cached content-automation-system

# Stop tracking local virtualenv artifacts if they were committed earlier.
git rm -r --cached venv

# Add the real application files.
git add .gitignore requirements.txt api/index.py deployment content-automation-system
git status
git commit -m "Fix FastAPI deployment entrypoint and track app source"
git push
```

If you intentionally wanted `content-automation-system` to be a submodule, do
not use the commands above. Instead add a real submodule URL:

```bash
git submodule add <repo-url> content-automation-system
git commit -m "Configure content automation submodule"
git push
```

Then clone on the VPS with:

```bash
git clone --recurse-submodules <repo-url> /var/www/automation
```

## Ubuntu setup

Replace `your-domain.com` with the real domain.

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx git

sudo mkdir -p /var/www
sudo chown -R "$USER":"$USER" /var/www

cd /var/www
git clone <repo-url> automation
cd /var/www/automation

python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# Optional: create production env vars here.
nano .env
```

Smoke-test the import before enabling systemd:

```bash
cd /var/www/automation
venv/bin/python -c "from api.index import app; print(app.title)"
venv/bin/gunicorn api.index:app --worker-class uvicorn.workers.UvicornWorker --workers 2 --bind 127.0.0.1:8000 --timeout 120
```

In another SSH session:

```bash
curl -I http://127.0.0.1:8000
```

## systemd

```bash
sudo cp /var/www/automation/deployment/automation.service /etc/systemd/system/automation.service
sudo systemctl daemon-reload
sudo systemctl enable --now automation
sudo systemctl status automation --no-pager
journalctl -u automation -f
```

## nginx

```bash
sudo cp /var/www/automation/deployment/nginx-automation.conf /etc/nginx/sites-available/automation
sudo sed -i 's/example.com www.example.com/your-domain.com www.your-domain.com/' /etc/nginx/sites-available/automation
sudo ln -sf /etc/nginx/sites-available/automation /etc/nginx/sites-enabled/automation
sudo nginx -t
sudo systemctl reload nginx
```

## HTTPS

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## Useful checks

```bash
systemctl status automation --no-pager
journalctl -u automation -n 100 --no-pager
curl -I http://127.0.0.1:8000
curl -I http://your-domain.com
```

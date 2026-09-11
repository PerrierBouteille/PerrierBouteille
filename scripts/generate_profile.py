import yaml
import os

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def fetch_github_stats(username, token=None):
    import requests

    headers = {}

    if token:
        headers['Authorization'] = f'token {token}'
    stats = {}
    url = f'https://api.github.com/users/{username}'

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            stats['Public repos'] = data.get('public_repos', 0)
            stats['Followers'] = data.get('followers', 0)
            stats['Following'] = data.get('following', 0)
    except Exception:
        pass

    # Contributions via GraphQL
    try:
        # Try with token if available, else unauthenticated may still work for public data
        query = '''
        query($login:String!) {
          user(login:$login) {
            contributionsCollection {
              contributionCalendar { totalContributions }
            }
          }
        }
        '''

        r2 = requests.post(
            'https://api.github.com/graphql',
            json={'query': query, 'variables': {'login': username}},
            headers={**headers, 'Content-Type': 'application/json'},
            timeout=10
        )

        if r2.status_code == 200:
            js = r2.json()
            total = js.get('data', {}).get('user', {}).get('contributionsCollection', {}).get('contributionCalendar', {}).get('totalContributions', 0)
            stats['Contributions 1y'] = total if total else 0
        else:
            stats['Contributions 1y'] = 0
    except Exception:
        stats['Contributions 1y'] = 0
    return stats

def build_svg(username="PerrierBouteille", about="", socials=None, tech_stack=None, stats=None, dark=True):
    socials = socials or {}
    tech_stack = tech_stack or []
    stats = stats or {}

    bg = "#0b0e14" if dark else "#ffffff"
    panel_bg = "#0f1117" if dark else "#f7f7f7"
    text_color = "#d1d5db" if dark else "#1a1a1a"
    label_color = "#ff8c00" if dark else "#ea580c"
    value_color = "#22c55e" if dark else "#15803d"
    title_color = "#e5e7eb" if dark else "#111827"

    # Escape HTML
    def esc(s):
        return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    def linkify(text):
        import re
        escaped = esc(text).replace("\n","<br/>")
        # simple URL detection
        url_pat = re.compile(r'(https?://[^\s<]+)')
        def repl(m):
            url = m.group(1)
            return f"<a href='{esc(url)}' target='_blank' style='color:{value_color}; text-decoration:underline;'>{esc(url)}</a>"
        return url_pat.sub(repl, escaped)
    socials_html = "<br/>".join(f"{esc(k)}: <a href='{esc(v)}' target='_blank' style='color:{value_color}; text-decoration:underline;'>{esc(v)}</a>" for k,v in socials.items())

    # Tech stack can be list or dict of categories
    if isinstance(tech_stack, dict):
        tech_parts = []
        for cat, items in tech_stack.items():
            items_html = ", ".join(f"<span style='color:{value_color}'>{esc(i)}</span>" for i in items)
            tech_parts.append(f"<b style='color:{label_color}'>{esc(cat)}</b><br/><div style='margin-left:16px;'>{items_html}</div>")
        tech_html = "<br/>".join(tech_parts)
    else:
        tech_html = ", ".join(f"<span style='color:{value_color}'>{esc(t)}</span>" for t in tech_stack)
        
    stats_html = "<br/>".join(f"{esc(k)}: <span style='color:{value_color}'>{esc(v)}</span>" for k,v in stats.items())
    html = f"""
<div style="font-family: ui-monospace, SFMono-Regular, Menlo, monospace; color:{text_color}; background:{panel_bg}; padding:24px; border-radius:14px; line-height:1.5;">
<div style="color:{title_color}; font-size:20px; font-weight:700; margin-bottom:16px; border-bottom:1px solid #2a3345; padding-bottom:8px;">{esc(username)} — Profile</div>
<div><span style="color:{label_color}; font-weight:700;">About</span><br/>{linkify(about)}</div>
<div style="margin-top:18px;"><span style="color:{label_color}; font-weight:700;">Socials</span><br/>{socials_html}</div>
<div style="margin-top:18px;"><span style="color:{label_color}; font-weight:700;">Tech Stack</span><br/>{tech_html}</div>
<div style="margin-top:18px;"><span style="color:{label_color}; font-weight:700;">Stats</span><br/>{stats_html}</div>
</div>
"""
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="880" style="background:{bg}">
  <rect width="100%" height="100%" fill="{bg}"/>
  <foreignObject x="40" y="30" width="880" height="820">
    <div xmlns="http://www.w3.org/1999/xhtml" style="width:100%;height:100%;">{html}</div>
  </foreignObject>
</svg>'''
    return svg

if __name__ == "__main__":
    cfg_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    cfg = load_config(cfg_path)
    username = cfg.get('username', 'PerrierBouteille')
    token = os.environ.get('GITHUB_TOKEN')
    stats = fetch_github_stats(username, token)
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'images')
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'profile_dark.svg'), 'w', encoding='utf-8') as f:
        f.write(build_svg(username=username, about=cfg.get('about',''), socials=cfg.get('socials',{}), tech_stack=cfg.get('tech_stack',[]), stats=stats, dark=True))
    with open(os.path.join(out_dir, 'profile_light.svg'), 'w', encoding='utf-8') as f:
        f.write(build_svg(username=username, about=cfg.get('about',''), socials=cfg.get('socials',{}), tech_stack=cfg.get('tech_stack',[]), stats=stats, dark=False))

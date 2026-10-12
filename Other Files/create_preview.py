import json
from pathlib import Path

xml_path = Path("Other Files/architecture_diagram.drawio")
xml_content = xml_path.read_text(encoding="utf-8")

config = {
    "highlight": "#0000ff",
    "nav": True,
    "resize": True,
    "toolbar": "zoom",
    "xml": xml_content
}

html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Production Architecture Diagram</title>
</head>
<body style="background: #ffffff; margin: 0; padding: 20px;">
    <div id="debug" style="font-family:monospace; font-size:12px; max-height:200px; overflow:auto; background:#eee; padding:10px;"></div>
    <div class="mxgraph" style="max-width:100%; border:1px solid #cbd5e1;" data-mxgraph='{json.dumps(config)}'></div>
    <script>
        const logs = [];
        const origLog = console.log;
        const origWarn = console.warn;
        const origErr = console.error;
        console.log = (...args) => {{ logs.push('LOG: ' + args.join(' ')); origLog.apply(console, args); }};
        console.warn = (...args) => {{ logs.push('WARN: ' + args.join(' ')); origWarn.apply(console, args); }};
        console.error = (...args) => {{ logs.push('ERR: ' + args.join(' ')); origErr.apply(console, args); }};
        window.addEventListener('error', e => logs.push('WINDOW ERR: ' + e.message + ' at ' + e.filename + ':' + e.lineno));

        setTimeout(() => {{
            const svg = document.querySelector('svg');
            const logBox = document.getElementById('debug');
            logBox.innerHTML = '<b>Captured logs (' + logs.length + '):</b><br>' + logs.join('<br>') + '<br><br>';
            if (svg) {{
                const cells = Array.from(svg.querySelectorAll('*')).map(el => el.getAttribute('data-cell-id') || el.id).filter(Boolean);
                logBox.innerHTML += '<b>Found SVG cell ids:</b> ' + cells.join(', ');
            }}
        }}, 3000);
    </script>
    <script type="text/javascript" src="https://viewer.diagrams.net/js/viewer-static.min.js"></script>
</body>
</html>
"""

out_html = Path(r"C:\Users\Saketh\.gemini\antigravity-ide\brain\c9497478-e40f-4d5c-99f6-7917e8353905\scratch\preview.html")
out_html.write_text(html, encoding="utf-8")
print("Updated preview.html with full console interception")

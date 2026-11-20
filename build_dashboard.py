import json
t = open("dashboard/template.html").read(); d = json.load(open("dashboard/kpis.json"))
open("dashboard/index.html", "w").write(t.replace("__DATA__", json.dumps(d)))

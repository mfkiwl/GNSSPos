content = ""
with open("ppp_static_base.conf", 'r') as file:
    content = file.read()

diz = {}
for line in content.splitlines():
    if line.startswith("#") or not line.strip():
        continue
    key, value = line.split("=", 1)
    diz[key.strip()] = value.split('#')[0].strip()

for key, value in diz.items():
    print(f"'{key}': '{value}',")
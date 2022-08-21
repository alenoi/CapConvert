import plotly.graph_objects as go

belso = ["Logisztikai szolgáltatás",
         "Pénzügy, könyvelés, kontrolling, számlázás",
         "Adminisztráció, dokumentum menedzsment",
         "Döntéstámogatás és riporting (BI, adatgyűjtés és adatelemzés)",
         "Ügyfélszolgálat (Callcenter, CRM)",
         "Belső ügyvitel, workflow támogatás",
         "Telekommunikáció",
         "IT infrastruktúra",
         "Egyéb IT",
         "Adott szakterülethez tartozó folyamatok támogatása"]
kulso = ["Közlekedés, útdíj, parkolás",
         "Oktatás",
         "Egészségügy",
         "Állampolgári ügyintézés és nyilvántartások",
         "Vállalati ügyintézés és nyilvántartások",
         "Rendvédelem",
         "Hatósági Szolgáltatások",
         "Földnyilvántartás, közmű és építésügy",
         "Kormányzati beszerzés,működés és döntéstámogatás",
         "Igazságügy, jog",
         "Turizmus",
         "ICT",
         "Jóléti programok, segélyek",
         "Pályázatok, támogatások",
         "Adóügy",
         "Szolgáltatást nyújtó szervezet belső folyamatainak támogatása"]

labels = []
parents = []

parents.append("")
labels.append("Alkalmazások")

parents.append("Alkalmazások")
labels.append("Belső")
for idx, belso in enumerate(belso):
    parents.append("Belső")
    labels.append(belso)
    for idy, szolg in enumerate(range(int(idx % 3) + 1)):
        parents.append(belso)
        labels.append(f'Szolg {idy + 1}')
        # for idz, eir in enumerate(range(int(idy % 4) + int(idx % 3) + 1)):
        #     parents.append(f'Szolg {idy + 1}')
        #     labels.append(f'EIR {idz + 1}')

parents.append("Alkalmazások")
labels.append("Külső")
for idx, kulso in enumerate(kulso):
    parents.append("Külső")
    labels.append(kulso)
    for idy, szolg in enumerate(range(int(idx % 3) + 1)):
        parents.append(kulso)
        labels.append(f'Szolg {idy + 1}')
        # for idz, eir in enumerate(range((int(idy % 4) + int(idx % 3)) + 1)):
        #     parents.append(f'Szolg {idy + 1}')
        #     labels.append(f'EIR {idz + 1}')

for idx, x in enumerate(labels): print(f'{parents[idx]} - {x}')

fig = go.Figure(go.Treemap(
    labels=labels,
    parents=parents,
    root_color="lightgray"
))

fig.update_layout(
    treemapcolorway=["pink", "lightblue"],
    margin=dict(t=50, l=25, r=25, b=25)
)
fig.show()

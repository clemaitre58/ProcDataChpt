import pandas as pd
import re
from fpdf import FPDF

# ================== FONCTION DE NORMALISATION DES ACCENTS ==================
def remove_accents(text):
    if not isinstance(text, str):
        return text
    accents = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'à': 'a', 'â': 'a', 'ä': 'a',
        'î': 'i', 'ï': 'i',
        'ô': 'o', 'ö': 'o',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c',
        'É': 'E', 'È': 'E', 'Ê': 'E',
        'À': 'A', 'Â': 'A',
        'Î': 'I', 'Ï': 'I',
        'Ô': 'O', 'Ö': 'O',
        'Ù': 'U', 'Û': 'U', 'Ü': 'U',
        'Ç': 'C'
    }
    for acc, non_acc in accents.items():
        text = text.replace(acc, non_acc)
    return text


# ================== CHARGEMENT DES FICHIERS ==================
ins_path = './src/pixi_py/Ins_route.csv'
data_path = './src/pixi_py/Data.csv'

ins_route = pd.read_csv(ins_path, sep=',', encoding='utf-8')
data = pd.read_csv(data_path, sep=';', encoding='utf-8', low_memory=False)

# ================== NETTOYAGE & NORMALISATION ==================
ins_route['NOM'] = ins_route['NOM'].astype(str).str.strip().str.upper()
ins_route['Prénom'] = ins_route['Prénom'].astype(str).str.strip().str.title()
ins_route['clé'] = ins_route['NOM'] + ' ' + ins_route['Prénom']
ins_route['clé_norm'] = ins_route['clé'].apply(remove_accents)

data['Identité'] = data['Identité'].astype(str).str.strip()
data['clé_data'] = data['Identité'].str.replace(r'^71-', '', regex=True).str.strip().str.upper()
data['clé_data_norm'] = data['clé_data'].apply(remove_accents)

# Conversion numérique
cols_to_num = ['CHPT DPT route', 'ROUTE', 'CHPT DPT clm', 'CLM INDIV', 
               'CHPT DPT cyclo-cross', 'CYCLO-CROSS']

for col in cols_to_num:
    data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)

# ================== TRAITEMENT ==================
print("=== ASSOCIATIONS RÉPONDANT AUX CRITÈRES ===\n")
print("Critères : CHPT DPT route = 1  |  Total général >= 8  |  Route >= 4\n")

associations_ok = []
associations_ko = []
vus = set()

for idx, row in ins_route.iterrows():
    nom_complet = row['clé']
    if nom_complet in vus:
        continue
    vus.add(nom_complet)
    
    licence = row.get('Numéro de Licence', 'N/A')
    club = row.get('CLUB', 'N/A')
    
    matches = data[data['clé_data_norm'].str.contains(re.escape(row['clé_norm']), case=False, na=False)]
    
    if not matches.empty:
        match = matches.iloc[0]
        identite = match['Identité']
        
        chpt_route = match['CHPT DPT route']
        route = match['ROUTE']
        chpt_clm = match['CHPT DPT clm']
        clm_indiv = match['CLM INDIV']
        chpt_cx = match['CHPT DPT cyclo-cross']
        cx = match['CYCLO-CROSS']
        
        total_general = chpt_route + route + chpt_clm + clm_indiv + chpt_cx + cx
        total_route = chpt_route + route
        
        if (chpt_route == 1 and total_general >= 8 and total_route >= 4):
            associations_ok.append((nom_complet, identite, licence, club, 
                                  match.get('Total', 'N/A'), total_route, total_general))
            print(f"✓ {nom_complet:<35} → {identite} | Route: {int(total_route)} | Total: {int(total_general)}")
        else:
            associations_ko.append((nom_complet, identite, licence, club, 
                                  match.get('Total', 'N/A'), total_route, total_general, chpt_route))
    else:
        associations_ko.append((nom_complet, "NON TROUVÉ", licence, club, "N/A", "N/A", "N/A", "N/A"))

# ================== EXPORT PDF (version corrigée) ==================
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Rapport de Sélection - Coureurs Route', ln=True, align='C')
        self.ln(10)

    def section_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, title, ln=True)
        self.ln(5)

    def row(self, text):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 6, text)
        self.ln(2)


pdf = PDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)

# === Coureurs OK ===
pdf.section_title(f"Coureurs validés ({len(associations_ok)})")

for nom, identite, licence, club, total, route_pts, general_pts in associations_ok:
    ligne = f"OK  {nom} - {identite}\n" \
            f"    Licence : {licence} | Club : {club}\n" \
            f"    Points Route : {route_pts} | Total Général : {general_pts}"
    pdf.row(ligne)

# === Coureurs KO ===
pdf.add_page()
pdf.section_title(f"Coureurs ne validant pas les critères ({len(associations_ko)})")

for item in associations_ko:
    nom, identite, licence, club, total, route_pts, general_pts, chpt = item
    ligne = f"KO  {nom} - {identite}\n" \
            f"    Licence : {licence} | Club : {club}\n" \
            f"    Points Route : {route_pts} | Total Général : {general_pts} | CHPT Route : {chpt}"
    pdf.row(ligne)

# === Récapitulatif ===
pdf.add_page()
pdf.section_title("Récapitulatif")
pdf.row(f"- Coureurs répondant aux critères : {len(associations_ok)}")
pdf.row(f"- Coureurs ne répondant pas aux critères : {len(associations_ko)}")
pdf.row(f"- Total de coureurs traités : {len(associations_ok) + len(associations_ko)}")

pdf.output("Rapport_Selection_Coureurs.pdf")
print(f"\n✅ Rapport PDF généré avec succès : Rapport_Selection_Coureurs.pdf")

# ================== AFFICHAGE CONSOLE ==================
print(f"\nRécapitulatif :")
print(f"- Coureurs répondant aux critères : {len(associations_ok)}")
print(f"- Coureurs ne répondant pas aux critères : {len(associations_ko)}")
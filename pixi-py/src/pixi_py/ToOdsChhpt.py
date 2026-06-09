import pandas as pd
from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table, TableRow, TableCell
from odf.text import P
import os

# ================== CONFIGURATION ==================
input_csv = './src/pixi_py/DataFinales.csv'  # Change si nécessaire

categorie_mapping = {
    'Minime': 'Min_G',
    'Minime F': 'Min_F',
    'Cadet': 'Cad_G',
    'Cadet F': 'Cad_F',
    'Junior': 'Jun_H',
    'Junior F': 'Jun_F',           # Sera regroupé dans Fém
    'Espoir': 'Esp_H',
    # 'Espoir F': 'Esp_F',         # Sera regroupé
    'Senior': 'Sen_H',
    # 'Senior F': ...              # Sera regroupé
    'Vétéran': 'Vet_H',
    'Super-Vétéran': 'SV_H',
    'Ancien': 'Anc_H',
    'Super-Ancien': 'Sup_Anc_H',
}

# Catégories féminines à regrouper dans un seul onglet
femmes_categories = ['Junior F', 'Espoir F', 'Senior F', 'Vétéran F', 
                     'Super-Vétéran F', 'Ancien F', 'Super-Ancien F', 'Minime F', 'Cadet F']

# Mapping colonnes
column_mapping = {
    'Date de délivrance de la licence 2026': 'Date de délivrance *',
    'Numéro de Licence': 'N° licence FSGT 2026 *',
    'Date de naissance': 'Date de naissance *',
    'Multi-licencié ?': 'multi licencié oui / non *',
    'Catégorie Fédérale': 'catégorie',
    'Titre Route-2026': 'titre route 2026*',
    'Participations': 'Participations'
}
# ===================================================

# Lecture du CSV
df = pd.read_csv(input_csv, sep=';', encoding='utf-8')

# Création de la colonne Noms - Prénoms
df['Noms - Prénoms *'] = df['NOM'].astype(str).str.strip() + " " + df['Prénom'].astype(str).str.strip()

# Nettoyage
df['Catégorie Fédérale'] = df['Catégorie Fédérale'].str.strip()

# === Création du document ODS ===
doc = OpenDocumentSpreadsheet()

def add_sheet(doc, sheet_name, data_df):
    table = Table(name=sheet_name)
    
    # En-têtes
    header_row = TableRow()
    for col in data_df.columns:
        cell = TableCell()
        cell.addElement(P(text=col))
        header_row.addElement(cell)
    table.addElement(header_row)
    
    # Données
    for _, row in data_df.iterrows():
        data_row = TableRow()
        for value in row:
            cell = TableCell()
            cell.addElement(P(text=str(value) if pd.notna(value) else ""))
            data_row.addElement(cell)
        table.addElement(data_row)
    
    doc.spreadsheet.addElement(table)

# === Traitement des feuilles normales + feuille Femmes ===
processed = set()

# 1. Onglet Femmes regroupé
femmes_df = df[df['Catégorie Fédérale'].isin(femmes_categories)].copy()
if not femmes_df.empty:
    output_femmes = pd.DataFrame()
    for orig_col, new_col in column_mapping.items():
        if orig_col in femmes_df.columns:
            output_femmes[new_col] = femmes_df[orig_col]
    
    output_femmes['Noms - Prénoms *'] = femmes_df['Noms - Prénoms *']
    
    # Ordre des colonnes
    cols_order = [
        'Noms - Prénoms *', 'Date de délivrance *', 'N° licence FSGT 2026 *',
        'Date de naissance *', 'multi licencié oui / non *', 'catégorie',
        'titre route 2026*', 'Participations'
    ]
    output_femmes = output_femmes.reindex(columns=[c for c in cols_order if c in output_femmes.columns])
    
    add_sheet(doc, 'Fém_de_JàS-A', output_femmes)
    processed.update(femmes_df.index)

# 2. Onglets normaux (hommes + ceux non féminins)
for cat, sheet_name in categorie_mapping.items():
    group = df[df['Catégorie Fédérale'] == cat]
    if group.empty:
        continue
    
    output_df = pd.DataFrame()
    for orig_col, new_col in column_mapping.items():
        if orig_col in group.columns:
            output_df[new_col] = group[orig_col]
    
    output_df['Noms - Prénoms *'] = group['Noms - Prénoms *']
    
    cols_order = [
        'Noms - Prénoms *', 'Date de délivrance *', 'N° licence FSGT 2026 *',
        'Date de naissance *', 'multi licencié oui / non *', 'catégorie',
        'titre route 2026*', 'Participations'
    ]
    output_df = output_df.reindex(columns=[c for c in cols_order if c in output_df.columns])
    
    add_sheet(doc, sheet_name, output_df)

# Sauvegarde
output_file = 'route_ventilee.ods'
doc.save(output_file)

print(f"✅ Fichier '{output_file}' créé avec succès !")
print(f"• Onglet Femmes : Fém_de_JàS-A ({len(femmes_df)} lignes)")
print(f"• Onglets créés : {list(categorie_mapping.values())}")
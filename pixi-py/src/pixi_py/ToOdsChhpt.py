import pandas as pd
from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table, TableRow, TableCell
from odf.text import P

# ================== CONFIGURATION ==================
route_csv = './src/pixi_py/DataFinales.csv'          # Fichier principal Route
clm_csv   = './src/pixi_py/CLMInd.csv'         # Fichier CLM Individuel

categorie_mapping = {
    'Minime': 'Min_G',
    'Minime F': 'Min_F',
    'Cadet': 'Cad_G',
    'Cadet F': 'Cad_F',
    'Junior': 'Jun_H',
    # 'Junior F': 'Jun_F',
    'Espoir': 'Esp_H',
    'Senior': 'Sen_H',
    'Vétéran': 'Vet_H',
    'Super-Vétéran': 'SV_H',
    'Ancien': 'Anc_H',
    'Super-Ancien': 'Sup_Anc_H',
}

femmes_categories = ['Junior F', 'Espoir F', 'Senior F', 'Vétéran F', 
                     'Super-Vétéran F', 'Ancien F', 'Super-Ancien F']

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

def add_sheet(doc, sheet_name, data_df):
    table = Table(name=sheet_name)
    header_row = TableRow()
    for col in data_df.columns:
        cell = TableCell()
        cell.addElement(P(text=col))
        header_row.addElement(cell)
    table.addElement(header_row)

    for _, row in data_df.iterrows():
        data_row = TableRow()
        for value in row:
            cell = TableCell()
            cell.addElement(P(text=str(value) if pd.notna(value) else ""))
            data_row.addElement(cell)
        table.addElement(data_row)
    
    doc.spreadsheet.addElement(table)

# ====================== DOCUMENT ODS ======================
doc = OpenDocumentSpreadsheet()

# ====================== ROUTE ======================
df_route = pd.read_csv(route_csv, sep=';', encoding='utf-8')
df_route['Noms - Prénoms *'] = df_route['NOM'].astype(str).str.strip() + " " + df_route['Prénom'].astype(str).str.strip()
df_route['Catégorie Fédérale'] = df_route['Catégorie Fédérale'].str.strip()

cols_order_base = ['Date de délivrance *', 'N° licence FSGT 2026 *', 'Noms - Prénoms *',
                   'Date de naissance *', 'multi licencié oui / non *',
                   'titre route 2026*', 'Participations']

# 1. Onglet Femmes regroupé → avec colonne "catégorie"
femmes_df = df_route[df_route['Catégorie Fédérale'].isin(femmes_categories)].copy()
output_femmes = pd.DataFrame()
for orig, new in column_mapping.items():
    if orig in femmes_df.columns:
        output_femmes[new] = femmes_df[orig]
output_femmes['Noms - Prénoms *'] = femmes_df['Noms - Prénoms *']

output_femmes = output_femmes.reindex(columns=[
    'Date de délivrance *', 'N° licence FSGT 2026 *', 'Noms - Prénoms *',
    'Date de naissance *', 'multi licencié oui / non *', 'catégorie',
    'titre route 2026*', 'Participations'
])
add_sheet(doc, 'Fém_de_JàS-A', output_femmes)

# 2. Onglets individuels → SANS colonne "catégorie"
for cat, sheet_name in categorie_mapping.items():
    group = df_route[df_route['Catégorie Fédérale'] == cat].copy()
    output_df = pd.DataFrame()
    for orig, new in column_mapping.items():
        if orig in group.columns and new != 'catégorie':   # Exclut la colonne catégorie
            output_df[new] = group[orig]
    output_df['Noms - Prénoms *'] = group['Noms - Prénoms *']
    
    output_df = output_df.reindex(columns=cols_order_base)
    add_sheet(doc, sheet_name, output_df)

# ====================== CLM_Ind_ ======================
df_clm = pd.read_csv(clm_csv, sep=';', encoding='utf-8')
df_clm = df_clm.dropna(how='all')

df_clm['Catégorie Fédérale'] = df_clm['Catégorie Fédérale'].str.strip()
df_clm['Noms - Prénoms *'] = df_clm['NOM'].astype(str).str.strip() + " " + df_clm['Prénom'].astype(str).str.strip()

def get_genre(cat):
    if pd.isna(cat):
        return 'Homme'
    return 'Femme' if str(cat).strip().endswith((' F', 'F')) else 'Homme'

df_clm['Homme Femme'] = df_clm['Catégorie Fédérale'].apply(get_genre)

output_clm = pd.DataFrame()
for orig, new in column_mapping.items():
    if orig in df_clm.columns:
        output_clm[new] = df_clm[orig]

output_clm['Noms - Prénoms *'] = df_clm['Noms - Prénoms *']
output_clm['Homme Femme'] = df_clm['Homme Femme']

output_clm = output_clm.reindex(columns=[
    'Date de délivrance *', 'N° licence FSGT 2026 *', 'Noms - Prénoms *',
    'Date de naissance *', 'multi licencié oui / non *', 'catégorie',
    'titre route 2026*', 'Homme Femme', 'Participations'
])

add_sheet(doc, 'CLM_Ind_', output_clm)

# ====================== SAUVEGARDE ======================
output_file = 'Championnat_FSGT71_2026.ods'
doc.save(output_file)

print(f"✅ Fichier '{output_file}' créé avec succès !")
print("• Colonne 'catégorie' présente uniquement dans : Fém_de_JàS-A et CLM_Ind_")
print(f"• Total onglets : {len(categorie_mapping) + 2}")
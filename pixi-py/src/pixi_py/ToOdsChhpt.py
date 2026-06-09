import pandas as pd

# ================== CONFIGURATION ==================
input_csv = './src/pixi_py/DataFinales.csv'  # ou 'route.csv'

# Mapping Catégorie Fédérale → Nom de l'onglet
categorie_mapping = {
    'Minime': 'Min_G',
    'Minime F': 'Min_F',
    'Cadet': 'Cad_G',
    'Cadet F': 'Cad_F',
    'Junior': 'Jun_H',
    'Junior F': 'Jun_F',
    'Espoir': 'Esp_H',
    'Senior': 'Sen_H',
    'Vétéran': 'Vet_H',
    'Vétéran F': 'Vet_F',
    'Super-Vétéran': 'SV_H',
    'Super-Vétéran F': 'SV_F',
    'Ancien': 'Anc_H',
    'Super-Ancien': 'Sup_Anc_H',
}

# Mapping colonnes (fichier source → colonnes destination)
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

# Lecture du CSV (séparateur ;)
df = pd.read_csv(input_csv, sep=';', encoding='utf-8')

# Création de la colonne "Noms - Prénoms *"
df['Noms - Prénoms *'] = df['NOM'].astype(str).str.strip() + ' ' + df['Prénom'].astype(str).str.strip()

# Nettoyage et mapping des catégories
df['Catégorie Fédérale'] = df['Catégorie Fédérale'].str.strip()
df['sheet_name'] = df['Catégorie Fédérale'].map(categorie_mapping)

# Création du fichier Excel (compatible LibreOffice ODS)
writer = pd.ExcelWriter('route_ventilee.xlsx', engine='openpyxl')

for sheet_name, group in df.groupby('sheet_name'):
    if pd.isna(sheet_name):
        continue  # Ignorer les lignes sans catégorie mappée
    
    sheet_data = group.copy()
    
    # Construction du DataFrame final avec les bonnes colonnes
    output_df = pd.DataFrame()
    for orig_col, new_col in column_mapping.items():
        if orig_col in sheet_data.columns:
            output_df[new_col] = sheet_data[orig_col]
    
    output_df['Noms - Prénoms *'] = sheet_data['Noms - Prénoms *']
    
    # Ordre des colonnes
    cols_order = [
        'Noms - Prénoms *',
        'Date de délivrance *',
        'N° licence FSGT 2026 *',
        'Date de naissance *',
        'multi licencié oui / non *',
        'catégorie',
        'titre route 2026*',
        'Participations'
    ]
    output_df = output_df.reindex(columns=[c for c in cols_order if c in output_df.columns])
    
    # Écriture dans l'onglet
    output_df.to_excel(writer, sheet_name=sheet_name, index=False)

writer.close()

print("✅ Fichier 'route_ventilee.xlsx' créé avec succès !")
print("Onglets créés :", sorted([s for s in df['sheet_name'].unique() if pd.notna(s)]))
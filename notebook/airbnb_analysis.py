import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


listings = pd.read_csv(r"C:\Users\Alessandro D'Atria\Desktop\Github\Airbnb-Data-Analysis\data\listings.csv", compression='gzip')
reviews = pd.read_csv(r"C:\Users\Alessandro D'Atria\Desktop\Github\Airbnb-Data-Analysis\data\reviews.csv")

def clean_price(price_str):
    if isinstance(price_str, str):
        clean = price_str.replace('$', '').replace(',', '')
        return float(clean)
    return price_str

listings['price'] = listings['price'].apply(clean_price)


cols_to_numeric = ['review_scores_rating', 'number_of_reviews', 
                   'number_of_reviews_ltm', 'availability_365', 
                   'minimum_nights']

for col in cols_to_numeric:
    listings[col] = pd.to_numeric(listings[col], errors='coerce')

listings['occupancy_rate'] = (365 - listings['availability_365']) / 365 * 100

print("Dati caricati e puliti correttamente!")

HOST_ID_FRANCESCO = 329999601 
francesco_df = listings[listings['host_id'] == HOST_ID_FRANCESCO].copy()

# 2. Trova i Quartieri di Francesco
quartieri_francesco = francesco_df['neighbourhood_cleansed'].unique()

# 3. Crea il set dei Competitor
# Filtra: Stesso quartiere E stessa tipologia di stanza (es. Intera casa) per precisione
tipi_stanza = francesco_df['room_type'].unique()

competitors_df = listings[
    (listings['neighbourhood_cleansed'].isin(quartieri_francesco)) &
    (listings['room_type'].isin(tipi_stanza)) &
    (listings['host_id'] != HOST_ID_FRANCESCO) # Escludiamo Francesco dai competitor
].copy()

print(f"Trovati {len(francesco_df)} annunci per Francesco.")
print(f"Trovati {len(competitors_df)} annunci Competitor nella stessa zona.")

# Calcoliamo le medie
kpi_francesco = francesco_df[['price', 'review_scores_rating', 'number_of_reviews_ltm', 'occupancy_rate']].mean()
kpi_competitor = competitors_df[['price', 'review_scores_rating', 'number_of_reviews_ltm', 'occupancy_rate']].mean()

# Creiamo un DataFrame di confronto
confronto = pd.DataFrame({
    'Metrica': ['Prezzo Medio (€)', 'Rating (0-5)', 'Recensioni/Anno (Traffico)', 'Occupancy Rate (%)'],
    'Francesco': [kpi_francesco['price'], kpi_francesco['review_scores_rating'], kpi_francesco['number_of_reviews_ltm'], kpi_francesco['occupancy_rate']],
    'Competitor': [kpi_competitor['price'], kpi_competitor['review_scores_rating'], kpi_competitor['number_of_reviews_ltm'], kpi_competitor['occupancy_rate']]
})

# Calcolo Differenza %
confronto['Gap'] = confronto['Francesco'] - confronto['Competitor']

# Arrotondiamo per pulizia
confronto = confronto.round(2)

print("\n--- CONFRONTO KPI PRINCIPALI ---")
print(confronto)
# Lista dei servizi da cercare
target_amenities = ["Air conditioning", "Wifi", "Elevator", "Washer", 
                    "Iron", "Kitchen", "Dedicated workspace", "Coffee maker"]

results = []

for amenity in target_amenities:
    # Calcola % presenza per Francesco
    # case=False ignora maiuscole/minuscole
    f_pct = francesco_df['amenities'].str.contains(amenity, case=False, regex=False).mean() * 100
    
    # Calcola % presenza Competitor
    c_pct = competitors_df['amenities'].str.contains(amenity, case=False, regex=False).mean() * 100
    
    results.append({
        'Servizio': amenity,
        'Francesco_pct': f_pct,
        'Competitor_pct': c_pct,
        'Gap': f_pct - c_pct
    })

df_servizi = pd.DataFrame(results).sort_values(by='Gap', ascending=False).round(1)

print("\n--- ANALISI SERVIZI (VANTAGGI COMPETITIVI) ---")
print(df_servizi)

# Impostiamo lo stile
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Colori: Blu per Francesco, Grigio/Oro per Competitor
colors = {'Francesco': '#0073C2', 'Competitor': '#EFC000'}

# Dati per il grafico
plot_data = confronto[confronto['Metrica'].isin(['Prezzo Medio (€)', 'Rating (0-5)'])]
plot_data = plot_data.melt(id_vars="Metrica", var_name="Chi", value_name="Valore")
plot_data = plot_data[plot_data['Chi'] != 'Gap'] # Rimuoviamo la colonna Gap

# Plot 1: Prezzo
sns.barplot(x="Chi", y="Valore", data=plot_data[plot_data['Metrica']=='Prezzo Medio (€)'], 
            ax=axes[0], palette=colors)
axes[0].set_title("Prezzo Medio: Ti stai svendendo?", fontsize=14)
axes[0].set_ylabel("Euro (€)")

# Plot 2: Rating
sns.barplot(x="Chi", y="Valore", data=plot_data[plot_data['Metrica']=='Rating (0-5)'], 
            ax=axes[1], palette=colors)
axes[1].set_title("Qualità (Rating): Sei superiore", fontsize=14)
axes[1].set_ylim(4.0, 5.0) # Zoom sulla parte alta della scala

plt.tight_layout()
plt.savefig("output/1_Prezzo_Qualita_Python.png")
#plt.show()

plt.figure(figsize=(7, 6))

# Dati solo per le recensioni
traffic_data = confronto[confronto['Metrica'] == 'Recensioni/Anno (Traffico)']
traffic_data = traffic_data.melt(id_vars="Metrica", var_name="Chi", value_name="Reviews")
traffic_data = traffic_data[traffic_data['Chi'] != 'Gap']

ax = sns.barplot(x="Chi", y="Reviews", data=traffic_data, palette=colors)
ax.set_title("Traffico Reale (Ospiti Ultimi 12 Mesi)", fontsize=15, weight='bold')
ax.bar_label(ax.containers[0], fontsize=14, padding=3)

plt.ylabel("Numero Recensioni / Anno")
plt.savefig("output/2_Traffico_Reale_Python.png")
#plt.show()
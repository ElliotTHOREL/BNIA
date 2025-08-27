import streamlit as st
from streamlit_plotly_events import plotly_events
import plotly.express as px
import pandas as pd

# Données
df = pd.DataFrame({
    "x": [1, 2, 3, 4],
    "y": [10, 15, 13, 17],
    "label": ["A", "B", "C", "D"]
})

# Création du scatter avec taille visible
fig = px.scatter(
    df,
    x="x",
    y="y",
    text="label",
    size=[30, 30, 30, 30],  # Points bien visibles
    size_max=40
)
fig.update_traces(textposition="middle center")

# Affichage + détection de clics (ne PAS utiliser st.plotly_chart)
clicked = plotly_events(fig, click_event=True)

if clicked:
    st.write("Point cliqué :", clicked)
else:
    st.write("Cliquez sur un point pour voir les détails")
import streamlit as st
import json
from db import SessionLocal, init_db
from models import Club, Pricing, Payment
from utils import compute_club_total, get_price
from sqlalchemy.orm import Session

st.set_page_config(page_title="Pool Payments Manager", layout="wide")

init_db()

def get_session() -> Session:
    return SessionLocal()

st.title("Gestion des paiements - Clubs (Piscine)")

# Sidebar: gestion des prix (BDD)
st.sidebar.header("Base de données - Tarifs")
session = get_session()
# afficher ou initialiser les prix
def set_pricing(key, value):
    p = session.query(Pricing).filter_by(key=key).first()
    if p:
        p.value = float(value)
    else:
        p = Pricing(key=key, value=float(value))
        session.add(p)
    session.commit()

pb_current = get_price(session, "PB_price", 1200)
lane_current = get_price(session, "lane_price", 1200)
frais_current = get_price(session, "frais_prestation", 20000)

pb_new = st.sidebar.number_input("Prix PB (par jour)", value=float(pb_current))
lane_new = st.sidebar.number_input("Prix couloir (par unité)", value=float(lane_current))
frais_new = st.sidebar.number_input("Frais prestation (fixe)", value=float(frais_current))

if st.sidebar.button("Enregistrer tarifs"):
    set_pricing("PB_price", pb_new)
    set_pricing("lane_price", lane_new)
    set_pricing("frais_prestation", frais_new)
    st.sidebar.success("Tarifs enregistrés.")

# Page principale
menu = st.radio("Menu", ["Créer Club", "Liste Clubs", "Ajouter Paiement", "Dashboard"])

if menu == "Créer Club":
    st.header("Créer un club")
    name = st.text_input("Nom du club", "")
    st.markdown("Choisir le type par jour et le nombre de couloirs si besoin.")
    days = ["samedi","dimanche","lundi","mardi","mercredi","jeudi"]
    config = {}
    for d in days:
        st.subheader(d.capitalize())
        typ = st.selectbox(f"Type pour {d}", ["Aucun","PB","Couloir"], key=f"type_{d}")
        nb_lane = 0
        if typ == "Couloir":
            nb_lane = st.number_input(f"Nombre de couloirs pour {d}", min_value=0, step=1, key=f"lane_{d}")
        config[d] = {"type": typ if typ!="Aucun" else None, "nb_lane": int(nb_lane)}
    if st.button("Créer le club"):
        if name.strip() == "":
            st.error("Donne un nom pour le club.")
        else:
            s = session
            # sauvegarder
            club = Club(name=name.strip(), days_config=json.dumps(config))
            # calcul du total
            total = compute_club_total(s, json.dumps(config))
            club.total_initial = total
            s.add(club); s.commit()
            st.success(f"Club {name} créé. Total initial = {total:,.2f} DZD")

if menu == "Liste Clubs":
    st.header("Liste des clubs")
    clubs = session.query(Club).all()
    if not clubs:
        st.info("Aucun club pour le moment.")
    else:
        for c in clubs:
            st.markdown(f"### {c.name}")
            st.write("Total initial:", f"{c.total_initial:,.2f}")
            st.write("Total payé:", f"{c.total_paid:,.2f}")
            st.write("Reste:", f"{c.remaining:,.2f}")
            if st.expander("Détails et actions"):
                st.write("Configuration:", c.days_config)
                if st.button(f"Recalculer total - {c.id}"):
                    new_total = compute_club_total(session, c.days_config)
                    c.total_initial = new_total
                    session.commit()
                    st.success(f"Total recalculé = {new_total:,.2f}")

if menu == "Ajouter Paiement":
    st.header("Ajouter un paiement pour un club")
    clubs = session.query(Club).all()
    club_map = {f"{c.id} - {c.name}": c.id for c in clubs}
    choice = st.selectbox("Choisir club", options=[""] + list(club_map.keys()))
    amt = st.number_input("Montant payé", min_value=0.0, value=0.0)
    note = st.text_input("Note (optionnel)")
    if st.button("Enregistrer paiement"):
        if choice == "":
            st.error("Choisir un club")
        elif amt <= 0:
            st.error("Montant doit être > 0")
        else:
            club_id = club_map[choice]
            c = session.query(Club).get(club_id)
            pay = Payment(club_id=club_id, amount=amt, note=note)
            session.add(pay)
            # mettre à jour total_paid
            c.total_paid = (c.total_paid or 0.0) + amt
            session.commit()
            st.success(f"Paiement de {amt:,.2f} enregistré pour {c.name}. Reste = {c.remaining:,.2f}")

if menu == "Dashboard":
    st.header("Dashboard synthèse")
    clubs = session.query(Club).all()
    data = []
    for c in clubs:
        data.append({
            "Nom": c.name,
            "Initial": c.total_initial,
            "Payé": c.total_paid,
            "Reste": c.remaining
        })
    import pandas as pd
    df = pd.DataFrame(data)
    st.dataframe(df)
    if not df.empty:
        st.bar_chart(df.set_index("Nom")[["Initial","Payé","Reste"]])

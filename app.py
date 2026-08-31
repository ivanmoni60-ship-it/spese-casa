import datetime
import pandas as pd
import streamlit as st
from supabase import create_client

# Configurazione pagina
st.set_page_config(
    page_title="Gestione Spese di Casa", page_icon="🏠", layout="wide"
)

# Connessione sicura a Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Titolo App
st.title("🏠 Gestione Spese di Casa")

# 1. Filtro Anno
anni_disponibili = [2026, 2025, 2024]
anno_selezionato = st.selectbox("📅 Seleziona Anno:", anni_disponibili, index=0)

st.markdown("---")

# 2. Form di inserimento Nuova Spesa
with st.expander("➕ **Aggiungi Nuova Spesa**", expanded=False):
    with st.form("form_nuova_spesa", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            servizio = st.selectbox(
                "Servizio",
                [
                    "Iren Teleriscaldamento",
                    "Iren Luce",
                    "Iren Rifiuti",
                    "Condominio",
                ],
            )
            periodo = st.text_input(
                "Periodo", placeholder="es. Gennaio - Febbraio 2026"
            )

        with col2:
            costo_totale = st.number_input(
                "Costo Complessivo (€)", min_value=0.0, step=0.01, format="%.2f"
            )
            data_inserimento = st.date_input(
                "Data Inserimento", datetime.date.today(), format="DD/MM/YYYY"
            )

        submit = st.form_submit_button("Salva Spesa")

        if submit:
            if not periodo or costo_totale <= 0:
                st.error("Per favore compila tutti i campi correttamente.")
            else:
                quota_figlio = round(costo_totale * 0.25, 2)
                nuova_spesa = {
                    "anno": int(anno_selezionato),
                    "servizio": servizio,
                    "periodo": periodo,
                    "costo_totale": costo_totale,
                    "quota_figlio": quota_figlio,
                    "data_inserimento": str(data_inserimento),
                    "pagata": "N",
                }
                supabase.table("spese").insert(nuova_spesa).execute()
                st.success("Spesa aggiunta con successo!")
                st.rerun()

# 3. Lettura dati dal Database Cloud
res = (
    supabase.table("spese")
    .select("*")
    .eq("anno", anno_selezionato)
    .order("servizio", desc=False)
    .order("data_inserimento", desc=False)
    .execute()
)
spese_data = res.data

if not spese_data:
    st.info(f"Nessuna spesa registrata per l'anno {anno_selezionato}.")
else:
    st.subheader(f"📋 Elenco Spese {anno_selezionato}")

    # Intestazione Tabella
    col_serv, col_per, col_cost, col_quot, col_data, col_pag, col_del = (
        st.columns([2.5, 2.5, 1.5, 1.5, 1.5, 1.8, 1.2])
    )

    with col_serv:
        st.markdown("**Servizio**")
    with col_per:
        st.markdown("**Periodo**")
    with col_cost:
        st.markdown("**Totale**")
    with col_quot:
        st.markdown("**Quota 25%**")
    with col_data:
        st.markdown("**Data**")
    with col_pag:
        st.markdown("**Pagato S/N**")
    with col_del:
        st.markdown("**Elimina**")

    st.markdown("---")

    # Righe di dati compatte con popover di conferma
    for spesa in spese_data:
        col_serv, col_per, col_cost, col_quot, col_data, col_pag, col_del = (
            st.columns([2.5, 2.5, 1.5, 1.5, 1.5, 1.8, 1.2])
        )

        data_it = datetime.datetime.strptime(
            spesa["data_inserimento"], "%Y-%m-%d"
        ).strftime("%d/%m/%Y")
        stato_attuale = spesa["pagata"]

        with col_serv:
            st.write(spesa["servizio"])
        with col_per:
            st.write(spesa["periodo"])
        with col_cost:
            st.write(f"€ {spesa['costo_totale']:.2f}")
        with col_quot:
            st.write(f"€ {spesa['quota_figlio']:.2f}")
        with col_data:
            st.write(data_it)

        # 1. Popover di conferma cambio stato Pagato (S/N)
        with col_pag:
            testo_btn = "🟢 S" if stato_attuale == "S" else "🔴 N"
            nuovo_stato = "N" if stato_attuale == "S" else "S"
            label_conferma = (
                "Segnare come NON PAGATA?"
                if stato_attuale == "S"
                else "Segnare come PAGATA?"
            )

            with st.popover(testo_btn, use_container_width=True):
                st.write(label_conferma)
                if st.button("Conferma", key=f"conf_pag_{spesa['id']}"):
                    supabase.table("spese").update(
                        {"pagata": nuovo_stato}
                    ).eq("id", spesa["id"]).execute()
                    st.rerun()

        # 2. Popover di conferma cancellazione riga
        with col_del:
            with st.popover("🗑️", use_container_width=True):
                st.write("Eliminare questa spesa?")
                if st.button("Sì, elimina", key=f"conf_del_{spesa['id']}"):
                    supabase.table("spese").delete().eq(
                        "id", spesa["id"]
                    ).execute()
                    st.rerun()

    st.markdown("---")

    # 4. Calcolo Totali
    df = pd.DataFrame(spese_data)
    tot_complessivo = df["costo_totale"].sum()
    tot_figlio = df["quota_figlio"].sum()

    st.subheader("📊 Riepilogo Totali")
    col_t1, col_t2 = st.columns(2)
    col_t1.metric("Totale Complessivo Spese", f"€ {tot_complessivo:.2f}")
    col_t2.metric("Totale Quota Figlio (25%)", f"€ {tot_figlio:.2f}")

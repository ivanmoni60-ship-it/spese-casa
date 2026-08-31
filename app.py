import datetime
import pandas as pd
import streamlit as st
from st_supabase_connection import SupabaseConnection

# Configurazione pagina
st.set_page_config(
    page_title="Gestione Spese di Casa", page_icon="🏠", layout="wide"
)

# Connessione al Database Cloud
conn = st.connection("supabase", type=SupabaseConnection)

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
                conn.table("spese").insert(nuova_spesa).execute()
                st.success("Spesa aggiunta con successo!")
                st.rerun()

# 3. Lettura dati dal Database Cloud
res = (
    conn.table("spese")
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

    for spesa in spese_data:
        col_info, col_costi, col_stato = st.columns([3, 2, 2])

        data_it = datetime.datetime.strptime(
            spesa["data_inserimento"], "%Y-%m-%d"
        ).strftime("%d/%m/%Y")
        stato_attuale = spesa["pagata"]

        with col_info:
            st.markdown(f"**{spesa['servizio']}**")
            st.caption(f"Periodo: {spesa['periodo']} | Data: {data_it}")

        with col_costi:
            st.markdown(f"Totale: **€ {spesa['costo_totale']:.2f}**")
            st.caption(f"Quota Figlio (25%): **€ {spesa['quota_figlio']:.2f}**")

        with col_stato:
            colore_btn = (
                "🟢 PAGATO (S)" if stato_attuale == "S" else "🔴 DA PAGARE (N)"
            )
            if st.button(
                colore_btn, key=f"btn_{spesa['id']}", use_container_width=True
            ):
                nuovo_stato = "N" if stato_attuale == "S" else "S"
                conn.table("spese").update({"pagata": nuovo_stato}).eq(
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

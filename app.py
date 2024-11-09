import streamlit as st
import asyncio
from scrype import generate_pdf_from_indices
import base64

# Funkcja uruchamiająca generowanie PDF na podstawie indeksów
def run_pdf_generation(indices):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(generate_pdf_from_indices(indices))
    loop.close()
    return result

# Funkcja do wyświetlania pliku PDF
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'''
        <div style="display: flex; justify-content: center; align-items: center; height: 73vh;">
            <iframe src="data:application/pdf;base64,{base64_pdf}#toolbar=0&navpanes=0&scrollbar=0"
                    width="619"
                    height="850"
                    style="border: none;">
            </iframe>
        </div>
    '''
    st.markdown(pdf_display, unsafe_allow_html=True)

# Funkcja do inicjalizacji stanu sesji
def initialize_session():
    if "pdf_generated" not in st.session_state:
        st.session_state["pdf_generated"] = False
    if "is_generating" not in st.session_state:
        st.session_state["is_generating"] = False
    if "reset_app" not in st.session_state:
        st.session_state.reset_app = False

# Funkcja do resetowania stanu sesji
def reset_session_state():
    st.session_state["pdf_generated"] = False
    st.session_state["is_generating"] = False
    # Resetowanie pól tekstowych
    for i in range(1, 5):
        st.session_state[f"index{i}"] = ""

# Główna funkcja interfejsu użytkownika
def main():
    # Konfiguracja strony
    st.set_page_config(page_title="Mat-Poż - Generator etykiet", layout="wide", page_icon="mini.png")
    hide_streamlit_style = """
        <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            body { margin: 0; }
            .css-1v3fvcr { padding-top: 0; padding-bottom: 0; }
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # Inicjalizacja stanu sesji
    initialize_session()

    # Sprawdzenie flagi resetu na początku
    if st.session_state.reset_app:
        reset_session_state()
        st.session_state.reset_app = False
        st.empty()  # Czyszczenie interfejsu

    # Wstawienie logo i pól do wprowadzania indeksów do paska bocznego
    st.sidebar.image("logo.png", use_container_width=True)
    st.sidebar.title("Generator etykiet Mat-Poż")

    if not st.session_state["pdf_generated"]:
        st.sidebar.divider()
        st.sidebar.markdown(
            "<p style='color:red;'>Wprowadź od 1 do 4 indeksów produktów, aby wygenerować etykietę PDF.</p>",
            unsafe_allow_html=True)
        st.sidebar.divider()
        index1 = st.sidebar.text_input("Indeks produktu 1", key="index1")
        index2 = st.sidebar.text_input("Indeks produktu 2", key="index2")
        index3 = st.sidebar.text_input("Indeks produktu 3", key="index3")
        index4 = st.sidebar.text_input("Indeks produktu 4", key="index4")

    # Pojemnik na komunikaty i podgląd PDF
    message_area = st.empty()
    pdf_display_area = st.empty()

    # Wyświetlenie pustego PDF na początku
    if not st.session_state["pdf_generated"]:
        with pdf_display_area:
            show_pdf("blank.pdf")

    # Funkcja obsługująca kliknięcie przycisku generowania
    def handle_generate_pdf():
        indices = [idx for idx in [index1, index2, index3, index4] if idx]
        if indices:
            st.session_state["is_generating"] = True
            with message_area:
                with st.spinner("Trwa generowanie pliku PDF..."):
                    # Wywołaj generowanie pliku PDF
                    run_pdf_generation(indices)
            st.session_state["pdf_generated"] = True
            st.session_state["is_generating"] = False

    # Przycisk do generowania PDF lub komunikat o powodzeniu
    if not st.session_state["pdf_generated"]:
        # Przycisk do generowania PDF
        if st.sidebar.button("Generuj PDF", on_click=handle_generate_pdf):
            st.session_state["is_generating"] = True
    else:
        # Po wygenerowaniu PDF pokazuje komunikat o powodzeniu
        st.sidebar.success("✅ Plik został wygenerowany!")

        # Wyświetlenie wygenerowanego PDF
        with pdf_display_area:
            show_pdf("products.pdf")

        # Przycisk pobierania
        with open("products.pdf", "rb") as pdf_file:
            pdf_data = pdf_file.read()
            if st.sidebar.download_button(
                label="Pobierz wygenerowany PDF",
                data=pdf_data,
                file_name="products.pdf",
                mime="application/pdf"
            ):
                # Po pobraniu, ustawiamy flagę resetu
                st.session_state.reset_app = True
                st.rerun()

if __name__ == "__main__":
    main()
# RUN: python -m streamlit run app.py 
import streamlit as st
import transformers, re
transformers.logging.set_verbosity_error()

st.set_page_config(page_title="Aplikacja do anonimizacji plików tekstowych")
st.title("Aplikacja do anonimizacji plików tekstowych")

@st.cache_resource
def load_model():
    return transformers.pipeline(
        task="token-classification", 
        model="openai/privacy-filter",
        aggregation_strategy="simple"
    )


# Call the function to get the model
redactor = load_model()

def redact_string(input_text):
    results = redactor(input_text)
    
    mapping = {}
    counters = {}
    
    # Pre-calculate tags in forward order
    forward_results = sorted(results, key=lambda x: x['start'])
    for res in forward_results:
        label = res.get('entity_group', res.get('entity', 'REDACTED'))
        if label not in counters:
            counters[label] = 1
        else:
            counters[label] += 1
        res['tag'] = f"[{label}_{counters[label]}]"
        
    # Replace in reverse order
    sorted_results = sorted(forward_results, key=lambda x: x['start'], reverse=True)
    redacted_text = input_text
    
    for res in sorted_results:
        start = res['start']
        end = res['end']
        tag = res['tag']
        
        original_text = input_text[start:end]
        mapping[tag] = original_text
        
        redacted_text = redacted_text[:start] + tag + redacted_text[end:]
        
    return redacted_text, mapping

st.markdown("Wybierz metodę anonimizacji poufnych informacji:")

tab1, tab2 = st.tabs(["Wgranie pliku", "Zwykły tekst"])

with tab1:
    uploaded_file = st.file_uploader("Wgraj plik .txt", type=["txt"])

    if uploaded_file is not None:
        # Read the file content
        text = uploaded_file.read().decode("utf-8")
        
        st.subheader("Oryginalny tekst")
        st.text_area("Podgląd", text, height=150, disabled=True, key="preview_file")
        
        if st.button("Zanonimizuj dokument"):
            with st.spinner("Anonimizowanie..."):
                try:
                    redacted_text, mapping = redact_string(text)
                    
                    st.success("Anonimizacja zakończona!")
                    
                    st.subheader("Zanonimizowany tekst")
                    st.text_area("Wynik", redacted_text, height=150, disabled=True, key="result_file")
                    
                    st.subheader("Mapowanie deanonimizacji")
                    st.json(mapping)
                    
                    st.download_button(
                        label="Pobierz zanonimizowany plik",
                        data=redacted_text.encode("utf-8"),
                        file_name=f"redacted_{uploaded_file.name}",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"Wystąpił błąd podczas przetwarzania: {e}")

with tab2:
    st.markdown("Wklej lub wpisz zwykły tekst poniżej:")
    input_text = st.text_area("Tekst wejściowy", height=200, key="input_text")
    
    if st.button("Zanonimizuj tekst"):
        if input_text.strip():
            with st.spinner("Anonimizowanie..."):
                try:
                    redacted_text, mapping = redact_string(input_text)
                    st.success("Anonimizacja zakończona!")
                    
                    st.subheader("Zanonimizowany tekst")
                    st.text_area("Tekst wynikowy", redacted_text, height=200, disabled=True, key="result_text")
                    
                    st.subheader("Mapowanie deanonimizacji")
                    st.json(mapping)
                except Exception as e:
                    st.error(f"Wystąpił błąd podczas przetwarzania: {e}")
        else:
            st.warning("Wprowadź tekst do zanonimizowania.")

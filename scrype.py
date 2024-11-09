import csv
import requests
from bs4 import BeautifulSoup
import openai
import re
import asyncio
import json
from pdf import create_pdf_with_grid  # Import funkcji generującej PDF
import os
from dotenv import load_dotenv

load_dotenv()  # Wczytanie zmiennych z pliku .env
openai.api_key = os.getenv("OPENAI_API_KEY")

# Ścieżka do pliku tymczasowego JSON
temp_json_path = "temp_product_data.json"

# Funkcja do wczytywania URL z pliku CSV na podstawie indeksu
def get_url_from_csv(reference):
    file_path = url_list2.csv
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            if row['reference'] == reference:
                return row['Url'], row['Pic_url']
    return None, None

# Funkcja do pobierania danych o produkcie ze strony
def fetch_product_info(url):
    response = requests.get(url)
    html = response.content
    soup = BeautifulSoup(html, 'html.parser')

    try:
        product_name = soup.find('h1', class_='h1 product-detail-name').text.strip()
    except AttributeError:
        product_name = "Brak nazwy produktu"

    try:
        product_price = soup.find('div', class_='current-price').text.strip()
    except AttributeError:
        product_price = "Brak ceny"

    try:
        description = soup.find('div', class_='product-description').text.strip()
    except AttributeError:
        description = "Brak opisu produktu"

    # Pobieranie indexu z określonego elementu
    try:
        additional_info = soup.find('div', class_='product-additional-info')
        index_span = additional_info.find('span', string=re.compile(r'Index:'))
        index_value = index_span.text.split(':')[1].strip()
    except AttributeError:
        index_value = "Brak indeksu"

    # Pobieranie producenta
    try:
        producer_link = additional_info.find('a', href=True)
        producer_name = producer_link.text.strip()
    except AttributeError:
        producer_name = "Brak producenta"

    return product_name, product_price, description, producer_name, index_value

# Funkcja do skracania opisu przy użyciu API OpenAI
async def summarize_description(description, temperature=0.3):
    prompt = f"Proszę podsumuj poniższy opis produktu w zwięzły i logiczny sposób, nie przekraczając 47 słów. Odpowiedź wygeneruj w języku polskim:\n\n{description}"

    completion = await openai.ChatCompletion.acreate(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Jesteś asystentem, który skraca opisy produktów."},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature
    )

    summary = completion.choices[0].message['content'].strip()
    return summary

# Funkcja generująca PDF i JSON z listą indeksów
async def generate_pdf_from_indices(indices):
    products_data = []

    for reference in indices:
        url, pic_url = get_url_from_csv(reference)

        if url:
            name, price, description, producer, index = fetch_product_info(url)
            short_desc = await summarize_description(description)

            products_data.append({
                "name": name,
                "price": price,
                "description": description,
                "summary_description": short_desc,
                "producer": producer,
                "index": index,
                "image_url": pic_url,
                "product_url": url
            })
        else:
            print(f"Indeks '{reference}' nie został znaleziony w CSV.")

    if products_data:
        # Zapisz dane do JSON
        with open("temp_product_data.json", "w", encoding="utf-8") as f:
            json.dump(products_data, f, ensure_ascii=False, indent=4)

        # Utwórz plik PDF na podstawie danych
        create_pdf_with_grid(products_data)
        return "PDF utworzony jako 'products.pdf'. Plik JSON został zapisany jako 'temp_product_data.json'."
    else:
        return "Nie udało się znaleźć produktów dla podanych indeksów."

# Uruchomienie programu
if __name__ == "__main__":
    # Przykład użycia dla testu
    asyncio.run(generate_pdf_from_indices(["12345"]))  # Podaj przykładowy indeks

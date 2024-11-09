import json
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import requests
from PIL import Image
from io import BytesIO
import segno

# Funkcja do wczytywania danych z pliku JSON
def load_data_from_json(file_path):
    with open(file_path, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)
    return data

# Funkcja do rysowania linii przerywanej
def draw_dashed_line(pdf, x1, y1, x2, y2, dash_length=5, gap_length=3):
    if x1 == x2:  # linia pionowa
        y = y1
        while y < y2:
            pdf.line(x1, y, x1, min(y + dash_length, y2))
            y += dash_length + gap_length
    elif y1 == y2:  # linia pozioma
        x = x1
        while x < x2:
            pdf.line(x, y1, min(x + dash_length, x2), y1)
            x += dash_length + gap_length

# Funkcja do generowania QR kodu dla URL i zapisywania go do formatu PNG w BytesIO
def generate_qr_code(url):
    qr = segno.make(url)
    img_byte_arr = BytesIO()
    qr.save(img_byte_arr, kind="png", scale=2)
    img_byte_arr.seek(0)
    return img_byte_arr

# Funkcja tworząca plik PDF na podstawie danych z JSON
def create_pdf_with_grid(data):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()

    # Dodaj czcionkę Poppins-Regular obsługującą Unicode
    pdf.add_font("Poppins", "", "Poppins-Regular.ttf")
    pdf.add_font("Poppins-Bold", "", "Poppins-Bold.ttf")
    pdf.set_font("Poppins", size=12)

    # Ustawienia dla linii
    pdf.set_draw_color(128, 128, 128)
    pdf.set_line_width(0.1)

    # Rozmiar strony A4 w mm
    page_width = 210
    page_height = 297

    # Środek strony (poziomo i pionowo)
    mid_width = page_width / 2
    mid_height = page_height / 2
    line_margin = 5

    # Linie przerywane w pionie i poziomie
    draw_dashed_line(pdf, mid_width, 0, mid_width, page_height)
    draw_dashed_line(pdf, 0, mid_height, page_width, mid_height)

    # Dodanie logo w każdej ćwiartce z marginesem 4 mm
    logo_path = "logo.png"
    logo_width, logo_height = 30, 10
    quarter_width = page_width / 2
    line_length = quarter_width - 2 * line_margin

    # Funkcja pomocnicza do umieszczenia loga, czerwonej linii, zdjęcia i QR kodu
    def add_logo_and_line(x, y, product):
        # Pobieranie danych produktu
        product_name = product["name"]
        price = product["price"]
        description = product["summary_description"]
        producer = product["producer"]
        image_url = product["image_url"]
        product_url = product["product_url"]

        # Dodaj logo
        pdf.image(logo_path, x=x, y=y, w=logo_width, h=logo_height)
        pdf.set_margins(0, 0, 0)
        pdf.set_auto_page_break(auto=False)

        # Dodaj czerwoną linię
        pdf.set_draw_color(237, 0, 35)
        pdf.set_line_width(0.1)
        line_x_start = x + ((quarter_width - line_length) / 2) - 4
        line_y_position = y + logo_height + 2
        pdf.line(line_x_start, line_y_position, line_x_start + line_length, line_y_position)

        # Oblicz pozycję dla nazwy produktu, aby była wyśrodkowana między czerwoną linią a kodem QR
        qr_img = generate_qr_code(product_url)
        qr_x_position = line_x_start - 2.5
        qr_y_position = line_y_position + 20  # Górna krawędź kodu QR

        # Oblicz wysokość nazwy, zależnie od liczby wierszy tekstu
        name_max_width = line_length
        name_line_height = 6  # Wysokość pojedynczej linii tekstu
        name_text_lines = pdf.multi_cell(name_max_width, name_line_height, product_name, dry_run=True, output="LINES")
        name_text_height = name_line_height * len(name_text_lines)
        name_y_position = line_y_position + ((qr_y_position - line_y_position - name_text_height) / 2)

        # Wyświetl nazwę produktu
        pdf.set_font("Poppins-Bold", size=12)
        pdf.set_text_color(46, 74, 155)
        pdf.set_xy(line_x_start, name_y_position + 0.75)
        pdf.multi_cell(name_max_width, name_line_height, product_name, align="L")

        # Dodaj QR kod
        pdf.image(qr_img, x=qr_x_position, y=qr_y_position, w=35, h=35)

        # Wyświetl cenę
        pdf.set_font("Poppins", size=12)
        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(line_x_start, qr_y_position + 34)
        pdf.cell(line_length, 10, "Cena:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_xy(line_x_start, qr_y_position + 40)
        pdf.set_text_color(237, 0, 35)
        pdf.set_font("Poppins-Bold", size=18)
        pdf.cell(line_length, 10, price, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Wyświetl dodatkowe informacje
        pdf.set_font("Poppins", size=8)
        pdf.set_text_color(88, 88, 88)
        pdf.set_xy(line_x_start, qr_y_position + 45)
        pdf.cell(line_length, 10, f"Indeks: {product.get('index', '')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Dodaj obraz z URL, jeśli jest dostępny
        if image_url:
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            img_width, img_height = img.size
            img_ratio = img_height / img_width
            max_width = quarter_width / 2
            new_width = max_width
            new_height = new_width * img_ratio
            img_y_position = qr_y_position
            pdf.image(image_url, x=line_x_start + line_length - 2 - new_width, y=img_y_position, w=new_width,
                      h=new_height)

            # Opis produktu, poniżej zdjęcia
            pdf.set_font("Poppins", size=9.6)
            pdf.set_text_color(0, 0, 0)
            pdf.set_xy(line_x_start, img_y_position + new_height + 6)
            pdf.multi_cell(line_length, 6, f"     {description}", align="J")

        # Dodaj niebieską linię i producenta, jeśli producent istnieje
        if producer != "Brak producenta":
            blue_line_y_position = y + quarter_width + 30
            pdf.set_draw_color(46, 74, 155)
            pdf.line(line_x_start, blue_line_y_position, line_x_start + line_length, blue_line_y_position)

            # Etykieta "Producent:" w domyślnym kolorze
            pdf.set_font("Poppins", size=10)
            pdf.set_text_color(0, 0, 0)  # Ustaw kolor czarny dla etykiety
            pdf.set_xy(line_x_start, blue_line_y_position)
            pdf.cell(line_length, 6, "Producent: ", new_x=XPos.RIGHT, new_y=YPos.TOP)

            # Nazwa producenta w kolorze czerwonym
            pdf.set_text_color(237, 0, 35)  # Ustaw kolor czerwony dla nazwy producenta
            pdf.set_xy(line_x_start + 21, blue_line_y_position)
            pdf.cell(line_length, 6, producer, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Dodawanie danych do ćwiartek z pliku JSON
    for i, product in enumerate(data):
        if i == 0:
            add_logo_and_line(4, 4, product)
        elif i == 1:
            add_logo_and_line(mid_width + 4, 4, product)
        elif i == 2:
            add_logo_and_line(4, mid_height + 4, product)
        elif i == 3:
            add_logo_and_line(mid_width + 4, mid_height + 4, product)

    # Zapisz plik PDF
    pdf.output("products.pdf")
    print("PDF utworzony jako 'products.pdf'.")

# Ładowanie danych i generowanie PDF
data = load_data_from_json("temp_product_data.json")
create_pdf_with_grid(data)

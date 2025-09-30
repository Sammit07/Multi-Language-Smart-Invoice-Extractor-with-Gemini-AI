# 📄 Multi-Language Smart Invoice Extractor with Gemini AI  

The **Multi-Language Smart Invoice Extractor** is a Streamlit-based application powered by **Google Gemini AI**.  
It extracts structured data from invoice images in any language, automatically translates content to English, allows users to ask custom questions about the invoice, and exports results into multiple formats (TXT, JSON, CSV, Excel).

This project demonstrates the use of **multimodal AI**, **data parsing**, and **streamlined export workflows** for real-world document automation.  
<img width="1312" height="857" alt="image" src="https://github.com/user-attachments/assets/3fab013d-71db-4c6b-9a1e-fbdf8d5ea1cd" />

---

## 🚀 Features  

- 🌍 **Multi-Language Support**  
  - Handles invoices in any language (Hindi, Spanish, etc.)  
  - Automatically translates all text, names, and addresses into English  

- 📑 **Invoice Data Extraction**  
  - Extracts invoice details (number, date, due date, currency)  
  - Captures vendor and customer information  
  - Retrieves line items (description, quantity, unit price, total)  
  - Computes totals (subtotal, tax, grand total, payment terms)  

- ❓ **Two Modes of Operation**  
  - **Auto Extract** → Automatically extracts all invoice fields  
  - **Custom Question** → Ask specific questions about the invoice  

- 💾 **Export Options**  
  - TXT (human-readable text file)  
  - JSON (structured data for APIs)  
  - CSV (spreadsheet-ready flat format)  
  - Excel (multi-sheet export with summary & line items)  

- 🖼️ **Streamlit UI**  
  - Upload invoice images (JPG, JPEG, PNG)  
  - Real-time preview of extracted data  
  - Download results in chosen export format(s)  

---

## 📂 Project Structure  

```
├── app.py            # Main Streamlit application
├── .env                 # API key storage (not included in repo)
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

---

## ⚙️ Setup Instructions  

### 1️⃣ Clone the Repository  
```bash
git clone
```

### 2️⃣ Create Virtual Environment  
```bash
python -m venv venv
source venv/bin/activate   # For Linux/Mac
venv\Scripts\activate      # For Windows
```

### 3️⃣ Install Dependencies  
```bash
pip install -r requirements.txt
```

### 4️⃣ Configure API Key  
Create a **`.env`** file in the root folder:  

```
GEMINI_API_KEY=your_api_key_here
```

Get your API key from **Google AI Studio**.

### 5️⃣ Run the App  
```bash
streamlit run app.py
```

---

### Exported Formats  
- **CSV/Excel** → Rows of invoice data, including line items.  
- **JSON** → Structured dictionary with header, vendor, customer, and item details.  
- **TXT** → Readable report for human reference.  

---

## 🛠️ Technologies Used  

- **Python 3.9+**  
- **Google Gemini AI (`google-generativeai`)**  
- **Streamlit** (frontend)  
- **Pandas** (data handling)  
- **OpenPyXL** (Excel export)  
- **dotenv** (API key management)  
- **Pillow** (image handling)  

---

## 📌 Future Enhancements  

- 🧾 Support for **PDF invoices**  
- 🗂️ Bulk extraction (multiple invoices at once)  
- 🔒 Secure storage and masking of sensitive fields  
- 🧠 Fine-tuned extraction with domain-specific prompts  
- ☁️ Integration with **ERP / Accounting Systems**  

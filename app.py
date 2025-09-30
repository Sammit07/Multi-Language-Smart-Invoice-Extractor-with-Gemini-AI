import csv
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import google.generativeai as genai
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()

class InvoiceExtractor:
    def __init__(self, api_key):
        """Initialize the invoice extractor with Gemini API."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
    def extract_invoice_data(self, image, custom_prompt=None):
        """Extract structured data from an invoice image."""
        try:
            if custom_prompt:
                # Use custom prompt if provided
                prompt = custom_prompt
            else:
                # Default extraction prompt
                prompt = """
                Analyze this invoice image and extract the following information in a structured text format.
                
                IMPORTANT: 
                - Translate ALL text to English. If the invoice is in another language (Hindi, Spanish, etc.), translate names, addresses, and item descriptions to English.
                - For item descriptions, provide the English translation (e.g., "फोटो कॉपी पेपर" should be "Photo Copy Paper")
                - For proper names, you can transliterate them to English characters
                
                Format the output exactly as follows:
                
                ============================================================
                INVOICE DETAILS
                ============================================================
                
                Invoice Number: [invoice number]
                Invoice Date: [date in YYYY-MM-DD format]
                Due Date: [due date or N/A]
                Currency: [currency code like USD, EUR, INR]
                
                ------------------------------------------------------------
                VENDOR INFORMATION
                ------------------------------------------------------------
                Name: [vendor name in English or N/A]
                Address: [vendor address in English or N/A]
                Tax ID: [tax ID or N/A]
                
                ------------------------------------------------------------
                CUSTOMER INFORMATION
                ------------------------------------------------------------
                Name: [customer name transliterated to English]
                Address: [customer address translated to English]
                
                ------------------------------------------------------------
                LINE ITEMS
                ------------------------------------------------------------
                
                Item 1:
                  Description: [item description in English]
                  Quantity: [quantity]
                  Unit Price: [price]
                  Total: [total]
                
                Item 2:
                  Description: [item description in English]
                  Quantity: [quantity]
                  Unit Price: [price]
                  Total: [total]
                
                [Continue for all items...]
                
                ------------------------------------------------------------
                TOTALS
                ------------------------------------------------------------
                Subtotal: [subtotal amount]
                Tax Rate: [tax rate % or N/A]
                Tax Amount: [tax amount or N/A]
                Total Amount: [total amount]
                Payment Terms: [payment terms or N/A]
                
                ============================================================
                
                Return ONLY the formatted text above with the actual values filled in. Do not include any additional commentary.
                """
            
            response = self.model.generate_content([prompt, image])
            
            if custom_prompt:
                # Return raw response for custom prompts
                return response.text
            else:
                # Return formatted text for default extraction
                return response.text.strip()
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def parse_text_to_dict(self, text_data):
        """Parse formatted text back to dictionary for Excel/CSV export."""
        data = {
            'invoice_number': None,
            'invoice_date': None,
            'due_date': None,
            'currency': None,
            'vendor_name': None,
            'vendor_address': None,
            'vendor_tax_id': None,
            'customer_name': None,
            'customer_address': None,
            'items': [],
            'subtotal': None,
            'tax_rate': None,
            'tax_amount': None,
            'total_amount': None,
            'payment_terms': None
        }
        
        lines = text_data.split('\n')
        current_item = {}
        current_section = None
        
        for line in lines:
            line_stripped = line.strip()
            
            # Detect sections
            if 'VENDOR INFORMATION' in line_stripped:
                current_section = 'VENDOR'
                continue
            elif 'CUSTOMER INFORMATION' in line_stripped:
                current_section = 'CUSTOMER'
                continue
            elif 'LINE ITEMS' in line_stripped:
                current_section = 'ITEMS'
                continue
            elif 'TOTALS' in line_stripped:
                current_section = 'TOTALS'
                continue
            elif 'INVOICE DETAILS' in line_stripped:
                current_section = 'HEADER'
                continue
            
            if ':' in line_stripped:
                key, value = line_stripped.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Skip N/A values
                if value == 'N/A':
                    value = None
                
                # Parse based on current section
                if current_section == 'HEADER':
                    if key == 'Invoice Number':
                        data['invoice_number'] = value
                    elif key == 'Invoice Date':
                        data['invoice_date'] = value
                    elif key == 'Due Date':
                        data['due_date'] = value
                    elif key == 'Currency':
                        data['currency'] = value
                
                elif current_section == 'VENDOR':
                    if key == 'Name':
                        data['vendor_name'] = value
                    elif key == 'Address':
                        data['vendor_address'] = value
                    elif key == 'Tax ID':
                        data['vendor_tax_id'] = value
                
                elif current_section == 'CUSTOMER':
                    if key == 'Name':
                        data['customer_name'] = value
                    elif key == 'Address':
                        data['customer_address'] = value
                
                elif current_section == 'ITEMS':
                    if key == 'Description':
                        current_item['description'] = value
                    elif key == 'Quantity':
                        try:
                            current_item['quantity'] = float(value) if value else None
                        except:
                            current_item['quantity'] = value
                    elif key == 'Unit Price':
                        try:
                            current_item['unit_price'] = float(value) if value else None
                        except:
                            current_item['unit_price'] = value
                    elif key == 'Total':
                        try:
                            current_item['total'] = float(value) if value else None
                        except:
                            current_item['total'] = value
                        # Save item when we get the total
                        if current_item:
                            data['items'].append(current_item.copy())
                            current_item = {}
                
                elif current_section == 'TOTALS':
                    if key == 'Subtotal':
                        try:
                            data['subtotal'] = float(value) if value else None
                        except:
                            data['subtotal'] = value
                    elif key == 'Tax Rate':
                        data['tax_rate'] = value
                    elif key == 'Tax Amount':
                        try:
                            data['tax_amount'] = float(value) if value else None
                        except:
                            data['tax_amount'] = value
                    elif key == 'Total Amount':
                        try:
                            data['total_amount'] = float(value) if value else None
                        except:
                            data['total_amount'] = value
                    elif key == 'Payment Terms':
                        data['payment_terms'] = value
        
        return data


    def export_to_csv(self, text_data, output_path):
        """Export text data to CSV format."""
        try:
            data = self.parse_text_to_dict(text_data)
            
            # Flatten data for CSV
            rows = []
            base_row = {
                'invoice_number': data.get('invoice_number'),
                'invoice_date': data.get('invoice_date'),
                'due_date': data.get('due_date'),
                'vendor_name': data.get('vendor_name'),
                'customer_name': data.get('customer_name'),
                'subtotal': data.get('subtotal'),
                'tax_amount': data.get('tax_amount'),
                'total_amount': data.get('total_amount'),
                'currency': data.get('currency'),
            }
            
            items = data.get('items', [])
            if items:
                for item in items:
                    row = base_row.copy()
                    row.update({
                        'item_description': item.get('description'),
                        'quantity': item.get('quantity'),
                        'unit_price': item.get('unit_price'),
                        'item_total': item.get('total')
                    })
                    rows.append(row)
            else:
                rows.append(base_row)
            
            df = pd.DataFrame(rows)
            df.to_csv(output_path, index=False)
            return output_path
        except Exception as e:
            print(f"Error in export_to_csv: {str(e)}")
            raise
    
    def export_to_json(self, text_data, output_path):
        """Export text data to JSON format."""
        try:
            data = self.parse_text_to_dict(text_data)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return output_path
        except Exception as e:
            print(f"Error in export_to_json: {str(e)}")
            raise
    
    def export_to_excel(self, text_data, output_path):
        """Export text data to Excel format."""
        try:
            data = self.parse_text_to_dict(text_data)
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = [{
                    'Invoice Number': data.get('invoice_number'),
                    'Date': data.get('invoice_date'),
                    'Vendor': data.get('vendor_name'),
                    'Customer': data.get('customer_name'),
                    'Total Amount': data.get('total_amount'),
                    'Currency': data.get('currency')
                }]
                
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Summary', index=False)
                
                # Line items sheet
                items = data.get('items', [])
                if items:
                    line_items = []
                    for item in items:
                        line_items.append({
                            'Description': item.get('description'),
                            'Quantity': item.get('quantity'),
                            'Unit Price': item.get('unit_price'),
                            'Total': item.get('total')
                        })
                    
                    df_items = pd.DataFrame(line_items)
                    df_items.to_excel(writer, sheet_name='Line Items', index=False)
            
            return output_path
        except Exception as e:
            print(f"Error in export_to_excel: {str(e)}")
            raise
    
    def export_to_txt(self, invoice_data, output_path):
        """Export invoice data to TXT format."""
        if not invoice_data or isinstance(invoice_data, str):
            st.error("No valid data to export")
            return
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("INVOICE DETAILS\n")
            f.write("=" * 60 + "\n\n")
            
            # Invoice Information
            f.write(f"Invoice Number: {invoice_data.get('invoice_number', 'N/A')}\n")
            f.write(f"Invoice Date: {invoice_data.get('invoice_date', 'N/A')}\n")
            f.write(f"Due Date: {invoice_data.get('due_date', 'N/A')}\n")
            f.write(f"Currency: {invoice_data.get('currency', 'N/A')}\n")
            f.write(f"Extracted At: {invoice_data.get('extracted_at', 'N/A')}\n")
            
            f.write("\n" + "-" * 60 + "\n")
            f.write("VENDOR INFORMATION\n")
            f.write("-" * 60 + "\n")
            f.write(f"Name: {invoice_data.get('vendor_name', 'N/A')}\n")
            f.write(f"Address: {invoice_data.get('vendor_address', 'N/A')}\n")
            f.write(f"Tax ID: {invoice_data.get('vendor_tax_id', 'N/A')}\n")
            
            f.write("\n" + "-" * 60 + "\n")
            f.write("CUSTOMER INFORMATION\n")
            f.write("-" * 60 + "\n")
            f.write(f"Name: {invoice_data.get('customer_name', 'N/A')}\n")
            f.write(f"Address: {invoice_data.get('customer_address', 'N/A')}\n")
            
            f.write("\n" + "-" * 60 + "\n")
            f.write("LINE ITEMS\n")
            f.write("-" * 60 + "\n\n")
            
            items = invoice_data.get('items', [])
            if items:
                for idx, item in enumerate(items, 1):
                    f.write(f"Item {idx}:\n")
                    f.write(f"  Description: {item.get('description', 'N/A')}\n")
                    f.write(f"  Quantity: {item.get('quantity', 'N/A')}\n")
                    f.write(f"  Unit Price: {item.get('unit_price', 'N/A')}\n")
                    f.write(f"  Total: {item.get('total', 'N/A')}\n\n")
            else:
                f.write("No items found\n\n")
            
            f.write("-" * 60 + "\n")
            f.write("TOTALS\n")
            f.write("-" * 60 + "\n")
            f.write(f"Subtotal: {invoice_data.get('subtotal', 'N/A')}\n")
            f.write(f"Tax Rate: {invoice_data.get('tax_rate', 'N/A')}\n")
            f.write(f"Tax Amount: {invoice_data.get('tax_amount', 'N/A')}\n")
            f.write(f"Total Amount: {invoice_data.get('total_amount', 'N/A')}\n")
            
            if invoice_data.get('payment_terms'):
                f.write(f"\nPayment Terms: {invoice_data.get('payment_terms')}\n")
            
            f.write("\n" + "=" * 60 + "\n")
        
        return output_path


def main():
    """Streamlit app for invoice extraction."""
    st.set_page_config(page_title="Invoice Extractor", page_icon="📄", layout="wide")
    
    st.title("📄 Multi-Language Smart Invoice Extractor with Gemini AI")
    st.markdown("Upload invoice images and extract structured data or ask custom questions")
    
    # Load API key from .env
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        st.error("⚠️ GEMINI_API_KEY not found in .env file!")
        st.info("Please create a .env file with: GEMINI_API_KEY=your_api_key_here")
        return
    
    # Initialize extractor
    extractor = InvoiceExtractor(api_key)
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        mode = st.radio(
            "Select Mode:",
            ["Auto Extract", "Custom Question"],
            help="Auto Extract: Extract all invoice data | Custom Question: Ask specific questions"
        )
        
        st.markdown("---")
        st.markdown("### 📊 Export Options")
        export_format = st.multiselect(
            "Choose export formats:",
            ["TXT", "JSON", "CSV", "Excel"],
            default=["TXT"]
        )
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📤 Upload Invoice")
        uploaded_file = st.file_uploader(
            "Choose an image...",
            type=['jpg', 'jpeg', 'png'],
            help="Drag and drop file here. Limit 200MB per file • JPG, JPEG, PNG"
        )
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Invoice", use_container_width=True)
        
        # Input prompt
        if mode == "Custom Question":
            user_prompt = st.text_area(
                "Input Prompt:",
                placeholder="Tell me about the image",
                help="Ask any question about the invoice"
            )
        else:
            user_prompt = None
            st.info("Auto-extraction mode: All invoice data will be extracted automatically")
        
        # Extract button
        extract_button = st.button("🚀 Extract Data", type="primary", use_container_width=True)
    
    with col2:
        st.subheader("📋 Extracted Data")
        
        if extract_button and uploaded_file:
            with st.spinner("Analyzing invoice..."):
                if mode == "Custom Question" and user_prompt:
                    result = extractor.extract_invoice_data(image, user_prompt)
                    st.markdown("### Answer:")
                    st.write(result)
                else:
                    result = extractor.extract_invoice_data(image)
                    
                    if isinstance(result, str):
                        # Display the formatted text directly
                        st.text(result)
                        
                        # Store result in session state for export
                        st.session_state['last_result'] = result
                        
                        # Export options
                        if export_format:
                            st.markdown("---")
                            st.markdown("### 💾 Export Data")
                            
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            temp_dir = tempfile.gettempdir()
                            
                            for fmt in export_format:
                                if fmt == "TXT":
                                    txt_file = os.path.join(temp_dir, f"invoice_{timestamp}.txt")
                                    with open(txt_file, 'w', encoding='utf-8') as f:
                                        f.write(result)
                                    
                                    with open(txt_file, 'rb') as f:
                                        st.download_button(
                                            "📥 Download TXT",
                                            f.read(),
                                            f"invoice_{timestamp}.txt",
                                            "text/plain",
                                            use_container_width=True
                                        )
                                
                                elif fmt == "JSON":
                                    json_file = os.path.join(temp_dir, f"invoice_{timestamp}.json")
                                    extractor.export_to_json(result, json_file)
                                    with open(json_file, 'rb') as f:
                                        st.download_button(
                                            "📥 Download JSON",
                                            f.read(),
                                            f"invoice_{timestamp}.json",
                                            "application/json",
                                            use_container_width=True
                                        )
                                
                                elif fmt == "CSV":
                                    csv_file = os.path.join(temp_dir, f"invoice_{timestamp}.csv")
                                    extractor.export_to_csv(result, csv_file)
                                    with open(csv_file, 'rb') as f:
                                        st.download_button(
                                            "📥 Download CSV",
                                            f.read(),
                                            f"invoice_{timestamp}.csv",
                                            "text/csv",
                                            use_container_width=True
                                        )
                                
                                elif fmt == "Excel":
                                    excel_file = os.path.join(temp_dir, f"invoice_{timestamp}.xlsx")
                                    extractor.export_to_excel(result, excel_file)
                                    with open(excel_file, 'rb') as f:
                                        st.download_button(
                                            "📥 Download Excel",
                                            f.read(),
                                            f"invoice_{timestamp}.xlsx",
                                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                            use_container_width=True
                                        )

                    
                    else:
                        st.error(result)
        
        elif extract_button and not uploaded_file:
            st.warning("⚠️ Please upload an invoice image first!")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
            Built with Streamlit and Google Gemini AI
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
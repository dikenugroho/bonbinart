import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import os
from PIL import Image

# ========== KONFIGURASI ==========
DATA_PATH = "data/data_master.xlsx"
IMAGE_FOLDER = "data/images/"
PLACEHOLDER_IMAGE = "https://via.placeholder.com/100"

# ========== FUNGSI BANTU ==========
def load_data():
    """Memuat dan membersihkan data produk"""
    try:
        df = pd.read_excel(DATA_PATH)
        df["Kode"] = df["Kode"].fillna("").astype(str).str.strip()
        df["Harga"] = pd.to_numeric(df["Harga"], errors="coerce")
        df["MOQ"] = pd.to_numeric(df["MOQ"], errors="coerce").fillna(1).astype(int)
        return df
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return pd.DataFrame()

def display_product_card(row):
    """Menampilkan card produk"""
    cols = st.columns([1, 2, 1])
    
    # Kolom 1: Gambar produk
    with cols[0]:
        img_path = os.path.join(IMAGE_FOLDER, f"{row['Kode']}.jpg")
        if os.path.exists(img_path):
            try:
                img = Image.open(img_path)
                st.image(img, width=200)
            except:
                st.image(PLACEHOLDER_IMAGE, width=200)
        else:
            st.image(PLACEHOLDER_IMAGE, width=200)
    
    # Kolom 2: Info produk
    with cols[1]:
        st.subheader(row["Nama Produk"])
        st.markdown(f"**💰 Harga:** Rp {row['Harga']:,}")
        st.markdown(f"**📦 MOQ:** {row['MOQ']} pcs")
        
        # Tampilkan info tambahan jika ada
        if "Deskripsi" in row and pd.notna(row["Deskripsi"]):
            with st.expander("ℹ️ Deskripsi"):
                st.write(row["Deskripsi"])
    
    # Kolom 3: Tombol tambah ke keranjang
    with cols[2]:
        if st.button( 
            f"➕ Tambah", 
            key=f"add_{row['No']}",
            help=f"Tambahkan {row['Nama Produk']} ke keranjang"
        ):
            add_to_cart(row)

def add_to_cart(product):
    """Menambahkan produk ke keranjang"""
    if "cart" not in st.session_state:
        st.session_state.cart = []
    
    # Cek apakah produk sudah ada di keranjang
    existing_item = next((item for item in st.session_state.cart 
                        if item["No"] == product["No"]), None)
    
    if existing_item:
        existing_item["quantity"] += 1
    else:
        new_item = product.to_dict()
        new_item["quantity"] = 1
        st.session_state.cart.append(new_item)
    
    st.success(f"✓ Ditambahkan: {product['Nama Produk']}")
    st.rerun()

def remove_from_cart(index):
    """Menghapus item dari keranjang"""
    st.session_state.cart.pop(index)
    st.rerun()

def display_cart():
    """Menampilkan keranjang belanja"""
    st.subheader("🛒 Keranjang Belanja")
    
    if not st.session_state.get("cart"):
        st.info("Keranjang masih kosong")
        return
    
    cart_df = pd.DataFrame(st.session_state.cart)
    
    # Hitung total per item
    cart_df["Subtotal"] = cart_df["Harga"] * cart_df["quantity"]
    
    # Tampilkan tabel
    for i, item in enumerate(st.session_state.cart):
        cols = st.columns([3, 2, 2, 2, 1, 1])
        with cols[0]:
            st.markdown(f"**{item['Nama Produk']}**")
        with cols[1]:
            st.markdown(f"Rp {item['Harga']:,}")
        with cols[2]:
            st.markdown(f"{item['quantity']} pcs")
        with cols[3]:
            subtotal = item['Harga'] * item['quantity']
            st.markdown(f"Rp {subtotal:,}")
        with cols[4]:
            if st.button("➖", key=f"decrease_{i}", help="Kurangi jumlah"):
                if item["quantity"] > 1:
                    st.session_state.cart[i]["quantity"] -= 1
                else:
                    remove_from_cart(i)  # Jika tinggal 1, langsung hapus
                st.rerun()
        with cols[5]:
            if st.button("🗑️", key=f"delete_{i}", help="Hapus produk dari keranjang"):
                remove_from_cart(i)
                st.stop()


    
    # Hitung total belanja
    # Hitung total belanja
    total = sum(item["Harga"] * item["quantity"] for item in st.session_state.cart)
    st.metric("**Total Belanja**", f"Rp {total:,}")

    # Tombol aksi
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Kosongkan Keranjang", type="primary"):
            st.session_state.cart = []
            st.rerun()

    with col2:
        checkout()


def checkout():
    """Proses checkout"""
    if st.button("💳 Checkout", type="secondary"):
        if not st.session_state.cart:
            st.warning("Keranjang masih kosong!")
            return
        
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = BytesIO()
        
        # Buat DataFrame dari keranjang
        cart_df = pd.DataFrame(st.session_state.cart)
        cart_df["Subtotal"] = cart_df["Harga"] * cart_df["quantity"]

        # Susun ulang dan format kolom untuk invoice
        invoice_df = cart_df[["Nama Produk", "Harga", "quantity", "Subtotal"]].copy()
        invoice_df.insert(0, "No", range(1, len(invoice_df) + 1))
        invoice_df.columns = ["No", "Nama Produk", "Harga (Rp)", "Jumlah", "Subtotal (Rp)"]

        # Tambahkan total
        total_belanja = invoice_df["Subtotal (Rp)"].sum()
        total_row = pd.DataFrame([["", "Total", "", "", total_belanja]], columns=invoice_df.columns)
        invoice_df = pd.concat([invoice_df, total_row], ignore_index=True)

        # Simpan ke Excel dengan styling sederhana
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            invoice_df.to_excel(writer, index=False, sheet_name="Invoice")

            # Format worksheet
            workbook  = writer.book
            worksheet = writer.sheets["Invoice"]
            currency_fmt = workbook.add_format({'num_format': 'Rp #,##0'})
            bold_fmt = workbook.add_format({'bold': True})

            # Lebar kolom
            worksheet.set_column("A:A", 5)
            worksheet.set_column("B:B", 30)
            worksheet.set_column("C:C", 15, currency_fmt)
            worksheet.set_column("D:D", 10)
            worksheet.set_column("E:E", 20, currency_fmt)

            # Format header
            for col_num, value in enumerate(invoice_df.columns.values):
                worksheet.write(0, col_num, value)

            # Tambah border, dan highlight baris total
            worksheet.set_row(len(invoice_df) - 1, None)

        # Tombol download
        st.download_button(
            label="⬇️ Download Invoice (Excel)",
            data=output.getvalue(),
            file_name=f"invoice_mbakdike_{now}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.balloons()
        st.success("Pesanan berhasil diproses! Terima kasih telah berbelanja")


# ========== TAMPILAN UTAMA ==========
def main():
    """Tampilan utama aplikasi"""
    st.set_page_config(
        page_title="Toko Online Mbak Dike",
        page_icon="🛍️",
        layout="wide"
    )
    
    # Header
    st.title("🛍️ Toko Online Mbak Dike")
    st.markdown("---")
    
    # Load data
    df = load_data()
    if df.empty:
        return
    
    # Sidebar - Filter
    with st.sidebar:
        st.header("🔍 Filter Produk")
        search_query = st.text_input("Cari produk...")
        
        if "Kategori" in df.columns:
            categories = ["Semua"] + sorted(df["Kategori"].dropna().unique().tolist())
            selected_category = st.selectbox("Kategori", categories)
        
        st.markdown("---")
        st.header("🛒 Keranjang")
        if st.session_state.get("cart"):
            total_items = sum(item["quantity"] for item in st.session_state.cart)
            st.metric("Total Item", total_items)
        else:
            st.write("Belum ada item")
    
    # Filter data
    filtered_df = df.copy()
    
    if search_query:
        filtered_df = filtered_df[
            filtered_df["Nama Produk"].str.contains(search_query, case=False, na=False)
        ]
    
    if "selected_category" in locals() and selected_category != "Semua":
        filtered_df = filtered_df[filtered_df["Kategori"] == selected_category]
    
    # Tampilkan produk
    st.subheader(f"📦 Daftar Produk ({len(filtered_df)} item)")
    
    if filtered_df.empty:
        st.warning("Tidak ada produk yang sesuai dengan filter")
    else:
        for _, row in filtered_df.iterrows():
            with st.container(border=True):
                display_product_card(row)
    
    # Tampilkan keranjang
    st.markdown("---")
    display_cart()

if __name__ == "__main__":
    if "cart" not in st.session_state:
        st.session_state.cart = []
    main()
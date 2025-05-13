import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import os

# Load data dari Excel
df = pd.read_excel("data/data_master.xlsx")

# Isi kosong pada kolom Kode dengan string kosong
df["Kode"] = df["Kode"].fillna("")

# App title
st.title("🛍️ Produk Mbak Dike")

# Search bar
search_query = st.text_input("Cari Produk")

# Filter berdasarkan pencarian
if search_query:
    filtered_df = df[df["Nama Produk"].str.contains(search_query, case=False, na=False)]
else:
    filtered_df = df

# Inisialisasi keranjang belanja
if "cart" not in st.session_state:
    st.session_state.cart = []

# Tampilkan daftar produk
st.subheader("Daftar Produk")

for index, row in filtered_df.iterrows():
    cols = st.columns([1, 2, 2])

    # Kode produk
    with cols[0]:
        kode = str(row["Kode"]).strip()
        img_path = f"data/images/{kode}.jpg"
        if os.path.exists(img_path):
            st.image(img_path, width=100)
        else:
            st.image("https://via.placeholder.com/100", width=100)

    # Info produk
    with cols[1]:
        st.markdown(f"**{row['Nama Produk']}**")
        st.markdown(f"Harga: Rp {int(row['Harga']):,}")
        st.markdown(f"MOQ: {int(row['MOQ'])}")

    # Tombol tambah ke keranjang
    with cols[2]:
        if st.button(f"Tambah ke Keranjang {row['No']}"):
            st.session_state.cart.append(row.to_dict())
            st.success(f"Ditambahkan: {row['Nama Produk']}")

# Tampilkan keranjang
st.subheader("🛒 Keranjang Belanja")
if st.session_state.cart:
    cart_df = pd.DataFrame(st.session_state.cart)
    st.table(cart_df[["Nama Produk", "Harga", "MOQ"]])

    # Tombol checkout
    if st.button("Checkout"):
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = BytesIO()
        cart_df.to_excel(output, index=False)
        st.download_button(
            label="Download Report Excel",
            data=output.getvalue(),
            file_name=f"checkout_{now}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Keranjang masih kosong.")






# import streamlit as st
# import pandas as pd
# import os
# import zipfile
# import matplotlib.pyplot as plt
# from io import BytesIO
# import json
# import smtplib
# from datetime import datetime
# import time
# import base64

# # File to store user credentials
# USER_CREDENTIALS_FILE = "users.json"
# SENDER_EMAIL = "sandeepbikkina87@gmail.com"
# SENDER_PASSWORD = "ojcmfywmlqvkxtev"
# ADMIN_EMAIL = "sandeepbikkina87@gmail.com"






# def set_background(image_path):
#     """Sets a background image for the Streamlit app using base64 encoding."""
#     with open(image_path, "rb") as image_file:
#         encoded_string = base64.b64encode(image_file.read()).decode()

#     page_bg_img = f"""
#     <style>
#     .stApp {{
#         background-image: url("data:image/jpg;base64,{encoded_string}");
#         background-size: cover;
#         background-position: center;
#         background-attachment: fixed;
#     }}
#     </style>
#     """
#     st.markdown(page_bg_img, unsafe_allow_html=True)

# # Call this function at the start of your app
# set_background("backgroundimage.jpg")  # Make sure this file exists in the 'assets' folder

# # Session state for login & scheduler
# if "logged_in" not in st.session_state:
#     st.session_state["logged_in"] = False
# if "download_time" not in st.session_state:
#     st.session_state["download_time"] = None
# if "download_triggered" not in st.session_state:
#     st.session_state["download_triggered"] = False

# # Load & Save User Credentials
# def load_users():
#     if os.path.exists(USER_CREDENTIALS_FILE):
#         with open(USER_CREDENTIALS_FILE, "r") as f:
#             return json.load(f)
#     return {}

# def save_users(users):
#     with open(USER_CREDENTIALS_FILE, "w") as f:
#         json.dump(users, f)

# # Email Notification System
# def send_email(subject, body):
#     try:
#         server = smtplib.SMTP("smtp.gmail.com", 587)
#         server.starttls()
#         server.login(SENDER_EMAIL, SENDER_PASSWORD)
#         message = f"Subject: {subject}\n\n{body}"
#         server.sendmail(SENDER_EMAIL, ADMIN_EMAIL, message)
#         server.quit()
#     except Exception as e:
#         print(" Error:", e)

# # Recursively List All Files in Scheduled_Downloads
# def list_all_files():
#     base_folder = "Scheduled_Downloads"
#     folder_structure = {}

#     if os.path.exists(base_folder):
#         for root, _, files in os.walk(base_folder):
#             relative_path = os.path.relpath(root, base_folder)
#             if relative_path not in folder_structure:
#                 folder_structure[relative_path] = []
#             for file in files:
#                 folder_structure[relative_path].append(file)
    
#     return folder_structure

# # Get File Type Distribution for Pie Chart
# def get_file_distribution():
#     base_folder = "Scheduled_Downloads"
#     file_counts = {}

#     if os.path.exists(base_folder):
#         for root, _, files in os.walk(base_folder):
#             for file in files:
#                 file_ext = file.split(".")[-1].lower()
#                 file_counts[file_ext] = file_counts.get(file_ext, 0) + 1
#     return file_counts

# # ZIP all Files including Subfolders
# def zip_all_files():
#     base_folder = "Scheduled_Downloads"
#     zip_buffer = BytesIO()

#     with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
#         for root, _, files in os.walk(base_folder):
#             for file in files:
#                 file_path = os.path.join(root, file)
#                 zipf.write(file_path, os.path.relpath(file_path, base_folder))

#     zip_buffer.seek(0)
#     return zip_buffer

# #  Auto-Check & Trigger Scheduled Download
# def check_and_trigger_download():
#     if st.session_state["download_time"]:
#         current_time = datetime.now().strftime("%H:%M")
#         if current_time == st.session_state["download_time"] and not st.session_state["download_triggered"]:
#             zip_buffer = zip_all_files()
#             with open("scheduled_download.zip", "wb") as f:
#                 f.write(zip_buffer.getvalue())
#             st.session_state["download_triggered"] = True
#             st.success(f" Scheduled download completed at {current_time}! Files saved as 'scheduled_download.zip'.")
#             send_email("Download Completed", "Scheduled download has been successfully executed.")
#             st.rerun()

# #  **Auto-refresh every 30 seconds** to check the scheduled download time
# if st.session_state["download_time"]:
#     time.sleep(30)
#     check_and_trigger_download()


# # Load and Process CSV Data
# def load_data(file):
    
#     df = pd.read_csv(file)
#     df.rename(columns={'Client Name': 'client_name',
#                        'Buy/Sell': 'buy_sell',
#                        'Trade Price / Wght. Avg. Price': 'trade_price'}, inplace=True)
#     df['trade_price'] = pd.to_numeric(df['trade_price'], errors='coerce')
#     return df

# # Get Top 5 Buy & Sell Trades
# def get_top_trades(df):
#     top_buys = df[df['buy_sell'] == 'BUY'].nlargest(5, 'trade_price')
#     top_sells = df[df['buy_sell'] == 'SELL'].nlargest(5, 'trade_price')
#     return pd.concat([top_buys, top_sells])[['client_name', 'buy_sell', 'trade_price']]

# # Dashboard
# def show_dashboard():
#     st.title("📂 File Dashboard")
#     check_and_trigger_download()
#     # File Download Section
#     st.subheader("📥 Download Files")
#     if os.path.exists("Scheduled_Downloads"):
#         zip_buffer = zip_all_files()
#         if st.download_button(label="Download All Files", data=zip_buffer, file_name="AllFiles.zip", mime="application/zip"):
#             send_email("File Downloaded", "User downloaded all files.")
#             st.success("✅ Files downloaded successfully! Email notification sent.")
#     else:
#         st.warning("No files found!")

#     tab1, tab2 = st.tabs(["📥 Download & Schedule", "📊 File Analysis"])

#     with tab1:
#         # Top 5 Buy & Sell Trades
#         st.subheader("📊 Top 5 Buy & Sell Trades")
#         file_path = "bulk.csv"
#         if os.path.exists(file_path):
#             df = load_data(file_path)
#             top_trades = get_top_trades(df)
#             st.dataframe(top_trades)
#         else:
#             st.warning("Trade data file not found!")

        
#         # Schedule Download
#         st.subheader("⏳ Schedule Automatic Download")
#         download_time = st.text_input("Enter time (HH:MM format, 24-hour)", placeholder="Example: 15:30")
#         if st.button("Schedule Download"):
#             if download_time:
#                 st.session_state["download_time"] = download_time
#                 st.session_state["download_triggered"] = False
#                 send_email("Download Scheduled", f"User scheduled a file download at {download_time}.")
#                 st.success(f"✅ Scheduled! Files will be downloaded automatically at {download_time}.")
#                 st.rerun()
#             else:
#                 st.error("Please enter a valid time!")

#     with tab2:
#         # File Type Distribution
#         st.subheader("📊 File Type Distribution")
#         file_distribution = get_file_distribution()
#         if file_distribution:
#             fig, ax = plt.subplots()
#             ax.pie(file_distribution.values(), labels=file_distribution.keys(), autopct="%1.1f%%", startangle=90, colors=plt.cm.Paired.colors)
#             ax.axis("equal")
#             st.pyplot(fig)
#         else:
#             st.warning("No files found!")

#         # Display All Files
#         st.subheader("📂 Available Files")
#         file_structure = list_all_files()
#         for folder, files in file_structure.items():
#             with st.expander(f"📁 {folder}", expanded=False):
#                 for file in files:
#                     st.write(f"📄 {file}")

#     if st.button("Logout"):
#         st.session_state["logged_in"] = False
#         st.session_state.pop("username", None)
#         st.rerun()

# # Login & Signup Pages
# def login_signup():
#     st.title("🔐 Authentication")
#     option = st.radio("Select an option", ["Login", "Signup"])

#     if option == "Login":
#         username = st.text_input("Username")
#         password = st.text_input("Password", type="password")

#         if st.button("Login"):
#             users = load_users()
#             if username in users and users[username] == password:
#                 st.session_state["logged_in"] = True
#                 st.session_state["username"] = username
#                 st.success("✅ Logged in successfully!")
#                 st.rerun()
#             else:
#                 st.error("❌ Invalid credentials!")

#     elif option == "Signup":
#         new_username = st.text_input("New Username")
#         new_password = st.text_input("New Password", type="password")
#         confirm_password = st.text_input("Confirm Password", type="password")

#         if st.button("Signup"):
#             users = load_users()
#             if new_username in users:
#                 st.error("❌ Username already exists!")
#             elif new_password != confirm_password:
#                 st.error("❌ Passwords do not match!")
#             else:
#                 users[new_username] = new_password
#                 save_users(users)
#                 st.success("✅ Signup successful!")

# if not st.session_state["logged_in"]:
#     login_signup()
# else:
#     show_dashboard()























































##MILESTONE 2 GITHUB REPOSITORY CREATED



import streamlit as st
import pandas as pd
import os
import zipfile
import matplotlib.pyplot as plt
from io import BytesIO
import json
import smtplib
from datetime import datetime
import time
import base64

# File to store user credentials
USER_CREDENTIALS_FILE = "users.json"
SENDER_EMAIL = "sandeepbikkina87@gmail.com"
SENDER_PASSWORD = "ojcmfywmlqvkxtev"
ADMIN_EMAIL = "sandeepbikkina87@gmail.com"






def set_background(image_path):
    """Sets a background image for the Streamlit app using base64 encoding."""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()

    page_bg_img = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded_string}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

# Call this function at the start of your app
set_background("backgroundimage.jpg")  # Make sure this file exists in the 'assets' folder







# Session state for login & scheduler
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "download_time" not in st.session_state:
    st.session_state["download_time"] = None
if "download_triggered" not in st.session_state:
    st.session_state["download_triggered"] = False

# Load & Save User Credentials
def load_users():
    if os.path.exists(USER_CREDENTIALS_FILE):
        with open(USER_CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_CREDENTIALS_FILE, "w") as f:
        json.dump(users, f)

# Email Notification System
def send_email(subject, body):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        message = f"Subject: {subject}\n\n{body}"
        server.sendmail(SENDER_EMAIL, ADMIN_EMAIL, message)
        server.quit()
    except Exception as e:
        print("❌ Error:", e)

# Recursively List All Files in Scheduled_Downloads
def list_all_files():
    base_folder = "Scheduled_Downloads"
    folder_structure = {}

    if os.path.exists(base_folder):
        for root, _, files in os.walk(base_folder):
            relative_path = os.path.relpath(root, base_folder)
            if relative_path not in folder_structure:
                folder_structure[relative_path] = []
            for file in files:
                folder_structure[relative_path].append(file)
    
    return folder_structure

# Get File Type Distribution for Pie Chart
def get_file_distribution():
    base_folder = "Scheduled_Downloads"
    file_counts = {}

    if os.path.exists(base_folder):
        for root, _, files in os.walk(base_folder):
            for file in files:
                file_ext = file.split(".")[-1].lower()
                file_counts[file_ext] = file_counts.get(file_ext, 0) + 1
    return file_counts

# ZIP all Files including Subfolders
def zip_all_files():
    base_folder = "Scheduled_Downloads"
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(base_folder):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, base_folder))

    zip_buffer.seek(0)
    return zip_buffer

# ✅ Auto-Check & Trigger Scheduled Download
def check_and_trigger_download():
    if st.session_state["download_time"]:
        current_time = datetime.now().strftime("%H:%M")
        if current_time == st.session_state["download_time"] and not st.session_state["download_triggered"]:
            zip_buffer = zip_all_files()
            with open("scheduled_download.zip", "wb") as f:
                f.write(zip_buffer.getvalue())
            st.session_state["download_triggered"] = True
            st.success(f"✅ Scheduled download completed at {current_time}! Files saved as 'scheduled_download.zip'.")
            send_email("Download Completed", "Scheduled download has been successfully executed.")
            st.rerun()

# 🔄 **Auto-refresh every 30 seconds** to check the scheduled download time
if st.session_state["download_time"]:
    time.sleep(30)
    check_and_trigger_download()


# Load and Process CSV Data
def load_data(file):
    
    df = pd.read_csv(file)
    df.rename(columns={'Client Name': 'client_name',
                       'Buy/Sell': 'buy_sell',
                       'Trade Price / Wght. Avg. Price': 'trade_price'}, inplace=True)
    df['trade_price'] = pd.to_numeric(df['trade_price'], errors='coerce')
    return df

# Get Top 5 Buy & Sell Trades
def get_top_trades(df):
    top_buys = df[df['buy_sell'] == 'BUY'].nlargest(5, 'trade_price')
    top_sells = df[df['buy_sell'] == 'SELL'].nlargest(5, 'trade_price')
    return pd.concat([top_buys, top_sells])[['client_name', 'buy_sell', 'trade_price']]

# Dashboard
def show_dashboard():
    st.title("📂 File Dashboard")
    check_and_trigger_download()
    # File Download Section
    st.subheader("📥 Download Files")
    if os.path.exists("Scheduled_Downloads"):
        zip_buffer = zip_all_files()
        if st.download_button(label="Download All Files", data=zip_buffer, file_name="AllFiles.zip", mime="application/zip"):
            send_email("File Downloaded", "User downloaded all files.")
            st.success("✅ Files downloaded successfully! Email notification sent.")
    else:
        st.warning("No files found!")

    tab1, tab2 = st.tabs(["📥 Download & Schedule", "📊 File Analysis"])

    with tab1:
        # Top 5 Buy & Sell Trades
        st.subheader("📊 Top 5 Buy & Sell Trades")
        file_path = "bulk.csv"
        if os.path.exists(file_path):
            df = load_data(file_path)
            top_trades = get_top_trades(df)
            st.dataframe(top_trades)
        else:
            st.warning("Trade data file not found!")

        
        # Schedule Download
        st.subheader("⏳ Schedule Automatic Download")
        download_time = st.text_input("Enter time (HH:MM format, 24-hour)", placeholder="Example: 15:30")
        if st.button("Schedule Download"):
            if download_time:
                st.session_state["download_time"] = download_time
                st.session_state["download_triggered"] = False
                send_email("Download Scheduled", f"User scheduled a file download at {download_time}.")
                st.success(f"✅ Scheduled! Files will be downloaded automatically at {download_time}.")
                st.rerun()
            else:
                st.error("❌ Please enter a valid time!")

    with tab2:
        # File Type Distribution
        st.subheader("📊 File Type Distribution")
        file_distribution = get_file_distribution()
        if file_distribution:
            fig, ax = plt.subplots()
            ax.pie(file_distribution.values(), labels=file_distribution.keys(), autopct="%1.1f%%", startangle=90, colors=plt.cm.Paired.colors)
            ax.axis("equal")
            st.pyplot(fig)
        else:
            st.warning("No files found!")

        # Display All Files
        st.subheader("📂 Available Files")
        file_structure = list_all_files()
        for folder, files in file_structure.items():
            with st.expander(f"📁 {folder}", expanded=False):
                for file in files:
                    st.write(f"📄 {file}")

    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state.pop("username", None)
        st.rerun()

# Login & Signup Pages
def login_signup():
    st.title("🔐 Authentication")
    option = st.radio("Select an option", ["Login", "Signup"])

    if option == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            users = load_users()
            if username in users and users[username] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success("✅ Logged in successfully!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials!")

    elif option == "Signup":
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.button("Signup"):
            users = load_users()
            if new_username in users:
                st.error("❌ Username already exists!")
            elif new_password != confirm_password:
                st.error("❌ Passwords do not match!")
            else:
                users[new_username] = new_password
                save_users(users)
                st.success("✅ Signup successful!")

if not st.session_state["logged_in"]:
    login_signup()
else:
    show_dashboard()

































































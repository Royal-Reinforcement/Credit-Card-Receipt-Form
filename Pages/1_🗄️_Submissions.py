import streamlit as st
import pandas as pd
import smartsheet
import requests

from PIL import Image
from io import BytesIO

import functions


st.set_page_config(page_title='Credit Card Receipts', page_icon='💳', layout='centered')


st.image(st.secrets["logo"], width=100)


st.title('Receipt Submissions')
st.info('Review your already-submitted receipts here.')


df_submissions = functions.smartsheet_to_dataframe_with_row_ids(st.secrets['smartsheet']['sheet_id']['submissions'])
df_submissions = df_submissions.dropna(subset=['Employee'])

df_cards = functions.smartsheet_to_dataframe_with_row_ids(st.secrets['smartsheet']['sheet_id']['cards'])
df_cards['Suffix']   = df_cards['Suffix'].astype(str)
df_cards['Suffix']   = df_cards['Suffix'].replace(r'\.0$', '', regex=True)
df_cards['Password'] = df_cards['Suffix'].str[-4:]


names          = ['Select your name'] + df_submissions['Employee'].sort_values().unique().tolist()
name           = st.selectbox('🪪 Name on Card', names)

if name != 'Select your name':

    passwords = df_cards[df_cards['Employee'] == name]
    passwords = passwords['Password'].values

    st.subheader('🔐 Authentication')

    password = st.text_input(f"Please provide the last four digits of one of your cards:", type='password', value=None)

    if password is not None:
        
        if password in passwords:

            submissions = df_submissions[df_submissions['Employee'] == name]
    
            st.subheader('💳 Transactions')
            st.dataframe(submissions.drop(columns='row_id'), use_container_width=True, hide_index=True)

            st.subheader('🧾 Receipts')
    
            st.success('Coming soon!')
        
        else:

            st.warning('Please review the **name** selected and the **last four digits** provided.')
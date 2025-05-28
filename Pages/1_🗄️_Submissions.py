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

st.success('**Coming soon!**')
# df_submissions = functions.smartsheet_to_dataframe_with_row_ids(st.secrets['smartsheet']['sheet_id']['submissions'])
# df_submissions = df_submissions.dropna(subset=['Employee'])

# names          = ['Select your name'] + df_submissions['Employee'].sort_values().unique().tolist()
# name           = st.selectbox('🪪 Name on Card', names)

# if name != 'Select your name':

#     submissions = df_submissions[df_submissions['Employee'] == name]
    
#     st.subheader('💳 Transactions')
#     st.dataframe(submissions.drop(columns='row_id'), use_container_width=True, hide_index=True)

#     st.subheader('🧾 Receipts')
    
#     st.success('Coming soon!')
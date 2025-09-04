import streamlit as st
import pandas as pd
import smartsheet
import requests
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor

# import functions

def smartsheet_to_dataframe(sheet_id):
    smartsheet_client = smartsheet.Smartsheet(st.secrets['smartsheet']['access_token'])
    sheet             = smartsheet_client.Sheets.get_sheet(sheet_id)
    columns           = [col.title for col in sheet.columns]
    rows              = []
    for row in sheet.rows: rows.append([cell.value for cell in row.cells])
    return pd.DataFrame(rows, columns=columns)

def smartsheet_to_dataframe_with_row_ids(sheet_id):
    smartsheet_client = smartsheet.Smartsheet(st.secrets['smartsheet']['access_token'])
    sheet             = smartsheet_client.Sheets.get_sheet(sheet_id)
    columns           = [col.title for col in sheet.columns]
    rows              = []
    row_ids           = []
    for row in sheet.rows:
        row_ids.append(row.id)
        rows.append([cell.value for cell in row.cells])
    df = pd.DataFrame(rows, columns=columns)
    df['row_id'] = row_ids
    return df


st.set_page_config(page_title='Credit Card Receipts', page_icon='💳', layout='centered')


st.image(st.secrets["logo"], width=100)


st.title('Receipt Submissions')
st.info('Review your already-submitted receipts here.')


df_submissions = smartsheet_to_dataframe_with_row_ids(st.secrets['smartsheet']['sheet_id']['submissions'])
df_submissions = df_submissions.dropna(subset=['Employee'])

df_cards = smartsheet_to_dataframe_with_row_ids(st.secrets['smartsheet']['sheet_id']['cards'])
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
            submissions = submissions.sort_values(by='Submitted', ascending=False)
    
            st.subheader('💳 Transactions')
            st.dataframe(submissions.drop(columns=['row_id','Reconciled?']), use_container_width=True, hide_index=True)

            st.subheader('🧾 Receipts')

            smartsheet_client = smartsheet.Smartsheet(st.secrets['smartsheet']['access_token'])

            def download_attachment_to_temp(att_obj):
                file_ext = os.path.splitext(att_obj.name)[1].lower()
                tmpdir = tempfile.TemporaryDirectory()
                smartsheet_client.Attachments.download_attachment(att_obj, tmpdir.name)
                filepath = os.path.join(tmpdir.name, att_obj.name)
                return filepath, file_ext, tmpdir

            def gather_attachments_for_rows(sheet_id, row_ids):
                all_attachments = []
                for row_id in row_ids:
                    attachments_meta = smartsheet_client.Attachments.list_row_attachments(sheet_id, row_id).data
                    for att_meta in attachments_meta:
                        att_obj = smartsheet_client.Attachments.get_attachment(sheet_id, att_meta.id)
                        all_attachments.append(att_obj)
                return all_attachments

            def show_attachments(sheet_id, row_ids):
                attachments = gather_attachments_for_rows(sheet_id, row_ids)

                temp_dirs = []
                with ThreadPoolExecutor(max_workers=5) as executor:
                    results = list(executor.map(download_attachment_to_temp, attachments))
                    for i, (filepath, file_ext, tmpdir) in enumerate(results):
                        temp_dirs.append(tmpdir)

                        with st.expander(f"{os.path.basename(filepath)}", expanded=False):
                            if file_ext == ".pdf":
                                st.pdf(filepath)
                            else:
                                st.image(filepath, use_container_width=True)


            today           = pd.to_datetime('today').date()
            minus_30_days   = today - pd.Timedelta(days=30)

            dates = st.date_input('Submitted dates:', value=(minus_30_days, today))

            if st.button('View Receipts', type='primary', use_container_width=True):
                if len(dates) == 2:
                    start_date, end_date = dates
                    mask = (pd.to_datetime(submissions['Submitted']).dt.date >= start_date) & (pd.to_datetime(submissions['Submitted']).dt.date <= end_date)
                    submissions = submissions[mask]

                with st.spinner('Fetching receipts...'):
                    show_attachments(st.secrets['smartsheet']['sheet_id']['submissions'], submissions['row_id'].head(10).tolist())



        
        else:

            st.warning('Please review the **name** selected and the **last four digits** provided.')
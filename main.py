import streamlit as st
import pandas as pd
import smartsheet
import tempfile

st.set_page_config(page_title='Credit Card Receipts', page_icon='💳', layout='centered')

st.image(st.secrets["logo"], width=100)

st.title('Credit Card Receipts')
st.info('Communication of your card swipes.')


if 'receipt_submitted' not in st.session_state:
    st.session_state.receipt_submitted = False


def is_receipt_submitted():
    st.session_state.receipt_submitted = True


def smartsheet_to_dataframe(sheet_id):
    smartsheet_client = smartsheet.Smartsheet(st.secrets['smartsheet']['access_token'])
    sheet             = smartsheet_client.Sheets.get_sheet(sheet_id)
    columns           = [col.title for col in sheet.columns]
    rows              = []
    for row in sheet.rows: rows.append([cell.value for cell in row.cells])
    return pd.DataFrame(rows, columns=columns)


df_settings = smartsheet_to_dataframe(st.secrets['smartsheet']['sheet_id']['settings'])
df_cards    = smartsheet_to_dataframe(st.secrets['smartsheet']['sheet_id']['cards'])


date        = None
name        = None
department  = None
card        = None
task_id     = None
location    = None
total       = None


date        = st.date_input('🗓️ Date of Transaction', disabled=st.session_state.receipt_submitted)


cards       = df_cards[df_cards['Status'] == 'Active']
names       = ['Select your name'] + cards['Employee'].sort_values().unique().tolist()
name        = st.selectbox('🪪 Name on Card', names, disabled=st.session_state.receipt_submitted)

if name != 'Select your name':
    card_type  = cards[cards['Employee'] == name]
    department = cards[cards['Employee'] == name]['Department'].values[0]
        
    if card_type.shape[0] > 1:
        card_types = ['Select the card you used'] + card_type['Bank'].sort_values().unique().tolist()

        card_choice = st.selectbox('💳 Card used', card_types, disabled=st.session_state.receipt_submitted)

        if card_choice != 'Select the card you used':
            card = card_type[card_type['Bank'] == card_choice]['Bank'].values[0]

    else:
        card = card_type['Bank'].values[0]


    if card is not None and card != 'Select the card you used':
        location = st.text_input('📍 Location of Transaction', value=None, placeholder='Ace Hardware, Amazon, Publix, Walmart, etc.', disabled=st.session_state.receipt_submitted)


        if location is not None:
            total = st.number_input('💰 **Total Amount**', value=None, step=1.00, format="%.2f", min_value=0.00, disabled=st.session_state.receipt_submitted)

            if total is not None:

                department_settings = df_settings[df_settings[department] == True]
                category_options    = department_settings['Financial Code Description'].sort_values().unique()
                categories       = st.multiselect('⚖️ **Applicable Spend Categories**', category_options, disabled=st.session_state.receipt_submitted)

# TODO: Determine is categories contains a category in which Breezeway ID is required.













task_id = st.number_input('Breezeway Task ID', value=None, step=1, disabled=st.session_state.receipt_submitted)

if task_id is not None:
    location = st.text_input('Location of Transaction', value=None, placeholder='Ace Hardware, Amazon, Publix, Walmart, etc.', disabled=st.session_state.receipt_submitted)

    if location is not None:
        smartsheet_client = smartsheet.Smartsheet(st.secrets['smartsheet']['access_token'])
        sheet_settings    = smartsheet_client.Sheets.get_sheet(st.secrets['smartsheet']['sheet_id']['cards'])
        columns           = [col.title for col in sheet_settings.columns]
        rows              = []
        for row in sheet_settings.rows: rows.append([cell.value for cell in row.cells])
        cards          = pd.DataFrame(rows, columns=columns)
        cards          = cards[cards['Status'] == 'Active']
        names          = cards['Employee'].sort_values().unique()
        name           = st.selectbox('Name on Card', names, disabled=st.session_state.receipt_submitted)

        card_type = cards[cards['Employee'] == name]
        
        if card_type.shape[0] > 1:
            card = st.selectbox('Card Used', card_type['Bank'], disabled=st.session_state.receipt_submitted)
        else:
            card = card_type['Bank'].values[0]


        if card is not None:
            total = st.number_input('Total Amount', value=None, step=1.00, format="%.2f", min_value=0.00, disabled=st.session_state.receipt_submitted)

            if total is not None:
                file = st.file_uploader('Reciept (Photo, Screenshot, or PDF)', type=['jpg', 'jpeg', 'png', 'heif', 'pdf'], help='Upload a photo, screenshot, or PDF of the receipt for this transaction.', accept_multiple_files=False, disabled=st.session_state.receipt_submitted)
                
                if file is not None:
                    
                    sheet_settings = smartsheet_client.Sheets.get_sheet(st.secrets['smartsheet']['sheet_id']['settings'])
                    columns        = [col.title for col in sheet_settings.columns]
                    rows           = []
                    departments    = st.secrets['departments']
                    department     = st.selectbox('**Department**', departments, )
                    for row in sheet_settings.rows: rows.append([cell.value for cell in row.cells])
                    settings       = pd.DataFrame(rows, columns=columns)
                    settings       = settings[settings[department] == True]
                    categories     = settings['Financial Code Description'].sort_values().unique()
                    selections     = st.multiselect('**Applicable Spend Categories**', categories, disabled=st.session_state.receipt_submitted)
                    amount         = 0.00

                    if selections != []:
                        st.subheader('Spend Allocation')
                        for selection in selections:
                            amount += st.number_input(selection, min_value=0.00, value=0.00, step=1.00, key=f"{selection}_amount", disabled=st.session_state.receipt_submitted)
                    
                        amount = round(amount, 2)
                        
                        st.metric('**Remaining Allocation**', round(total - amount, 2), help='The amount you have left to allocate to the selected categories.')

                        nonzero_check = True

                        for selection in selections:
                            if st.session_state[f"{selection}_amount"] == 0:
                                nonzero_check = False
                                break
                        
                        if (total - amount) == 0.00 and nonzero_check:

                            if st.button(f"Submit **${amount}** for **{department}**", use_container_width=True, type='primary', on_click=is_receipt_submitted, disabled=st.session_state.receipt_submitted):
                                
                                submission = []

                                for selection in selections:
                                    submission.append({
                                        'Submitted': pd.Timestamp.now().strftime('%m-%d-%Y %H:%M:%S'),
                                        'Date': date.strftime('%m-%d-%Y'),
                                        'Task ID': task_id,
                                        'Location': location,
                                        'Employee': name,
                                        'Card Used': card,
                                        'Total': total,
                                        'Department': department,
                                        'Financial Code Description': selection,
                                        'Allocation': st.session_state[f"{selection}_amount"]
                                    })

                                submission_df = pd.DataFrame(submission)
                                submission_df = pd.merge(submission_df, settings[['Financial Code Type','Financial Code Description','Financial Code Value']], on='Financial Code Description', how='left')
                                submission_df = pd.merge(submission_df, cards, how='left', left_on=['Employee', 'Card Used'], right_on=['Employee', 'Bank'])
                                submission_df = submission_df[['Submitted','Date','Department','Employee','Bank','Suffix','Location','Total','Task ID','Financial Code Type','Financial Code Value','Financial Code Description','Allocation']]
                                submission_df.columns = ['Submitted','Date','Department','Employee','Card','Card Suffix','Location','Total','Task ID','Financial Code Type','Financial Code Value','Financial Code Description','Allocation']
                                submission_df = submission_df.astype(str)

                                submission_df['Location']             = submission_df['Location'].str.upper()
                                submission_df['Task ID']              = submission_df['Task ID'].replace(r'\.0$', '', regex=True)
                                submission_df['Card Suffix']          = submission_df['Card Suffix'].replace(r'\.0$', '', regex=True)
                                submission_df['Financial Code Value'] = submission_df['Financial Code Value'].replace(r'\.0$', '', regex=True)

                                sheet         = smartsheet_client.Sheets.get_sheet(st.secrets['smartsheet']['sheet_id']['submissions'])
                                column_map    = {col.title: col.id for col in sheet.columns}

                                def submit_to_smartsheet(df):
                                    row_ids = []

                                    for _, row_data in df.iterrows():

                                        row        = smartsheet.models.Row()
                                        row.to_top = True
                                        row.cells  = []

                                        for col in df.columns: row.cells.append({"column_id": column_map[col], "value": row_data[col]})

                                        response = smartsheet_client.Sheets.add_rows(st.secrets['smartsheet']['sheet_id']['submissions'], [row])

                                        row_ids.append(response.result[0].id)

                                    return row_ids
                                
                                def attach_image_to_rows(row_ids, image_file):
                                    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                                        tmp_file.write(image_file.read())
                                        tmp_file.flush()

                                        file_name = f"{card}_{date.strftime("%Y_%U")}_{department}_{location}_{name}_{task_id}.{file.type.rpartition('/')[-1]}"
                                        
                                        for row_id in row_ids:
                                            with open(tmp_file.name, 'rb') as file_stream:
                                                smartsheet_client.Attachments.attach_file_to_row(st.secrets['smartsheet']['sheet_id']['submissions'], row_id, (file_name, file_stream, 'application/octet-stream'))
                                
                                row_ids = submit_to_smartsheet(submission_df)
                                attach_image_to_rows(row_ids, file)

                                st.balloons()
                                st.success('**Thank you!** **Transaction** and **receipt** submitted.', icon='🏅')
                                st.link_button('Submit another receipt', url=st.secrets.url_mobile, use_container_width=True, type='primary')
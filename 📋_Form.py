import streamlit as st
import pandas as pd
import smartsheet
import tempfile

import functions


st.set_page_config(page_title='Credit Card Receipts', page_icon='💳', layout='centered')


st.image(st.secrets["logo"], width=100)


st.title('Credit Card Receipts')
st.info('Communication of your card swipes.')


if 'receipt_submitted' not in st.session_state:
    st.session_state.receipt_submitted = False


def is_receipt_submitted():
    st.session_state.receipt_submitted = True


df_settings = functions.smartsheet_to_dataframe(st.secrets['smartsheet']['sheet_id']['settings'])
df_cards    = functions.smartsheet_to_dataframe(st.secrets['smartsheet']['sheet_id']['cards'])


date             = None
name             = None
department       = None
card             = None
location         = None
total            = None
is_web_purchase  = None
is_task_required = False
task_id          = None
home             = None



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

            is_purchased_online = st.selectbox('🧑🏻‍💻 Is this an online purchase?', options=['Select a response', 'No', 'Yes'])

            if is_purchased_online != 'Select a response':

                if is_purchased_online == 'No':
                    is_web_purchase = False
                else:
                    is_web_purchase = True
            
            if is_web_purchase is not None:

                total = st.number_input('💰 Total Amount from Receipt', value=None, step=1.00, format="%.2f", min_value=0.00, placeholder=1234.56, disabled=st.session_state.receipt_submitted)

                if total is not None:

                    department_settings = df_settings[df_settings[department] == True]
                    category_options    = department_settings['Financial Code Description'].sort_values().unique()
                    categories          = st.multiselect('⚖️ Spending Categories of Transaction', category_options, disabled=st.session_state.receipt_submitted)
                    task_required       = df_settings[df_settings['Breezeway Required']]
                    is_task_required    = task_required['Financial Code Description'].isin(categories).any()

                    if categories is not None and categories != []:
                        amount = 0.00

                        st.subheader('Spend Allocation')
                        st.info('Distribute the total amount across the selected categories. There must be a balance of $0.00 to proceed, and all categories must have a non-zero allocation.')

                        for category in categories:
                            amount += st.number_input(category, min_value=0.00, value=None, step=1.00, key=f"{category}_amount", placeholder=123.45, disabled=st.session_state.receipt_submitted) or 0.00
                    
                        amount = round(amount, 2)
                        
                        st.metric('**Remaining Allocation**', round(total - amount, 2), help='The amount you have left to allocate to the selected categories.')

                        nonzero_check = True

                        for category in categories:
                            if st.session_state[f"{category}_amount"] == 0:
                                nonzero_check = False
                                break
                        
                        if (total - amount) == 0.00 and nonzero_check:
                            file = st.file_uploader('🧾 Reciept (Photo, Screenshot, or PDF)', type=['jpg', 'jpeg', 'png', 'heif', 'pdf'], help='Upload a photo, screenshot, or PDF of the receipt for this transaction.', accept_multiple_files=False, disabled=st.session_state.receipt_submitted)


                            if file is not None:
                                
                                if is_task_required:
                                    task_id = st.number_input('#️⃣ Breezeway Task ID', value=None, placeholder=1234567890, step=1, disabled=st.session_state.receipt_submitted)

                                    if task_id is not None:
                                        home = st.text_input('🏠 Property', value=None, placeholder='Please provide the Unit_Code', disabled=st.session_state.receipt_submitted)
                                else:
                                    task_id = 'NOTASK'
                                    home    = 'NONE'
                                

                                if task_id is not None and home is not None:

                                    if st.button(f"Submit **${amount}** for **{department}**", use_container_width=True, type='primary', disabled=st.session_state.receipt_submitted):
                                    # if st.button(f"Submit **${amount}** for **{department}**", use_container_width=True, type='primary', on_click=is_receipt_submitted, disabled=st.session_state.receipt_submitted):
                                        
                                        submission = []

                                        for category in categories:
                                            submission.append({
                                                'Submitted': pd.Timestamp.now().strftime('%m-%d-%Y %H:%M:%S'),
                                                'Date': date.strftime('%m-%d-%Y'),
                                                'Task ID': task_id,
                                                'Property': home,
                                                'Location': location,
                                                'Employee': name,
                                                'Card Used': card,
                                                'Total': total,
                                                'Department': department,
                                                'Financial Code Description': category,
                                                'Allocation': st.session_state[f"{category}_amount"]
                                            })

                                        submission_df = pd.DataFrame(submission)
                                        submission_df = pd.merge(submission_df, df_settings[['Financial Code Type','Financial Code Description','Financial Code Value']], on='Financial Code Description', how='left')
                                        submission_df = pd.merge(submission_df, cards, how='left', left_on=['Employee', 'Card Used', 'Department'], right_on=['Employee', 'Bank', 'Department'])
                                        submission_df = submission_df[['Submitted','Date','Department','Employee','Bank','Suffix','Location','Total','Task ID','Property','Financial Code Type','Financial Code Value','Financial Code Description','Allocation']]
                                        submission_df.columns = ['Submitted','Date','Department','Employee','Card','Card Suffix','Location','Total','Task ID','Property','Financial Code Type','Financial Code Value','Financial Code Description','Allocation']
                                        submission_df = submission_df.astype(str)
                                        submission_df['Website?']    = is_web_purchase
                                        submission_df['Reconciled?'] = False

                                        submission_df['Location']             = submission_df['Location'].str.upper()
                                        submission_df['Task ID']              = submission_df['Task ID'].replace(r'\.0$', '', regex=True)
                                        submission_df['Card Suffix']          = submission_df['Card Suffix'].replace(r'\.0$', '', regex=True)
                                        submission_df['Financial Code Value'] = submission_df['Financial Code Value'].replace(r'\.0$', '', regex=True)

                                        smartsheet_client = smartsheet.Smartsheet(st.secrets['smartsheet']['access_token'])
                                        sheet             = smartsheet_client.Sheets.get_sheet(st.secrets['smartsheet']['sheet_id']['submissions'])
                                        column_map        = {col.title: col.id for col in sheet.columns}

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

                                                file_name = f"{date.strftime("%Y_%U")}_{card}_{submission_df['Card Suffix'].values[0]}_{location}_{department}_{name}_{task_id}.{file.type.rpartition('/')[-1]}"
                                                
                                                for row_id in row_ids:
                                                    with open(tmp_file.name, 'rb') as file_stream:
                                                        smartsheet_client.Attachments.attach_file_to_row(st.secrets['smartsheet']['sheet_id']['submissions'], row_id, (file_name, file_stream, 'application/octet-stream'))
                                        
                                        row_ids = submit_to_smartsheet(submission_df)
                                        attach_image_to_rows(row_ids, file)

                                        st.balloons()
                                        st.success('**Thank you!** Receipt submitted.', icon='🏅')
                                        st.link_button('Submit another receipt', url=st.secrets.url_mobile, use_container_width=True, type='primary')
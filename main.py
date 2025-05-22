import streamlit as st
import pandas as pd
import smartsheet

st.set_page_config(page_title='Credit Card Receipts', page_icon='💳', layout='centered')

st.image(st.secrets["logo"], width=100)

st.title('Credit Card Receipts')
st.info('Communication of what card swipes are toward.')

taskid = st.number_input('Breezeway Task ID', value=None, step=1)

if taskid is not None:
    photo = st.file_uploader('Reciept')

    if photo is not None:

        departments = st.secrets['departments']
        department  = st.selectbox('**Department**', departments)

        SMARTSHEET_ACCESS_TOKEN = st.secrets['smartsheet']['api_token']
        ss_client = smartsheet.Smartsheet(SMARTSHEET_ACCESS_TOKEN)
        SHEET_ID = st.secrets['smartsheet']['sheet_id']
        sheet = ss_client.Sheets.get_sheet(SHEET_ID)
        columns = [col.title for col in sheet.columns]
        rows = []

        for row in sheet.rows:
            values = []
            for cell in row.cells:
                values.append(cell.value)
            rows.append(values)

        df = pd.DataFrame(rows, columns=columns)
        df = df[df[department] == True]
        
        categories = df['Financial Code Description'].sort_values().unique()

        selections = st.multiselect('**Applicable Spend Categories**', categories)

        amount = 0.00

        if selections != []:
            st.subheader('Spend Allocation')
            for selection in selections:
                amount += st.number_input(selection, min_value=0.00, value=0.00, step=1.00, key=f"{selection}_amount")
        
            amount = round(amount, 2)
            st.metric('**Total Amount**', amount)

            nonzero_check = True

            for selection in selections:
                if st.session_state[f"{selection}_amount"] == 0:
                    nonzero_check = False
                    break
            
            if amount > 0 and nonzero_check:
                if st.button(f"Submit **${amount}** for **{department}**", use_container_width=True, type='primary'):
                    
                    submission = []

                    for selection in selections:
                        submission.append({
                            'Task ID': taskid,
                            'Department': department,
                            'Financial Code Description': selection,
                            'Amount': st.session_state[f"{selection}_amount"]
                        })

                    submission_df = pd.DataFrame(submission)
                    submission_df = pd.merge(submission_df, df[['Financial Code Type','Financial Code Description','Financial Code Value']], on='Financial Code Description', how='left')
                    submission_df = submission_df[['Financial Code Type','Financial Code Value','Financial Code Description','Task ID','Department','Amount']]
                    st.dataframe(submission_df, use_container_width=True, hide_index=True)
                    st.image(photo)
                    st.toast('Success!', icon='✅')
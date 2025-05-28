import streamlit as st
import pandas as pd
import datetime
import smartsheet
import tempfile

import functions

st.set_page_config(page_title='Credit Card Receipts', page_icon='💳', layout='centered')


st.image(st.secrets["logo"], width=100)


st.title('Receipt Accounting')
password = st.text_input('🔐 Enter the password to access the accounting data:', type='password')

if password == st.secrets['password']:
    df_submissions = functions.smartsheet_to_dataframe_with_row_ids(st.secrets['smartsheet']['sheet_id']['submissions'])

    # l, r = st.columns(2)

    # today              = datetime.date.today()
    # this_week_tuesday  = today - datetime.timedelta(days=(today.weekday() - 1) % 7)
    # last_week_tuesday  = this_week_tuesday - datetime.timedelta(weeks=1)

    # end_date           = r.date_input('🗓️ Period End',   value=this_week_tuesday)
    # start_date         = l.date_input('🗓️ Period Start', value=last_week_tuesday)
    # date_range         = pd.date_range(start_date, end_date)

    # date_range

    df_submissions['Allocation'] = df_submissions['Allocation'].astype(float)

    fields = st.multiselect('Fields of Interest', options=df_submissions.columns, default=None)

    if fields is not None and fields != []:

        categories = pd.pivot_table(
            data=df_submissions,
            index=fields,
            values='Allocation',
            aggfunc='sum'
        )

        categories = categories.sort_values(by='Allocation', ascending=False)
        categories

    '**Date range** coming soon!'
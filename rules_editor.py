from copy import deepcopy
import uuid
import streamlit as st
import pandas as pd
from streamlit.elements.widgets.data_editor import _apply_dataframe_edits, determine_dataframe_schema
import pyarrow as pa

st.set_page_config(
    page_title="Rules Editor",
    page_icon="📊",
    layout="wide"
)

uploaded_file = st.file_uploader("Import Rule Set", type="csv")

if uploaded_file is not None:
    st.divider()
    # Read the uploaded file
    df = pd.read_csv(uploaded_file)

    # df = pd.read_csv("ryffine_dita/rules/all.csv")

    if st.session_state.get("current_df") is None:
        st.session_state["current_df"] = df

    

    col_title_map = {
        "type": "Rule Type",
        "rule": "Rule",
        "implemented": "Is implemented?",
        "rule_location": "Info Model Location",
        "rule_file": "Rule File",
        "rule_code": "Rule Code",
        "context_required": "Is Context Required?",
        "applicable_to": "Applicable To",
        "rule_id": "Rule Id",
        "rule_element": "Rule Element",
        "uid": "Unique ID",
    }

    title_col_map = {
        val: key for key, val in col_title_map.items()
    }

    filtering_df = pd.DataFrame(
        {
            col: [""] for col in st.session_state["current_df"].columns
        }
    )

    st.subheader("Rule Filtering")
    edited_filterng_df = st.data_editor(
        filtering_df,
        key="df_filterer",
        column_order=[
            'rule_id',
            'rule',
            'type',
            'applicable_to',
            'implemented',
            'context_required',
            'rule_file',
            'rule_code',
            'rule_element',
            'rule_location'
        ],
        column_config={
            **{col: st.column_config.TextColumn(
                col_title_map[col],
                default=None
            )
            for col in df.columns},
            "implemented": st.column_config.SelectboxColumn(
                col_title_map["implemented"],
                options=[
                    None,
                    "True",
                    "False"
                ],
                default="",
            ),
            "context_required": st.column_config.SelectboxColumn(
                col_title_map["context_required"],
                options=[
                    None,
                    "True",
                    "False"
                ],
                default="",
            ),
            "type": st.column_config.SelectboxColumn(
                col_title_map["type"],
                options=[
                    None,
                    "rng",
                    "programmatic",
                    "semantic",
                ],
            ),
        },
        hide_index=True
    )

    st.session_state["filtered_df"] = deepcopy(st.session_state["current_df"])
    unfiltered_df = deepcopy(pd.DataFrame())
    for col in col_title_map:
        filter_string = edited_filterng_df.loc[0, col]
        if filter_string not in ["", None]:
            st.session_state["filtered_df"] = st.session_state["filtered_df"][st.session_state["filtered_df"][col].astype(str).str.contains(filter_string, case=False, na=False)]
            unfiltered_df = st.session_state["current_df"][~st.session_state["current_df"].index.isin(st.session_state["filtered_df"].index)]

    def on_change():
        arrow_table = pa.Table.from_pandas(st.session_state["filtered_df"])
        dataframe_schema = determine_dataframe_schema(st.session_state["filtered_df"], arrow_table.schema)
        editor_state = st.session_state["df_editor"]

        temp_df = deepcopy(st.session_state["filtered_df"])
        # Add index and uid
        for r in editor_state["added_rows"]:
            r["_index"] = len(st.session_state["current_df"])
            r['uid'] = str(uuid.uuid4())

        # Updated df
        _apply_dataframe_edits(
            temp_df,
            editor_state,
            dataframe_schema
        )
        st.session_state["filtered_df"] = temp_df
        st.session_state["current_df"] = pd.concat([unfiltered_df, temp_df], ignore_index=True)

    st.subheader("Rules")
    edited_df = st.data_editor(
        st.session_state["filtered_df"],
        num_rows="dynamic",
        key="df_editor",
        on_change=on_change,
        column_order=[
            'rule_id',
            'rule',
            'type',
            'applicable_to',
            'implemented',
            'context_required',
            'rule_file',
            'rule_code',
            'rule_element',
            'rule_location',
            '_index',
        ],
        column_config={
            "type": st.column_config.SelectboxColumn(
                col_title_map["type"],
                options=[
                    "rng",
                    "programmatic",
                    "semantic",
                ],
                help="What type of **Rule** is this?",
                required=True,
                default=edited_filterng_df.loc[0, "type"]
            ),
            "rule": st.column_config.TextColumn(
                col_title_map["rule"],
                width="large",
                pinned=True,
                help="The Rule"
            ),
            "implemented": st.column_config.CheckboxColumn(
                col_title_map["implemented"],
                help="Is this **Rule** implemented?",
                default=edited_filterng_df.loc[0, "implemented"] or False
            ),
            "rule_location": st.column_config.TextColumn(
                col_title_map["rule_location"],
                disabled=True
            ),
            "rule_file": st.column_config.TextColumn(
                col_title_map["rule_file"],
                disabled=True
            ),
            "rule_code": st.column_config.TextColumn(
                col_title_map["rule_code"],
                disabled=True
            ),
            "context_required": st.column_config.CheckboxColumn(
                col_title_map["context_required"],
                help="Is extra context require to validate/fulfill this **Rule**?",
                default=edited_filterng_df.loc[0, "context_required"] or False
            ),
            "applicable_to": st.column_config.TextColumn(
                col_title_map["applicable_to"],
                help="Comma seperated list of Task|Concept|Reference|Troubleshooting|Learning objective|Bookmap|Glossary terms|Map|Scripts|Field definitions.",
                validate=r"^(Task|Concept|Reference|Troubleshooting|Learning objective|Bookmap|Glossary terms|Map|Scripts|Field definitions)(\s*,\s*(Task|Concept|Reference|Troubleshooting|Learning objective|Bookmap|Glossary terms|Map|Scripts|Field definitions))*$",
                default=edited_filterng_df.loc[0, "applicable_to"]
            ),
            "rule_id": st.column_config.TextColumn(
                col_title_map["rule_id"],
                disabled=True,
                pinned=True,
                default=max(df["rule_id"]) + 1
            ),
            "rule_element": st.column_config.TextColumn(
                col_title_map["rule_element"],
                disabled=True,
                default=None
            ),
            "uid": st.column_config.TextColumn(
                col_title_map["uid"],
                disabled=True,
                required=True,
                default=str(uuid.uuid4())
            ),
            "_index": st.column_config.NumberColumn(
                "Index",
                disabled=True,
                pinned=False,
                default=len(st.session_state["current_df"])
            ),
        }
    )

    # Export DF
    csv = st.session_state["current_df"].to_csv(index=False)

    st.download_button(
        label="Export Updated Rule Set",
        data=csv,
        file_name='data.csv',
        mime='text/csv'
    )
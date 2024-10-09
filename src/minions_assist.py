import _snowflake
import json
import streamlit as st
import shap
import io
import pandas as pd
from snowflake.snowpark.context import get_active_session
import plotly.express as px
import plotly.graph_objects as go

# Configuration Constants
DATABASE = "TEST1"
SCHEMA = "PUBLIC"
STAGE = "CUSTOMER"
FILE = "customer.yaml"

def send_message(prompt: str) -> dict:
    """Calls Snowflake Cortex AI API and returns the response."""
    request_body = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "semantic_model_file": f"@{DATABASE}.{SCHEMA}.{STAGE}/{FILE}",
    }
    resp = _snowflake.send_snow_api_request(
        "POST",
        f"/api/v2/cortex/analyst/message",
        {},
        {},
        request_body,
        {},
        30000,
    )
    if resp["status"] < 400:
        return json.loads(resp["content"])
    else:
        raise Exception(
            f"Failed request with status {resp['status']}: {resp}"
        )

def process_message(prompt: str) -> None:
    """Processes a message and adds the response to the chat."""
    st.session_state.messages.append(
        {"role": "user", "content": [{"type": "text", "text": prompt}]}
    )
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Generating response..."):
            response = send_message(prompt=prompt)
            content = response["message"]["content"]
            display_content(content=content)
    st.session_state.messages.append({"role": "assistant", "content": content})

def explain_model_prediction(model, df):
    """Generates SHAP explanation for the model's predictions."""
    explainer = shap.Explainer(model, df)
    shap_values = explainer(df)
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot(shap.summary_plot(shap_values, df))

def display_content(content: list, message_index: int = None) -> None:
    """Displays a content item for a message."""
    message_index = message_index or len(st.session_state.messages)
    
    # Loop through the content items
    for item in content:
        if item["type"] == "text":
            st.markdown(item["text"])
        
        elif item["type"] == "suggestions":
            with st.expander("Suggestions", expanded=True):
                for suggestion_index, suggestion in enumerate(item["suggestions"]):
                    if st.button(suggestion, key=f"{message_index}_{suggestion_index}"):
                        st.session_state.active_suggestion = suggestion

        elif item["type"] == "sql":
            with st.expander("SQL Query", expanded=False):
                st.code(item["statement"], language="sql")

            with st.expander("Results", expanded=True):
                with st.spinner("Running SQL..."):
                    session = get_active_session()
                    df = session.sql(item["statement"]).to_pandas()
                    st.session_state.dataframe = df

                    # Display summary
                    st.markdown(summarize_data(df))

                    # Download button for the dataset
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                    label="Download data as CSV",
                    data=csv,
                    file_name='query_results.csv',
                    mime='text/csv',
                    key=f"download_button_{message_index}"
                    
                    )

                    # Visualizations in separate tabs
                    data_tab, line_tab, bar_tab = st.tabs(
                        ["Data", "Line Chart", "Bar Chart"]
                    )
                    data_tab.dataframe(df)
                    
                    if len(df.columns) > 1:
                        df = df.set_index(df.columns[0])

                    with line_tab:
                        fig = px.line(df)
                        st.plotly_chart(fig)
                        st.markdown(generate_explanation("line", df))

                    with bar_tab:
                        fig = px.bar(df)
                        st.plotly_chart(fig)
                        st.markdown(generate_explanation("bar", df))

            # Explainable AI support
            if 'Explainable AI' in content:
                with st.expander("Explainable AI", expanded=True):
                    explain_model_prediction(trained_model, df)

def generate_explanation(chart_type: str, df: pd.DataFrame) -> str:
    """Generates explanations for visualizations."""
    if chart_type == "line":
        explanation = (
            "### Line Chart Explanation\n"
            "This line chart shows trends over time. Each line represents a different variable from the data. "
            "Look for upward or downward trends to analyze performance or changes in the data. "
            "For example, if you see a consistent upward trend, it indicates growth in that area."
        )
    elif chart_type == "bar":
        explanation = (
            "### Bar Chart Explanation\n"
            "This bar chart compares different categories. Each bar represents a different segment of the data. "
            "The height of the bars indicates the magnitude of the values, making it easy to compare categories directly. "
            "For instance, a taller bar signifies a larger value in that category compared to others."
        )
    else:
        explanation = "No explanation available for this chart type."

    # Customize explanation based on specific data if needed
    # Example: Check the data in df to provide specific insights
    return explanation

def summarize_data(df):
    """Summarizes the DataFrame content."""
    summary = f"### Data Summary\n\n"
    summary += f"- **Number of rows**: {df.shape[0]}\n"
    summary += f"- **Number of columns**: {df.shape[1]}\n\n"
    
    # Numeric columns summary
    numeric_cols = df.select_dtypes(include='number')
    if not numeric_cols.empty:
        summary += "#### Numeric Columns Summary:\n\n"
        summary += numeric_cols.describe().to_markdown()  # Converts to markdown
    
    # Categorical columns summary
    categorical_cols = df.select_dtypes(include='object')
    if not categorical_cols.empty:
        summary += "\n\n#### Categorical Columns Summary:\n\n"
        for col in categorical_cols.columns:
            summary += f"- **{col}**: {df[col].nunique()} unique values\n"
            top_value = df[col].value_counts().idxmax()
            top_freq = df[col].value_counts().max()
            summary += f"  - Most frequent: {top_value} ({top_freq} occurrences)\n"

    return summary

st.title("Minions_Assist: Talk to Data")
st.markdown(f"Semantic Model: `{FILE}`")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.suggestions = []
    st.session_state.active_suggestion = None

# Display past messages
for message_index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        display_content(content=message["content"], message_index=message_index)

# Input for new message
if user_input := st.chat_input("Ask your question to the data:"):
    process_message(prompt=user_input)

# Process any active suggestions
if st.session_state.active_suggestion:
    process_message(prompt=st.session_state.active_suggestion)
    st.session_state.active_suggestion = None

# Example questions and corresponding SQL queries
example_questions = {
    "What is the summary of the customer data?": "SELECT * FROM CUSTOMER_DATA;",
    "What is the distribution of customers across different market segments?": 
        "SELECT C_MKTSEGMENT, COUNT(*) as count FROM CUSTOMER_DATA GROUP BY C_MKTSEGMENT;",
    "What are the statistics of account balances among customers?": 
        "SELECT C_ACCTBAL FROM CUSTOMER_DATA;",
    "Can you show the number of customers in each nation?": 
        "SELECT C_NATIONKEY, COUNT(*) as count FROM CUSTOMER_DATA GROUP BY C_NATIONKEY;",
    "Who are the top 5 customers with the highest account balances?": 
        "SELECT C_CUSTKEY, C_NAME, C_ACCTBAL FROM CUSTOMER_DATA ORDER BY C_ACCTBAL DESC LIMIT 5;",
    "What are the details of customers who have an account balance greater than 1000?": 
        "SELECT * FROM CUSTOMER_DATA WHERE C_ACCTBAL > 1000;",
    "Can you analyze the comments provided by customers for common themes?": 
        "SELECT C_COMMENT FROM CUSTOMER_DATA;",
    "What are the unique phone numbers of customers?": 
        "SELECT DISTINCT C_PHONE FROM CUSTOMER_DATA;"
}

# Display example questions
st.sidebar.header("Example Questions")
for question, query in example_questions.items():
    if st.sidebar.button(question):
        process_message(prompt=question)

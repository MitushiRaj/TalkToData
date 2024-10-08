# Minions Assist - "TALK TO DATA"
## Description

## Getting Started
### Snowflake Trial Account
1. Navigate to https://signup.snowflake.com to create your trial account
2. Fill in your personal details and proceed to next page
3. Select the settings on the right hand side:
    - Edition: Business Critical
    - Cloud Provider: AWS
    - Region: EU (Frankfurt)
4. You will receive a confirmation e-mail with a link to activate your account

### Database Connectivity:
1. Login to SnowFlake account, Under Data - Go to Databases
2. Establish connection to multiple databases ( SQL, NoSQL, cloud-based, custom database )
   
### Data for File Handling
1. Select the appropriate dataset for the use-case which you want to implement.
2. Select a database with more information for better visualization.

### Semantic Modal Generator
1. Navigate to https://github.com/Snowflake-Labs/semantic-model-generator
2. Follow the steps given in the above github link and run the Semantic Model Generator.
3. Generate a semantic (.yaml) file by providing snowflake credentials.

### Create a Stage in Database
1. Navigate to Snowflake account, Under the database connected, create a stage.
2. Upload the generated .yaml file into the stage.

### Streamlit Application
1. Now open the Streamlit application, Add the snowflake database credentials and Write the functioanlities needed for the use case
2. Once you run the application, you can check the prompts appear to "Talk To Data".
3. Select a prompt, so that it will be provide a summarized output with data visualizations, Explainable AI, Downlaod data functionalities.


    Till next time, Keep Talking to Data with Minions Assist !!

import streamlit as st
from snowflake.snowpark.functions import col

# Create connection using Streamlit's connection (ONLY method needed)
cnx = st.connection("snowflake")
session = cnx.session()

# Write directly to the app
st.title("Customize your smoothie! 🥤")
st.write('Choose the fruits you want to add to your smoothie!')

# Get fruit data using the session we created above
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'))

# Convert the dataframe to a list for the multiselect
fruit_list = my_dataframe.to_pandas()['FRUIT_NAME'].tolist()

# Add name input field
name_on_order = st.text_input('Name on Smoothie:')
if name_on_order:
    st.write('The name on your Smoothie will be:', name_on_order)

# Create multiselect with the fruit options
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_list,
    max_selections=6
)

# Only process if both name and ingredients are provided
if ingredients_list and name_on_order:
    # Convert the list to a string with spaces
    ingredients_string = ''
    
    # FOR loop to build the string with spaces
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
    
    # Remove trailing space
    ingredients_string = ingredients_string.strip()
    
    # Display order summary
    st.write('Your order:')
    st.write(f'Name: {name_on_order}')
    st.write(f'Ingredients: {ingredients_string}')
    
    # Build SQL insert statement with name - UPDATED DATABASE NAME
    my_insert_stmt = f"INSERT INTO smoothies.public.orders(ingredients, name_on_order) VALUES ('{ingredients_string}', '{name_on_order}')"
    
    # Show the SQL statement for debugging (comment out in production)
    st.write("SQL Statement:")
    st.code(my_insert_stmt)
    
    # Add submit button
    time_to_insert = st.button('Submit Order')
    
    # Execute the insert only when button is clicked
    if time_to_insert:
        try:
            session.sql(my_insert_stmt).collect()
            st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")
            
            # Kitchen notification
            st.subheader('Kitchen Order Display')
            st.info(f'Order for: {name_on_order}')
            st.info(f'Ingredients: {ingredients_string}')
        except Exception as e:
            st.error(f'Error submitting order: {e}')
elif ingredients_list and not name_on_order:
    st.warning('Please enter a name for your smoothie order.')
elif name_on_order and not ingredients_list:
    st.warning('Please select at least one ingredient.')

# New section to display smoothiefroot nutrition information
st.subheader('Nutrition Information')
import requests
smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/watermelon")
st.text(smoothiefroot_response.json())

# Convert JSON to DataFrame
import pandas as pd
sf_df = pd.json_normalize(smoothiefroot_response.json())
st.dataframe(sf_df, use_container_width=True)

# Display the fruit options dataframe for reference
st.subheader('Our fruit options')
st.dataframe(data=my_dataframe, use_container_width=True)

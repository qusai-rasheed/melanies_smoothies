import streamlit as st
import requests
import pandas as pd
from snowflake.snowpark.functions import col

# Create connection using Streamlit's connection (ONLY method needed)
cnx = st.connection("snowflake")
session = cnx.session()

# Write directly to the app
st.title("Customize your smoothie! 🥤")
st.write('Choose the fruits you want to add to your smoothie!')

# Get fruit data including the search_on column
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))

# Convert to pandas dataframe so we can use the LOC function
pd_df = my_dataframe.to_pandas()

# Create list for multiselect (still using FRUIT_NAME for display)
fruit_list = pd_df['FRUIT_NAME'].tolist()

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
    
    # FOR loop to build the string with spaces AND get nutrition data
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        
        # Get the search term for this fruit from the database using LOC function
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        st.write('The search value for ', fruit_chosen,' is ', search_on, '.')
        
        # Get nutrition data for each fruit and display immediately
        st.subheader(fruit_chosen + ' Nutrition Information')
        try:
            # Use the search_on value for the API call
            smoothiefroot_response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")
            
            if smoothiefroot_response.status_code == 200:
                fruit_data = smoothiefroot_response.json()
                sf_df = pd.json_normalize(fruit_data)
                st.dataframe(sf_df, use_container_width=True)
            else:
                st.error("Sorry, that fruit is not in our database.")
                
        except Exception as e:
            st.error("Sorry, that fruit is not in our database.")
    
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

# Display the fruit options dataframe for reference
st.subheader('Our fruit options')
st.dataframe(data=my_dataframe, use_container_width=True)

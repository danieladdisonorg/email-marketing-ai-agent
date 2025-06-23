import pandas as pd
import os 

def read_data(prospects_path, existing_customers_path):
    """_summary_

    Args:
        prospects_path (_type_): _description_
        existing_customers_path (_type_): _description_

    Returns:
        2 pd.DataFrame: prospects and pre-procecced existing_customers
    """
    try:
        prospects = pd.read_csv(prospects_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Prospects file not found at path: {prospects_path}")
    except pd.errors.EmptyDataError:
        raise ValueError(f"Prospects file at path {prospects_path} is empty")
    except Exception as e:
        raise Exception(f"An error occurred while reading the prospects file: {e}")

    try:
        existing_customers = pd.read_csv(existing_customers_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Existing customers file not found at path: {existing_customers_path}")
    except pd.errors.EmptyDataError:
        raise ValueError(f"Existing customers file at path {existing_customers_path} is empty")
    except Exception as e:
        raise Exception(f"An error occurred while reading the existing customers file: {e}")

    try:
        existing_customers = existing_customers.drop(columns=['Record Id', 'Annual Service Renew', 'Annual Service Renew', 'Important Notes', 'Payment Terms'])
    except KeyError as e:
        raise KeyError(f"One or more columns to drop do not exist in the existing customers DataFrame: {e}")
    except Exception as e:
        raise Exception(f"An error occurred while processing the existing customers DataFrame: {e}")

    return prospects, existing_customers

def find_matching_domain_emails(email, df):
    """
    Finds all email addresses in the DataFrame with the same domain as the given email and appends the associated Account Names to a list.

    Args:
        email (str): The email address to match the domain.
        df (pd.DataFrame): The DataFrame containing 'AP Email' and 'Account Name' columns.

    Returns:
        list: A list of Account Names with matching domains.
    """
    # Extract domain from the given email
    try:
        domain = email.split('@')[1]
    except IndexError:
        raise ValueError("Invalid email address")

    # Check if necessary columns exist in the DataFrame
    if 'AP Email' not in df.columns or 'Account Name' not in df.columns:
        raise ValueError("The DataFrame must contain 'AP Email' and 'Account Name' columns")

    # Initialize the organization list
    orgs = []
    flag = True

    # Filter rows with the same domain
    matching_rows = df[df['AP Email'].str.endswith(f'@{domain}', na=False)]

    # Check the number of matching rows
    if matching_rows.empty:
        print("No matching emails found, returning 2 customers.")
        # Select 2 random Account Names from the DataFrame
        flag = False
        orgs = df.sample(2)['Account Name'].tolist()
    elif len(matching_rows) == 1:
        print("Only 1 matching email found, returning 1 customer.")
        # Add the single matching Account Name and one random Account Name
        orgs = matching_rows['Account Name'].tolist()
        orgs.append(df[~df.index.isin(matching_rows.index)].sample(1)['Account Name'].values[0])
    else:
        # Add all matching Account Names
        orgs = matching_rows['Account Name'].tolist()

    return orgs, flag


def set_api_key_env(var: str, api_key: str):
    print(f"Setting {var} environment variable")
    if not os.environ.get(var):
        os.environ[var] = api_key
        
        
def get_text_from_file(file_path):
    with open(file_path, "r") as file:
        return file.read()
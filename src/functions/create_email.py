import pandas as pd
import time
from helpers.agent import email_agent, retriever

def create_email():
    """
        - Parameters: 
            - None
        
        - Returns: 
            - DataFrame
        
        - Description:  
            This function generates personalized email templates for each prospect in the prospects.csv file.
    """
    # Load the prospects CSV
    prospects = pd.read_csv("data/prospects.csv")
    zoho_emails = pd.read_csv("data/zoho_emails.csv")['Email'].tolist()
    zoho_domains = [email.split('@')[1] for email in zoho_emails]

    mail_df = pd.DataFrame(columns=["Email_address", "Subject", "Email Template Body"])

    for _, row in prospects.iterrows():
        try:
            email = row["Email"]
            first_name = row["First Name"]
            last_name = row["Last Name"]
            company_name = row["Company"] if pd.notna(row["Company"]) else "your organization"
            title = row["Title"] if pd.notna(row["Title"]) else "your team"
            target_domain = email.split('@')[1]

            generated_subject = f"Enhancing Healthcare Operations for {first_name} at {company_name}"
            
            # Check if the email needs personalization
            if target_domain in zoho_domains:
                docs = retriever.invoke(
                    f"{first_name}, {last_name}, {email}, {title}, {company_name}\n"
                    f"A sister company using our service has been identified."
                )
            else:
                docs = retriever.invoke(
                    f"{email}\nWe have success stories to share, and we'd love to collaborate with you!"
                )

            # Generate personalized email body using the AI agent
            context = "\n".join(docs)
            generated_response = email_agent.invoke(
                f"context: {context}, Generate a personalized email body for {first_name}."
            )

            generated_body = (
                generated_response.content
                .replace("\n", "<br>")
                .replace("[First Name]", first_name)
                .replace("[Company Name]", company_name)
                .replace("[Title]", title)
            )

            mail_df = pd.concat([mail_df, pd.DataFrame({
                "Email_address": [email],
                "Subject": [generated_subject],
                "Email Template Body": [generated_body]
            })])

            # Prevent hitting rate limits
            time.sleep(2)

        except Exception as e:
            print(f"Error processing {email}: {e}")

    # Save the generated emails to a CSV file
    mail_df.to_csv("data/generated_emails.csv", index=False)
    return mail_df
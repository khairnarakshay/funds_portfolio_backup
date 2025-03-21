# excel_processing.py

import pandas as pd
from django.utils.timezone import now
from .models import MutualFundData, UploadedFile
import pandas as pd
from django.shortcuts import render
from django.http import JsonResponse

import matplotlib.pyplot as plt
import io
import base64

def process_amc_excel_file(amc, scheme, file):
    """
    Determines which function to call based on the AMC.
    """
    amc_functions = {
       
        "SBI Mutual Fund" : SBI_Mutual_Fund,
        "ICICI Prudential Mutual Fund" : ICICI_Prudential_Mutual_Fund,

        "Baroda BNP Paribas Mutual Fund" : 	Baroda_BNP_Paribas_Mutual_Fund,  
         "DSP Mutual Fund" : DSP_Mutual_Fund,
        
       
    }
    print(f"Processing AMC: {amc.name}")
    processing_function = amc_functions.get(amc.name, default_excel_processing)
    processing_function(file, scheme,amc)
    print(amc.name)


def safe_strip(value):
    """Convert to string and strip if it's not NaN."""
    if isinstance(value, str):
        return value.strip()
    return str(value) if pd.notna(value) else ''  # Convert NaN to empty string

def SBI_Mutual_Fund(file, scheme, amc):
    print(amc.name)
    print(f'scheme name :{scheme.scheme_name}')
    
    print("Processing Excel file for AMC and updating the existing data in MutualFundData.")

    try:
        df = pd.read_excel(file, header=5)
        df.columns = df.columns.str.strip()  # Clean column names
        df.columns = df.columns.str.replace('\n', ' ', regex=True)
        #df['Market Value (Rs. In Lakhs)'] = pd.to_numeric(df['Market value (Rs. in Lakhs)'], errors='coerce').fillna(0)
        
        market_value_col = next((col for col in df.columns if col.lower().startswith("market value")), None)

        if market_value_col:
            df[market_value_col] = pd.to_numeric(df[market_value_col], errors='coerce').fillna(0)
        else:
            print("Error: Market value column not found!")
            

        print("Available columns:", df.columns.tolist()) 
        # Replace "NIL" with 0 and fill missing values for numeric columns
        df.replace("NIL", 0, inplace=True)
        df.fillna({
         'Quantity': 0,
         'Market value (Rs. in Lakhs)': 0,
         '% to AUM': 0,
         'YTC %##': 0,
         'YTM %': 0,
         'ISIN': '',
        }, inplace=True)
        
        if 'Quantity' in df.columns:
            df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0)
        elif 'Quantity/Face Value' in df.columns:
            df['Quantity/Face Value'] = pd.to_numeric(df['Quantity/Face Value'], errors='coerce').fillna(0)
            df.rename(columns={'Quantity/Face Value': 'Quantity'}, inplace=True)
            
      
        
        # Replace '#' or other non-numeric values with NaN
        df['% to AUM'] = pd.to_numeric(df['% to AUM'], errors='coerce').fillna(0)

        
        df['YTM %'] = pd.to_numeric(df['YTM %'], errors='coerce').fillna(0)
        
        if 'YTM %' in df.columns:
            df['YTM %'] = df['YTM %'].astype(str).str.rstrip('%').replace('nan', None)
            df['YTM %'] = pd.to_numeric(df['YTM %'], errors='coerce').fillna(0)
            
        
        # Check if the uploaded file already exists in the database
        uploaded_file = UploadedFile.objects.filter(amc=amc, scheme=scheme).first()

        deleted_count, _ = MutualFundData.objects.filter(scheme=scheme).delete()
        if deleted_count > 0:
            print(f"Deleted {deleted_count} existing records for scheme: {scheme.scheme_name}")
        
        # Initialize individual category totals
        
        equity_total = 0
        debt_total = 0
        money_market_total = 0
        others_current = 0
        others_total = 0
        Other_current_assets_total = 0
       

        industry_investments = {}
        instrument_aum_percentages = []

        for index, row in df.iterrows():
            name = safe_strip(row.get('Name of the Instrument / Issuer', ''))
            lower_name = name.lower()
            
            # Detect section header rows and update current_category
             # Exit the loop immediately
            if lower_name .startswith( "grand total"):
                break 
            if lower_name.startswith('equity'):
                current_category = 'Equity'
                continue
            elif lower_name.startswith('debt'):
                current_category = 'Debt'
                continue
            elif lower_name.startswith('money market'):
                current_category = 'Money Market'
                continue
            elif lower_name.startswith('other'):
                current_category = 'Others'
                continue
            #elif lower_name.startswith('other current'):
                #continue

            if not name:
                continue

            # Check if the row contains "Total" and update category total
            if "total" in lower_name :
                
                market_value = row['Market value (Rs. in Lakhs)']
                if current_category == 'Equity':
                    
                    equity_total += market_value  # Accumulate if multiple total rows exist
                    print(f"Equity Total: {equity_total}")
                elif current_category == 'Debt':
                    debt_total += market_value
                    print(f"Debt Total: {debt_total}")
                elif current_category == 'Money Market':
                    money_market_total += market_value
                    print(f"Money Market Total: {money_market_total}")
                elif current_category == 'Others':
                    others_total += market_value
                    print(f"Others Total: {others_total}")
                elif current_category == 'Other Current': 
                    
                    Other_current_assets_total += market_value
                    print(f"Other Current Total: {Other_current_assets_total}")
                continue  # Skip processing further for "Total" row
            print(f'current category : {current_category}')
           
                
            if not name:
                continue
                
            isin = safe_strip(row.get('ISIN', ''))
            market_value = safe_strip(row.get('Market value (Rs. in Lakhs)', ''))

            if not isin :
                continue  

            instrument_type = current_category if current_category else 'Others'
            market_value = row['Market value (Rs. in Lakhs)']

            instrument = MutualFundData(
                amc=amc,
                scheme=scheme,
                instrument_name=name,
                isin=isin,
                industry_rating=safe_strip(row.get('Industry / Rating', '')),
                quantity=row['Quantity'],
                market_value=market_value,
                percentage_to_nav=row['% to AUM'],
                yield_percentage=row['YTM %'],
                ytc=row.get('YTC %##', None),
                instrument_type=instrument_type,
            )
            instrument.save()

            # Aggregate investment for industry/ratings
            industry_rating = safe_strip(row.get('Rating / Industry^', ''))
            if industry_rating:
                industry_investments[industry_rating] = industry_investments.get(industry_rating, 0) + market_value

            # Store the top 5 instruments by % to NAV
            nav_percentage = row['% to AUM']
            instrument_aum_percentages.append((name, nav_percentage, market_value))
            
            
        others_total = others_total 
        # Calculate combined Money Market and Others into one category
        combined_others_total = money_market_total + others_total + Other_current_assets_total

        # Calculate the overall total market value
        total_market_value = equity_total + debt_total + others_total + money_market_total
        total = total_market_value if total_market_value > 0 else 1

        equity_percentage = (equity_total / total) * 100
        debt_percentage = (debt_total / total) * 100
        others_percentage = (combined_others_total / total) * 100

     # Get top 5 industries by total market value
        sorted_industries = sorted(industry_investments.items(), key=lambda x: x[1], reverse=True)[:5]
        top_sectors = [{"industry": industry, "investment": round(investment, 2)} for industry, investment in sorted_industries]

        # Get top 5 instruments by % to NAV
        sorted_instruments = sorted(instrument_aum_percentages, key=lambda x: x[1], reverse=True)[:5]
        top_holdings = [{"instrument_name": instrument, "nav_percentage": round(nav_percentage, 2)} for instrument, nav_percentage, _ in sorted_instruments]

        

        print("Top Sectors:", top_sectors)
        print("Top Holdings:", top_holdings)



        print("Equity Total:", equity_total)
        print("Debt Total:", debt_total)
        print("Money Market Total:", money_market_total)
        print("Others Total:", others_total)
        print("Total Market Value:", total_market_value)
        print("Equity Percentage:", equity_percentage)
        print("Debt Percentage:", debt_percentage)
        print("Others Percentage:", others_percentage)
        print("Top Industries:", top_sectors)
        print("Top Instruments:", top_holdings)
        print("Data saved successfully!")
        
        category_totals = { 
                           'Equity': equity_total,
                           'Debt': debt_total,
                           'Money Market': money_market_total,
                           'Others': others_total,
                           'Total Market Value': total_market_value,
                            }  
        
               # Ensure uploaded file exists
        if uploaded_file:
            try:
                # Update the uploaded file with the latest totals
                print('Final Before update into DB - Others Total:', others_total)
                
                
                
                
                # Top sectors and holdings
                uploaded_file.category_total = category_totals
                uploaded_file.top_sectors = top_sectors
                uploaded_file.top_holdings = top_holdings
                
                # Save changes to the database
                uploaded_file.save()
                print('File updated successfully!')
            
            except Exception as e:
                print(f"Error updating the file: {e}")
                   
        else:
            print("No uploaded file found.")
    

    
    except Exception as e:
        print(f"Error reading Excel file: {e}")          
        
     
import re    
def ICICI_Prudential_Mutual_Fund(file, scheme, amc):
    print(amc.name)
    print(f'Scheme name: {scheme.scheme_name}')
    
    print("Processing Excel file for AMC and updating the existing data in MutualFundData.")
    
    try:
        df = pd.read_excel(file, header=3)
        df.columns = df.columns.str.strip()  # Clean column names   
        df.columns = df.columns.str.replace('\n', ' ', regex=True)
                
        market_value_col = next((col for col in df.columns if re.match(r"(?i)Exposure/Market\s?Value\(Rs\.Lakh\)", col.strip())), None)

        if market_value_col:
            df[market_value_col] = pd.to_numeric(df[market_value_col], errors='coerce').fillna(0)
        else:
            print("Market Value column not found in the Excel file.")
            return  # Exit if market value column is missing
        
        print("Available columns:", df.columns.tolist())
        
        df.replace("NIL", 0, inplace=True)
         # Replace "NIL" with 0 and fill missing values for numeric columns
        df.replace("NIL", 0, inplace=True)
        df.fillna({
         'Quantity': 0,
         'Market value (Rs. in Lakhs)': 0,
         '% to Nav': 0,
         'Yield of the instrument': 0,
         'Yield to Call @': 0,
         'ISIN': '',
        }, inplace=True)
        
        if 'Quantity' in df.columns:
            df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0)
        elif 'Quantity/Face Value' in df.columns:
            df['Quantity/Face Value'] = pd.to_numeric(df['Quantity/Face Value'], errors='coerce').fillna(0)
            df.rename(columns={'Quantity/Face Value': 'Quantity'}, inplace=True)
            
        df['% to Nav'] = pd.to_numeric(df['% to Nav'], errors='coerce').fillna(0)
        df['Yield of the instrument'] = pd.to_numeric(df['Yield of the instrument'], errors='coerce').fillna(0)
        
         # Check if the uploaded file already exists in the database
        uploaded_file = UploadedFile.objects.filter(amc=amc, scheme=scheme).first()

        deleted_count, _ = MutualFundData.objects.filter(scheme=scheme).delete()
        if deleted_count > 0:
            print(f"Deleted {deleted_count} existing records for scheme: {scheme.scheme_name}")
          

        # Initialize a category totals dictionary
        category_totals = {
            'Equity': 0,
            'Debt': 0,
            'Money Market': 0,
            'Others': 0,
            'Reverse Repo': 0,
            'Treps': 0,
            'Units of Real Estate Investment Trust (REITs)': 0,
            'Units of an Alternative Investment Fund (AIF)': 0,
            'Gold': 0,
            'Net Current Assets': 0
        }
        
        current_category = None  # Initialize category variable
        industry_investments = {}
        instrument_aum_percentages = []
       

        # Define category mapping (lowercased for optimized lookup)
        category_mapping = {
            "equity & equity related instruments": "Equity",
            "debt": "Debt",
            "money market": "Money Market",
            "reverse repo": "Reverse Repo",
            "treps": "Treps",
            "gold": "Gold",
            "units of real estate investment trust (reits)": "Units of Real Estate Investment Trust (REITs)",
            "units of an alternative investment fund (aif)": "Units of an Alternative Investment Fund (AIF)",
            "net current assets": "Net Current Assets",
            "others": "Others",
            "units of mutual funds": "Units of Mutual Funds"
        }

        category_mapping = {k.lower(): v for k, v in category_mapping.items()}  # Convert keys to lowercase

        # Initialize category-related variables
        category_totals = {v: 0 for v in category_mapping.values()}
        current_category = None  

        # Identify the correct Market Value column dynamically
        market_value_col = next((col for col in df.columns if re.match(r"(?i)Exposure/Market\s?Value\(Rs\.Lakh\)", col.strip())), None)
        if not market_value_col:
            print("Market Value column not found.")
            return  # Exit if the required column is missing

        # Loop through rows once, optimizing category detection
        for index, row in df.iterrows():
            name = str(row.get('Company/Issuer/Instrument Name', '')).strip().lower()

            # Stop processing when 'Total Net Assets' is encountered
            if "total net assets" in name:
                print("Reached 'Total Net Assets' row. Stopping processing.")
                break

            # Extract Market Value and convert safely
            market_value = pd.to_numeric(row.get(market_value_col, 0), errors='coerce')
            market_value = 0 if pd.isna(market_value) else market_value  # Handle NaN cases
            #skip blanck row 
            
            # if not name:
            #     continue
            #skip line where quantity is not present 
            # quantity = row.get('Quantity', '')
            # if not quantity:
            #     continue
            
            # **Ensure `key` is always defined within the loop**
            for key, category in category_mapping.items():
                key_lower = key.lower().strip()  # Normalize key
                if key_lower == "reverse repo":
                    # **Exact match for "Reverse Repo" only**
                    if name.strip() == key:
                        current_category = category
                        category_totals[current_category] = market_value
                        print(f"Exact Match Found: {current_category}, Market Value: {market_value}")
                        break  # Exit loop after match
                elif key_lower == "gold":
                    if name.startswith("gold "):  # **Only match "Gold" at the start**
                        current_category = category
                        category_totals[current_category] = market_value
                        print(f"Gold Category Assigned: {current_category}, Market Value: {market_value}")
                        break
                elif key_lower == "debt":
                    if name.startswith("debt "):  # **Only match "Debt" at the start**
                        current_category = category
                        category_totals[current_category] = market_value
                        print(f"Debt Category Assigned: {current_category}, Market Value: {market_value}")
                        break
                elif key_lower == "units of an alternative investment fund (aif)":
                    if name == key_lower:  # **Full case-insensitive match**
                        current_category = category
                        category_totals[current_category] = market_value
                        print(f"AIF Category Assigned: {current_category}, Market Value: {market_value}")
                        break
                elif key_lower == "units of real estate investment trust (reits)":
                    if name == key_lower:  # **Exact match for REITs**
                        current_category = category
                        category_totals[current_category] = market_value
                        print(f"REITs Category Assigned: {current_category}, Market Value: {market_value}")
                        break
                else:
                    # **Full-word match for all other categories**
                    pattern = r'\b' + re.escape(key) + r'\b'
                    if re.search(pattern, name):  
                        current_category = category
                        category_totals[current_category] = market_value
                        print(f"Category Identified: {current_category}, Market Value: {market_value}")
                        break  # Exit loop after match

            # Process valid data rows (excluding category headers)
            if current_category:
                instrument_type = current_category  # Assign instrument type

            # Extract Market Value and convert safely
            market_value = pd.to_numeric(row.get(market_value_col, 0), errors='coerce')
            market_value = 0 if pd.isna(market_value) else market_value  # Handle NaN cases

           
            # Collect data for industry and instrument AUM
            industry = safe_strip(row.get('Industry / Rating', ''))
            if industry:
                industry_investments[industry] = industry_investments.get(industry, 0) + row[market_value_col]

            instrument_name = name
            nav_percentage = row.get('% to Nav', 0)
            instrument_aum_percentages.append((instrument_name, nav_percentage, row[market_value_col]))

            # Insert data into the database
            instrument_type = current_category if current_category else 'Others'
            instrumnet = MutualFundData(
                amc=amc,
                scheme=scheme,
                instrument_name=name,
                isin=safe_strip(row.get('ISIN', '')),
                industry_rating=safe_strip(row.get('Industry / Rating', '')),
                quantity=row['Quantity'],
                market_value=row[market_value_col],  # Store actual market value, not the column name
                percentage_to_nav=row['% to Nav'],
                yield_percentage=row['Yield of the instrument'],
                ytc=row.get('Yield to Call @', None),
                instrument_type=instrument_type,
            )
            instrumnet.save()
        
        total_market_value = sum(category_totals.values())    
        print('Category Totals:', category_totals)
        print('Total market value:', total_market_value )
        final_others_total = sum(value for key, value in category_totals.items() if key not in ["Equity", "Debt"])

        final_category_total = {
            "Equity" : category_totals["Equity"],
            "Debt" : category_totals["Debt"],
            "Others" : final_others_total,
            "Total Market value ": sum(category_totals.values())
        }
        
        # Get top 5 industries by total market value
        # Filter out rows where 'ISIN' is empty
        
        
       # Initialize lists to hold industry and instrument data
        industry_investments = {}
        instrument_aum_percentages = []

        # Loop over each row in the dataframe
        for _, row in df.iterrows():
            # Check if ISIN is blank or missing, skip the row if ISIN is blank or NaN
            if pd.isna(row['ISIN']) or row['ISIN'] == '':
                continue  # Skip this row if ISIN is blank or missing
            
            # Extract industry and market value data for top 5 industries
            industry = row['Industry/Rating']
            market_value = row['Exposure/Market Value(Rs.Lakh)']
            if industry in industry_investments:
                industry_investments[industry] += market_value
            else:
                industry_investments[industry] = market_value
            
            # Extract instrument and NAV percentage data for top 5 instruments
            instrument_name = row['Company/Issuer/Instrument Name']
            nav_percentage = row.get('% to Nav', 0)
            instrument_aum_percentages.append((instrument_name, nav_percentage, row['Exposure/Market Value(Rs.Lakh)']))

        # Get top 5 industries by total market value
        sorted_industries = sorted(industry_investments.items(), key=lambda x: x[1], reverse=True)[:5]
        top_sectors = [{"industry": industry, "investment": round(investment, 2)} for industry, investment in sorted_industries]

        # Get top 5 instruments by % to NAV
        sorted_instruments = sorted(instrument_aum_percentages, key=lambda x: x[1], reverse=True)[:5]
        top_holdings = [{"instrument_name": instrument, "nav_percentage": round(nav_percentage, 2)} for instrument, nav_percentage, _ in sorted_instruments]

        # Print results
        
        


        if uploaded_file:
            print("file uploded....")
            try:
                # Update the uploaded file with the latest totals
                # Top sectors and holdings
                uploaded_file.category_total = final_category_total
                uploaded_file.top_sectors = top_sectors
                uploaded_file.top_holdings = top_holdings
                
                # Save changes to the database
                uploaded_file.save()
                print('File updated successfully!')
            
            except Exception as e:
                print(f"Error updating the file: {e}")
        else :
            print("No file uploaded")

    except Exception as e:
        print(f"Error reading Excel file: {e}")


def Baroda_BNP_Paribas_Mutual_Fund(file , scheme , amc):

    print(amc.name)
    print(f'Scheme Name: {scheme.scheme_name}')
    print("Processing Excel file for AMC and updating the existing data in MutualFundData.")

    try:
        df = pd.read_excel(file, header=3)
        df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)
        
        print("Columns in Excel:", df.columns.tolist())  # Debugging step

        # Ensure correct column names
        expected_col_name = "Market/Fair Value (Rs. in Lakhs)"
        standardized_col_name = "Market Value (Rs. In Lakhs)"

        if expected_col_name in df.columns:
            df.rename(columns={expected_col_name: standardized_col_name}, inplace=True)

        df.replace("NIL", 0, inplace=True)
        df.fillna({
            standardized_col_name: 0,
            "Quantity": 0,
            "% to Net Assets": 0,
            "ISIN": "",
        }, inplace=True)

        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
        df[standardized_col_name] = pd.to_numeric(df[standardized_col_name], errors="coerce").fillna(0)
        df["% to Net Assets"] = pd.to_numeric(df["% to Net Assets"], errors="coerce").fillna(0) * 100 
    
        # Check if the uploaded file exists
        uploaded_file = UploadedFile.objects.filter(amc=amc, scheme=scheme).first()
        
        # Delete old records for the scheme
        deleted_count, _ = MutualFundData.objects.filter(scheme=scheme).delete()
        if deleted_count > 0:
            print(f"Deleted {deleted_count} records for scheme {scheme.scheme_name}")
        
        current_category = None
        industry_investments = {}
        instrument_list = []
        category_totals = {
            "Equity": 0,
            "Debt": 0,
            "Gold" : 0,
            "Derivatives": 0,
            "Money Market": 0,
            "Others": 0,
            "Net Receivables": 0,
            "Reverse Repo": 0
        }

        for index, row in df.iterrows():
            name = safe_strip(str(row.get("Name of the Instrument", "")).strip().lower())
            
            if 'grand total' in name:
                break
            if not name or "subtotal" in name or "sub total" in name:
                continue

            if name.startswith('equity'):
                current_category = "Equity"
                continue
            elif name.startswith('debt'):
                current_category = "Debt"
                continue
            elif name.startswith('derivatives'):
                current_category = "Derivatives"
                continue
            elif name.startswith('money market'):
                current_category = "Money Market"
                continue
            elif name.startswith('others'):
                current_category = "Others"
                continue  
            elif name.startswith('net receivables'):
                category_totals["Net Receivables"] = row.get(standardized_col_name, 0)
                continue
            elif name.startswith('reverse repo'):
                current_category = "Reverse Repo"
                continue

            if "total" in name:
                market_value = row[standardized_col_name]
                if current_category:
                    category_totals[current_category] += market_value
                print(f"Category: {current_category} Total: {market_value}")
                continue

            
            quantity = safe_strip(str(row.get("Quantity", 0)))
            isin = safe_strip(str(row.get("ISIN", "")).strip())
            if not quantity:
                continue
            
           
            
            instrument_type = current_category if current_category else "Others"
            market_value = row[standardized_col_name]
            if not market_value:
                continue
            #convert column name of diffrent format into one format  with possible matches
            industry_rating = str(row.get("Industry / Rating", row.get("Industry", row.get("Rating","")))).strip()
            # Save record to database
            instrument = MutualFundData(
                amc=amc,
                scheme=scheme,
                instrument_name=name.title(),
                isin=isin,
                industry_rating=industry_rating,
                quantity=row.get("Quantity", 0),
                market_value=market_value,
                percentage_to_nav=row.get("% to Net Assets", 0),
                instrument_type=instrument_type,
            )
            instrument.save()
            
            if not isin :
                continue
            # Aggregate investment for industry/ratings
        
            #industry_rating = industry_rating.strip()
            # if industry_rating:
            #     industry_investments[industry_rating] = industry_investments.get(industry_rating, 0) + market_value
            if 'nan' not in industry_rating :
                if industry_rating:
                    industry_investments[industry_rating] = industry_investments.get(industry_rating, 0) + market_value

            # Store the top 5 instruments by % to NAV
            nav_percentage = row["% to Net Assets"]
            print(f"Nav Percentage: {nav_percentage}")
            instrument_list.append((name, nav_percentage, market_value))
        #calculate combined money market and others into one category
        final_others_total = sum(value for key, value in category_totals.items() if key not in ["Equity", "Debt"])

        final_category_total = {
            "Equity" : category_totals["Equity"],
            "Debt" : category_totals["Debt"],
            "Others" : final_others_total,
            "Total Market value ": sum(category_totals.values())
        }
        # get top 5 industries by total market value
        
        sorted_industries = sorted(industry_investments.items(), key=lambda x: x[1], reverse=True)[:5]
        top_sectors = [{"industry": industry, "investment": round(investment, 2)} for industry, investment in sorted_industries]
        print(top_sectors)

        # get top 5 instruments by % to NAV
        sorted_instruments = sorted(instrument_list, key=lambda x: x[1], reverse=True)[:5]
        top_holdings = [{"instrument_name": instrument, "nav_percentage": round(nav_percentage, 2)} for instrument, nav_percentage, _ in sorted_instruments]
        print(top_holdings)

        # Print category totals for debugging
        total_market_value = sum(category_totals.values())
        print('++++++++++++++++++++++++++++++++++++++++')
        for category, total in category_totals.items():
            print(f"{category} Total: {total}")
        print("Total Market Value:", total_market_value)
        print('++++++++++++++++++++++++++++++++++++++++')
        print()

        
        if uploaded_file:
            try:
                uploaded_file.category_total = final_category_total
                uploaded_file.top_sectors = top_sectors
                uploaded_file.top_holdings = top_holdings
                uploaded_file.save()
            except Exception as e:
                print(f"Error updating the file: {e}")
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        
#---------------------------------------------------------------------
def DSP_Mutual_Fund(file , scheme , amc):

    print(amc.name)
    print(f'Scheme Name: {scheme.scheme_name}')
    print("Processing Excel file for AMC and updating the existing data in MutualFundData.")

    try:
        df = pd.read_excel(file, header=3)
        df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)
        
        print("Columns in Excel:", df.columns.tolist())  # Debugging step

        # Ensure correct column names
        expected_col_name = "Market value (Rs. In lakhs)"
        standardized_col_name = "Market Value (Rs. In Lakhs)"

        if expected_col_name in df.columns:
            df.rename(columns={expected_col_name: standardized_col_name}, inplace=True)

        df.replace("NIL", 0, inplace=True)
        df.fillna({
            standardized_col_name: 0,
            "Quantity": 0,
            "% to Net Assets": 0,
            "ISIN": "",
        }, inplace=True)

        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
        df[standardized_col_name] = pd.to_numeric(df[standardized_col_name], errors="coerce").fillna(0)
        df["% to Net Assets"] = pd.to_numeric(df["% to Net Assets"], errors="coerce").fillna(0) * 100 
    
        # Check if the uploaded file exists
        uploaded_file = UploadedFile.objects.filter(amc=amc, scheme=scheme).first()
        
        # Delete old records for the scheme
        deleted_count, _ = MutualFundData.objects.filter(scheme=scheme).delete()
        if deleted_count > 0:
            print(f"Deleted {deleted_count} records for scheme {scheme.scheme_name}")
        
        current_category = None
        industry_investments = {}
        instrument_list = []
        category_totals = {
            "Equity": 0,
            "Debt": 0,
            "Gold" : 0,
            "Derivatives": 0,
            "Money Market": 0,
            "Others": 0,
           # "Net Receivables": 0,
            #"Reverse Repo": 0
            "Government Securities (Central/State)" : 0,
            "Cash & Cash Equivalent" : 0 ,
        }

        for index, row in df.iterrows():
            name = safe_strip(str(row.get("Name of Instrument", "")).strip().lower())
            
            if 'grand total' in name:
                break
            # if not name or "subtotal" in name or "sub total" in name:
            #     continue

            if name.startswith('equity'):
                current_category = "Equity"
                continue
            elif name.startswith('debt'):
                current_category = "Debt"
                continue
            elif name.startswith('gold'):
                current_category = "Gold"
                continue
            elif name.startswith('derivatives'):
                current_category = "Derivatives"
                continue
            elif name.startswith('money market'):
                current_category = "Money Market"
                continue
            elif name.startswith('others'):
                current_category = "Others"
                continue  
            # elif name.startswith('net receivables'):
            #     category_totals["Net Receivables"] = row.get(standardized_col_name, 0)
            #     continue
            elif name.startswith('reverse repo'):
                current_category = "Reverse Repo"
                continue
            elif name.startswith('government securities'):
                current_category = "Government Securities (Central/State)"
                continue

            if "total" in name:
                market_value = row[standardized_col_name]
                if current_category:
                    category_totals[current_category] += market_value
                print(f"Category: {current_category} Total: {market_value}")
                continue

            
            quantity = safe_strip(str(row.get("Quantity", 0)))
            isin = safe_strip(str(row.get("ISIN", "")).strip())
            if not quantity:
                continue
            
           
            
            instrument_type = current_category if current_category else "Others"
            market_value = row[standardized_col_name]
            if not market_value:
                continue
            #convert column name of diffrent format into one format  with possible matches
            industry_rating = str(row.get("Industry / Rating",row.get("Rating/Industry" ,row.get("Industry", row.get("Rating",""))))).strip()
            # Save record to database
            instrument = MutualFundData(
                amc=amc,
                scheme=scheme,
                instrument_name=name.title(),
                isin=isin,
                industry_rating=industry_rating,
                quantity=row.get("Quantity", 0),
                market_value=market_value,
                percentage_to_nav=row.get("% to Net Assets", 0),
                instrument_type=instrument_type,
            )
            instrument.save()
            
            if not isin :
                continue
            # Aggregate investment for industry/ratings
        
            #industry_rating = industry_rating.strip()
            # if industry_rating:
            #     industry_investments[industry_rating] = industry_investments.get(industry_rating, 0) + market_value
            if 'nan' not in industry_rating :
                if industry_rating:
                    industry_investments[industry_rating] = industry_investments.get(industry_rating, 0) + market_value

            # Store the top 5 instruments by % to NAV
            nav_percentage = row["% to Net Assets"]
            #print(f"Nav Percentage: {nav_percentage}")
            instrument_list.append((name, nav_percentage, market_value))
        #calculate combined money market and others into one category
        final_others_total = sum(value for key, value in category_totals.items() if key not in ["Equity", "Debt"])

        final_category_total = {
            "Equity" : category_totals["Equity"],
            "Debt" : category_totals["Debt"],
            "Others" : final_others_total,
            "Total Market value ": sum(category_totals.values())
        }
        # get top 5 industries by total market value
        
        sorted_industries = sorted(industry_investments.items(), key=lambda x: x[1], reverse=True)[:5]
        top_sectors = [{"industry": industry, "investment": round(investment, 2)} for industry, investment in sorted_industries]
        print(top_sectors)

        # get top 5 instruments by % to NAV
        sorted_instruments = sorted(instrument_list, key=lambda x: x[1], reverse=True)[:5]
        top_holdings = [{"instrument_name": instrument, "nav_percentage": round(nav_percentage, 2)} for instrument, nav_percentage, _ in sorted_instruments]
        print(top_holdings)

        # Print category totals for debugging
        total_market_value = sum(category_totals.values())
        print('++++++++++++++++++++++++++++++++++++++++')
        for category, total in category_totals.items():
            print(f"{category} Total: {total}")
        print("Total Market Value:", total_market_value)
        print('++++++++++++++++++++++++++++++++++++++++')

        
        if uploaded_file:
            try:
                uploaded_file.category_total = final_category_total
                uploaded_file.top_sectors = top_sectors
                uploaded_file.top_holdings = top_holdings
                uploaded_file.save()
            except Exception as e:
                print(f"Error updating the file: {e}")
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        
#----------------------------------------------------------------------

def default_excel_processing(file, scheme, amc):
    """
    Default function for AMCs without specific processing logic.
    """
    print(f"Default processing for {scheme.scheme_name}. No specific function defined.")



# import requests
# from upload_excel.models import AMC, MutualFundScheme

# AMFI_URL = "https://www.amfiindia.com/spages/NAVAll.txt"

# def fetch_mutual_fund_schemes():
#     response = requests.get(AMFI_URL)
#     if response.status_code == 200:
#         data = response.text.splitlines()
#         amc_schemes = {}
#         current_amc = None

#         for line in data:
#             if line.strip() == "" or "Open Ended Schemes" in line:
#                 continue
            
#             if not line[0].isdigit():  
#                 current_amc = line.strip()
#                 amc_schemes[current_amc] = []
#             else:
#                 scheme_details = line.split(";")
#                 if len(scheme_details) > 1:
#                     scheme_name = scheme_details[3].strip()
#                     amc_schemes[current_amc].append(scheme_name)

#         return amc_schemes
#     else:
#         print("Failed to fetch data from AMFI.")
#         return {}

# def save_amc_data():
#     amc_data = fetch_mutual_fund_schemes()
#     for amc_name, schemes in amc_data.items():
#         amc_obj, created = AMC.objects.get_or_create(name=amc_name)
#         for scheme in schemes:
#             MutualFundScheme.objects.get_or_create(amc=amc_obj, scheme_name=scheme)
#     print("AMC & Mutual Fund Schemes Updated in Database!")


import requests
from upload_excel.models import AMC, MutualFundScheme

AMFI_URL = "https://www.amfiindia.com/spages/NAVAll.txt"

def fetch_mutual_fund_schemes():
    response = requests.get(AMFI_URL)
    if response.status_code == 200:
        data = response.text.splitlines()
        amc_schemes = {}
        current_amc = None

        for line in data:
            line = line.strip()
            if not line or "Open Ended Schemes" in line:
                continue  # Skip empty lines and headers

            # Identify AMC Names (non-numeric lines)
            if not line[0].isdigit():  
                current_amc = line.strip()
                if current_amc not in amc_schemes:
                    amc_schemes[current_amc] = []  # Initialize list for schemes
            else:
                # Extract scheme details safely
                scheme_details = line.split(";")
                if len(scheme_details) >= 4:  # Ensure enough fields exist
                    scheme_name = scheme_details[3].strip()
                    if scheme_name:  # Avoid empty scheme names
                        amc_schemes[current_amc].append(scheme_name)

        return amc_schemes
    else:
        print(" Failed to fetch data from AMFI.")
        return {}

def save_amc_data():
    amc_data = fetch_mutual_fund_schemes()
    for amc_name, schemes in amc_data.items():
        if amc_name:  # Ensure valid AMC names
            amc_obj, created = AMC.objects.get_or_create(name=amc_name)
            for scheme in schemes:
                MutualFundScheme.objects.get_or_create(amc=amc_obj, scheme_name=scheme)
    print(" AMC & Mutual Fund Schemes Updated in Database!")

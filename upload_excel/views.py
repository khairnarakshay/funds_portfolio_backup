# from django.shortcuts import render, redirect
from django.http import HttpResponse
import matplotlib.pyplot as plt
from django.http import JsonResponse
from django.utils.timezone import now
from .models import UploadedFile, AMC, MutualFundScheme, MutualFundData
from .forms import UploadFileForm
from .excel_processing import process_amc_excel_file
from django.shortcuts import render, redirect

def upload_file_view(request):
    amcs = AMC.objects.all()
    
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            amc = form.cleaned_data["amc"]  # Get selected AMC
            scheme = form.cleaned_data["scheme"]  # Get selected Scheme
            uploaded_file = form.cleaned_data["file"]  # Get uploaded file

            # Check if an entry already exists for the same Scheme
            existing_entry = UploadedFile.objects.filter(scheme=scheme).first()

            if existing_entry:
                # Update the existing entry (Replace old file & update date)
                existing_entry.file = uploaded_file
               
                timestamp = now().strftime('%Y-%m-%d %H:%M:%S')
                existing_entry.update_logs = f"[{timestamp}],\n" + (existing_entry.update_logs or "") 
                existing_entry.save()
            else:
                # Create a new entry if it doesn’t exist
                UploadedFile.objects.create(
                    amc=amc,
                    scheme=scheme,
                    file=uploaded_file,
                    update_logs=now(),
                )

             # Trigger processing function based on AMC
            process_amc_excel_file(amc, scheme, uploaded_file)
            
            
            updated_entry = UploadedFile.objects.filter(scheme=scheme).first()   
             # Prepare JSON response with selected scheme data
            result = {
                #"scheme": scheme.name,  # Assuming scheme has a name field
                #"amc": amc.name,  # Assuming AMC has a name field
                #"file_url": existing_entry.file.url if existing_entry.file else None,
                #"total_market_value": existing_entry.total_market_value,
                # "equity_total": existing_entry.equity_total,
                # "debt_total": existing_entry.debt_total,
                # "other_total": existing_entry.other_total,
                "category_total": updated_entry.category_total,
                "top_sectors": updated_entry.top_sectors,
                "top_holdings": updated_entry.top_holdings,
                "created_at": updated_entry.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                #"update_logs": existing_entry.update_logs
            }

            return JsonResponse({"data": result, "message": "Scheme data fetched successfully!"})

        print("File uploaded successfully message from view!")
            
            
            

            #return redirect("success_page")  # Redirect after successful upload
            

    else:
        form = UploadFileForm()
    
    return render(request, "upload.html", {"form": form, "amcs": amcs})


def get_schemes(request, amc_id):
    schemes = MutualFundScheme.objects.filter(amc_id=amc_id).values("id", "scheme_name")
    return JsonResponse({"schemes": list(schemes)})
    print(schemes)


def success_page(request):
     return HttpResponse('File uploaded successfully!')






   

# def process_amc_excel_file(amc, scheme, file):
#     """
#     Determines which function to call based on the AMC.
#     """
#     amc_functions = {
#         "Aditya Birla Sun Life Mutual Fund": process_48kc_excel,
#        # "AnotherAMC": process_another_amc_excel,
#     }
#     print(amc.name)
#     processing_function = amc_functions.get(amc.name, default_excel_processing)
#     processing_function(file, scheme)

# def process_48kc_excel(file, scheme):
    
#     print("Processes the Excel file for AMC  and stores data in MutualFundData.")
    
#     df = pd.read_excel(file)

#     for _, row in df.iterrows():
#         column1 = row["Column1"]
#         column2 = row["Column2"]

#         # Check if data exists for this scheme
#         existing_entry = MutualFundData.objects.filter(scheme=scheme, column1=column1).first()

#         if existing_entry:
#             existing_entry.column2 = column2
#             existing_entry.processed_at = now()
#             existing_entry.save()
#         else:
#             MutualFundData.objects.create(
#                 scheme=scheme,
#                 column1=column1,
#                 column2=column2,
#                 processed_at=now(),
#             )
#         print("Data saved successfully!")
# def default_excel_processing(file, scheme):
#     """
#     Default function for AMCs without specific processing logic.
#     """
#     print("Default processing for AMC")
#     print(f"Processing file for {scheme.scheme_name} (Default method)")
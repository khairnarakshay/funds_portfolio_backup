from .models import AMC

amc_names = [
    "HDFC Mutual Fund", "SBI Mutual Fund", "ICICI Prudential Mutual Fund", 
    "Axis Mutual Fund", "Nippon India Mutual Fund", "Kotak Mutual Fund",
    "UTI Mutual Fund", "DSP Mutual Fund", "Franklin Templeton Mutual Fund",
    "Tata Mutual Fund", "Aditya Birla Sun Life Mutual Fund", "Mirae Asset Mutual Fund"
]

for name in amc_names:
    AMC.objects.get_or_create(name=name)

print("AMCs added successfully!")

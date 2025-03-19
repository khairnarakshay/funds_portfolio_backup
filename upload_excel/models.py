from django.db import models
import datetime

class AMC(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class MutualFundScheme(models.Model):
    amc = models.ForeignKey(AMC, on_delete=models.CASCADE, related_name="schemes")
    scheme_name = models.CharField(max_length=255)

    def __str__(self):
        return self.scheme_name

class UploadedFile(models.Model):
    amc = models.ForeignKey(AMC, on_delete=models.CASCADE)
    scheme = models.ForeignKey(MutualFundScheme, on_delete=models.CASCADE,default= 1)
    file = models.FileField(upload_to="uploads/")
    #new added fields
    
    # total_market_value = models.FloatField(default=0)
    # equity_total = models.FloatField(default=0)
    # debt_total = models.FloatField(default=0)
    # other_total = models.FloatField(default=0)
    top_sectors = models.JSONField(default=dict, blank=True)
    top_holdings = models.JSONField(default=dict, blank=True)
    category_total = models.JSONField( default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
        
    update_logs = models.TextField(blank=True, null=True)
    
    

    def add_log(self):
        """Function to add a timestamp log."""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}],\n"

        # Append the new log entry to existing logs
        self.update_logs = (self.update_logs or "") + log_entry
        self.save()
    
    def __str__(self):
        return f"{self.file.name} "
    

class MutualFundData(models.Model):
    """
    Stores processed data from the Excel file.
    """
    amc = models.ForeignKey(AMC, on_delete=models.CASCADE, null=True) 
    scheme = models.ForeignKey(MutualFundScheme, on_delete=models.CASCADE, null=True)
    
    processed_at = models.DateField(auto_now=True)
    file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, null=True)
    #new added fields
    instrument_name = models.CharField(max_length=255, null=True)
    industry_rating = models.CharField(max_length=255 , null=True)
    quantity = models.IntegerField(null=True, blank=True)
    market_value = models.FloatField(null=True, blank=True)

    percentage_to_nav = models.FloatField( null=True)
    isin = models.CharField(max_length=50, null=True)
    yield_percentage = models.FloatField(null=True, blank=True)
    ytc = models.FloatField(null=True, blank=True)
    instrument_type = models.CharField(max_length=50 , null=True)  # Equity, Debt, Money Market, etc.
    
    
    
    
    

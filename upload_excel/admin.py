from django.contrib import admin
from.models import UploadedFile, AMC , MutualFundScheme , MutualFundData
from django.utils.safestring import mark_safe
# Register your models here.

class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('amc', 'scheme', 'file', 'category_total',  'display_top_sectors', 'display_top_holdings', 'created_at', 'update_logs')

    def display_top_sectors(self, obj):
        return mark_safe(f"<pre>{obj.top_sectors}</pre>") if obj.top_sectors else "No Data"
    display_top_sectors.short_description = "Top Sectors"

    def display_top_holdings(self, obj):
        return mark_safe(f"<pre>{obj.top_holdings}</pre>") if obj.top_holdings else "No Data"
    display_top_holdings.short_description = "Top Holdings"


admin.site.register(UploadedFile, UploadedFileAdmin)

class AMCAdmin(admin.ModelAdmin):
    list_display = ('name',)
admin.site.register(AMC, AMCAdmin)

class MutualFundSchemeAdmin(admin.ModelAdmin):
    list_display = ('amc', 'scheme_name')
admin.site.register(MutualFundScheme, MutualFundSchemeAdmin)


class MutualFundDataAdmin(admin.ModelAdmin):
    list_display = ('amc','scheme','instrument_type', 'instrument_name', 'industry_rating', 'quantity', 'market_value', 'percentage_to_nav','isin', 'processed_at')
    list_filter = ('amc','scheme', 'processed_at')
admin.site.register(MutualFundData, MutualFundDataAdmin)
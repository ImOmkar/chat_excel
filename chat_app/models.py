import os
from django.db import models

# Create your models here.

class UploadExcel(models.Model):
    excel_file = models.FileField(upload_to='file_uploads/')
    column_names = models.TextField(null=True, blank=True) 
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return os.path.basename(self.excel_file.name)
    
    def file_name(self):
        return os.path.basename(self.excel_file.name)

class InputCommand(models.Model):
    file = models.ForeignKey(UploadExcel, null=True, on_delete=models.SET_NULL)
    command = models.TextField()
    response_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.command
    


    

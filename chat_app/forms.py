from django import forms
from django.forms import ModelForm
from .models import UploadExcel, InputCommand
from django.core.validators import FileExtensionValidator 

class UploadForm(ModelForm):
    
    excel_file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            "name": "files",
            "type": "file",
        }),
        validators=[FileExtensionValidator(allowed_extensions=['xls', 'xlsx'])]
    )

    class Meta:
        model = UploadExcel
        fields = ['excel_file']


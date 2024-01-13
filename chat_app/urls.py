from django.urls import path
from .views import (
                    home, 
                    upload_file, 
                    retrieve_file_in_session,
                    files,
                    
                    delete_uploaded_file,
                    delete_input_command
                    )

urlpatterns = [
    path("", home, name="home"),
    path("upload/", upload_file, name="upload_file"),
    path("files/", files, name="files"),
    path("files/<int:id>/", delete_uploaded_file, name="delete_uploaded_file"),
    path("retrieve_file_in_session/", retrieve_file_in_session, name="retrieve_file_in_session"),
    
    path("delete_input_command/<int:id>/", delete_input_command, name="delete_input_command")
]

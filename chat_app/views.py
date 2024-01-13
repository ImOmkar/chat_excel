from django.shortcuts import render, redirect
from django.http import JsonResponse
from .forms import UploadForm
from django.contrib import messages
from .models import UploadExcel
import pandas as pd
import os
from .models import InputCommand
import uuid

import matplotlib
matplotlib.use('Agg')  
"""
Using 'Agg' Non-interactive backend to avoid, 
"RuntimeError: main thread is not in main loop
Tcl_AsyncDelete: async handler deleted by the wrong thread" error
"""
import matplotlib.pyplot as plt
# Create your views here.

def home(request):
    form = UploadForm()
    files = UploadExcel.objects.all()
    cached_id = request.session.get('file_id')
    commands = InputCommand.objects.filter(file=cached_id).order_by('created_at')
    context = {'form': form, 'commands': commands, 'files': files}
    return render(request, 'home.html', context)

def upload_file(request):
    if request.method == 'POST':
        files = request.FILES.getlist('excel_file')
        print(files)
        for file in files:
            try:
                df = pd.read_excel(file, nrows=5) 
                column_names = ','.join(df.columns)

                upload_file = UploadExcel.objects.create(excel_file=file, column_names=column_names)
                upload_file.save()
                messages.error(request, f"File has been uploaded")
            except Exception as e:
                messages.error(request, f"Unsupported file: {file.name}")

        return redirect('home')
    return render(request, 'upload_form.html')

def files(request):
    files = UploadExcel.objects.all()
    context = {'files': files}
    return render(request, 'files.html', context)

def retrieve_file_in_session(request):
    if request.method == 'POST':
        file_id = request.POST.get('files')
        data = request.POST.get('command')

        if data and file_id and data.strip():
            request.session['file_id'] = file_id
            selected_file = UploadExcel.objects.get(id=file_id)
            processed_data = process_excel(selected_file.excel_file.path, data)
            print(processed_data)

            input_command = InputCommand.objects.create(file=selected_file, command=data, response_url=processed_data)
            input_command.save()

            return JsonResponse({'final_data_list': processed_data})
        else:
            return JsonResponse({'error': 'Select file and enter command'})
    else:
        return JsonResponse({'error': 'method not allowed'})

def process_excel(file_path, command):
    try:
        df = pd.read_excel(file_path)

        command_parts = command.lower().split()
        print(command_parts)

        if "summarize" in command_parts and "sales" in command_parts and "data" in command_parts and "for" in command_parts and "q1" in command_parts:

            q1_data = df[(df["Month Name"] == "January") | (df["Month Name"] == "February") | (df["Month Name"] == "March")]
            q1_data_grouped = q1_data.groupby(["Product", "Country"])
            q1_sales_summary = q1_data_grouped["Sales"].sum()
            q1_sales_summary = q1_sales_summary.sort_values(ascending=False)

            excel_filename = f"q1_sales_summary_{uuid.uuid4()}.xlsx"
            excel_file_path = os.path.join("media/processed_files/", excel_filename)
            q1_sales_summary.to_excel(excel_file_path, index=True)

            return excel_file_path

        if "create" in command_parts and "pie" in command_parts and "chart" in command_parts and "country" in command_parts and "wise" in command_parts and "sales" in command_parts:
            country_sales_data = df.groupby('Country')['Sales'].sum()

            plt.figure(figsize=(8, 8))
            plt.pie(country_sales_data, labels=country_sales_data.index, autopct='%1.1f%%', startangle=90)
            plt.title("Country-wise Sales Pie Chart")
            
            image_filename = f"country_wise_sales_pie_chart_{uuid.uuid4()}.png"
            image_file_path = os.path.join("media/processed_files/", image_filename)
            plt.savefig(image_file_path)
            plt.close()

            return image_file_path

        elif "filter" in command_parts and "out" in command_parts and "profits" in command_parts and "below" in command_parts and "$500" in command_parts:
            profit_threshold = 500
            filtered_data = df[df['Profit'] <= profit_threshold]

            excel_filename = f"entries_below_$500_{uuid.uuid4()}.xlsx"
            excel_file_path = os.path.join("media/processed_files/", excel_filename)
            filtered_data.to_excel(excel_file_path, index=False)

            return excel_file_path

        else:
            return f'Unsupported command: {command}'

    except Exception as e:
        return f'Error processing file: {e}'

def delete_uploaded_file(request, id):
    uploaded_file = UploadExcel.objects.get(id=id)
    uploaded_file.delete()
    return redirect('files')

def delete_input_command(request, id):
    uploaded_file = InputCommand.objects.get(id=id)
    uploaded_file.delete()
    
    cached_id = request.session.get('file_id')
    commands = InputCommand.objects.filter(file=cached_id).order_by('created_at')
    return render(request, 'chat_box.html', context={'commands': commands})
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .forms import UploadForm
from django.contrib import messages
from .models import UploadExcel
import pandas as pd
import os
from .models import InputCommand
import uuid
import re
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

            # return JsonResponse({'final_data_list': processed_data})
            if '/' in processed_data:
                return JsonResponse({'final_data_list': processed_data})
            else:
                return JsonResponse({'error': processed_data})
        else:
            return JsonResponse({'error': 'Select file and enter command'})
    else:
        return JsonResponse({'error': 'method not allowed'})


def check_column(df, commands):
    matching_commands = []
    for command in commands:
        if command in df.columns.str.capitalize().tolist():
            matching_commands.append(command)
    return matching_commands

def extract_column_info(command):
    grouping_pattern = re.compile(r'group\s*by\s*([^\s,]+)')
    summing_pattern = re.compile(r'sum\s*of\s*([^\s,]+)')
    pie_pattern = re.compile(r'pie')

    grouping_match = grouping_pattern.search(command)
    summing_match = summing_pattern.search(command)
    pie_match = pie_pattern.search(command)

    grouping_column = None
    if grouping_match:
        grouping_column = grouping_match.group(1)

    summing_column = None
    if summing_match:
        summing_column = summing_match.group(1)

    include_pie = False
    if pie_match:
        include_pie = True

    return grouping_column, summing_column, include_pie


def process_excel(file_path, command):
    grouping_column, summing_column, include_pie = extract_column_info(command)
    try:
        df = pd.read_excel(file_path)

        command_parts = command.split()
        print(command_parts)
        matching_columns = check_column(df, command_parts)

        if 'head' in command:
            data = df.head()

            excel_filename = f"{command}_{uuid.uuid4()}.xlsx"
            excel_file_path = os.path.join("media/processed_files/", excel_filename)
            data.to_excel(excel_file_path, index=True)

            return excel_file_path
        
        elif 'tail' in command:
            data = df.tail()

            excel_filename = f"{command}_{uuid.uuid4()}.xlsx"
            excel_file_path = os.path.join("media/processed_files/", excel_filename)
            data.to_excel(excel_file_path, index=True)

            return excel_file_path
        
        elif 'count' in command:
            data = df.count()

            excel_filename = f"{command}_{uuid.uuid4()}.xlsx"
            excel_file_path = os.path.join("media/processed_files/", excel_filename)
            data.to_excel(excel_file_path, index=True)

            return excel_file_path
        
        elif 'unique' in command:
            match = re.search(r'\bunique\s*([^\s,]+)\b', command)
            if match:
                column_name = match.group(1)
                if column_name in df.columns:
                    unique_values = df[column_name].unique()
                    unique_df = pd.DataFrame(unique_values, columns=[column_name])
                    excel_filename = f"{command}_{uuid.uuid4()}.xlsx"
                    excel_file_path = os.path.join("media/processed_files/", excel_filename)
                    unique_df.to_excel(excel_file_path, index=True)

                    return excel_file_path
                else:
                    return f"Column '{column_name}' not found."
            else:
                return "No match found."

        elif 'summarize' in command_parts:
            matching_columns = check_column(df, command_parts)
            print(matching_columns)
            summary = df[matching_columns].describe() if len(matching_columns) > 0 else df.describe()
            print(summary)

            excel_filename = f"summarize_{uuid.uuid4()}.xlsx"
            excel_file_path = os.path.join("media/processed_files/", excel_filename)
            summary.to_excel(excel_file_path, index=True)

            return excel_file_path

        elif 'average' in command_parts and len(matching_columns) > 0:
            averages_dict = {}
            for column in matching_columns:
                if column in df.columns:
                    column_average = df[column].replace('[\$,]', '', regex=True).astype(float).mean()
                    print(f"Average {column}: ${column_average:.2f}")
                    averages_dict[column] = column_average
                else:
                    print(f"Column '{column}' not found.")

            excel_filename = f"average_{uuid.uuid4()}.xlsx"
            excel_file_path = os.path.join("media/processed_files/", excel_filename)
            averages_df = pd.DataFrame.from_dict(averages_dict, orient='index', columns=['Average'])
            averages_df.to_excel(excel_file_path, index_label='Column')
            return excel_file_path
        

        elif 'filter' in command_parts:
            matching_columns = check_column(df, command_parts)
            print(matching_columns)

            if len(matching_columns) == 1:
                column_name = matching_columns[0]

                if column_name in df.columns:
                    filter_value = [int(value) for value in command_parts if value.isnumeric()]
                    
                    if filter_value:
                        filter_value = filter_value[0]  

                        if 'below' in command_parts:
                            filtered_df = df[df[column_name] < filter_value]
                            excel_filename = f"entries_below_{filter_value}_{uuid.uuid4()}.xlsx"
                            excel_file_path = os.path.join("media/processed_files/", excel_filename)
                            filtered_df.to_excel(excel_file_path, index=False)
                            return excel_file_path

                        elif 'above' in command_parts:
                            filtered_df = df[df[column_name] > filter_value]
                            excel_filename = f"entries_above_{filter_value}_{uuid.uuid4()}.xlsx"
                            excel_file_path = os.path.join("media/processed_files/", excel_filename)
                            filtered_df.to_excel(excel_file_path, index=False)
                            return excel_file_path

                        else:
                            return 'Specify "below" or "above" in the command for filtering.'
                    else:
                        return 'Enter a numeric value to filter.'

                else:
                    return 'Column not found in the DataFrame.'
            else:
                return 'Please specify a single column for filtering.'

        
        elif grouping_column and summing_column:
            if all(column in df.columns for column in [grouping_column, summing_column]):
                group_data = df.groupby(grouping_column)[summing_column].sum()

                if include_pie:
                    plt.figure(figsize=(8, 8))
                    plt.pie(group_data, labels=group_data.index, autopct='%1.1f%%', startangle=90)
                    plt.title(f"{grouping_column.capitalize()} {summing_column.capitalize()} Pie Chart")

                    image_filename = f"{grouping_column}_{summing_column}_pie_chart_{uuid.uuid4()}.png"
                    image_file_path = os.path.join("media/processed_files/", image_filename)
                    plt.savefig(image_file_path)
                    plt.close()

                    return image_file_path
                else:
                    return f"{grouping_column.capitalize()} {summing_column.capitalize()} Sum: {group_data}"
            else:
                return "One or more specified columns not found."

        else:
            return "Command not recognized."

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
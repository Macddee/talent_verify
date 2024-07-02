import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_verify_project.settings')
application = get_wsgi_application()


from .views import generate_user, create_or_change_role, create_to_the_employee_table, create_to_the_company_table
import csv
import pyexcel as pe

def find_file(filename):
    file_dir = os.path.dirname(__file__)
    file_path = os.path.join(file_dir, filename)
    return file_path

def process_employee_txt_file():
    # heading order : name; surname; id_number; email; role; duties_csv; departments_csv;  date_started; date_left
    heading= []
    batch_size = 3
    data_batch = []
            
    with open(find_file("employee_textfile.txt"), "r") as file:
        heading = file.readline().strip().split(";")
        print("employee txt file opened")

        if heading[0].strip() == "name" and heading[1].strip() == "surname" and heading[2].strip() == "id_number" and \
        heading[3].strip() == "email" and heading[4].strip() == "role" and heading[5].strip() == "duties_csv" and \
        heading[6].strip() == "departments_csv" and heading[7].strip() == "date_started" and heading[8].strip() == "date_left" :

            for line in file:
                data_batch.append(line.split(";"))
                print("for file opened")
                
                # chunk the data and only send to db if its 10
                if len(data_batch) >= batch_size:
                    current_batch =  process_employees_batch(data_batch)      
                    data_batch = []
                    # print(current_batch)
                    yield current_batch

            # its less than 10, so lest just send whats there...
            if data_batch:
                print("data exiss.....................................................................")
                yield process_employees_batch(data_batch)
                               
        else:
            return "Error in file heading"
        

def process_employee_csv_file():
    # heading order : name; surname; id_number; email; role; duties_csv; departments_csv;  date_started; date_left
    heading= []
    batch_size = 3
    data_batch = []
            
    with open(find_file("employee_csv.csv"), "r") as file:
        csv_reader = csv.reader(file, delimiter=';')
        heading = next(csv_reader)
        print("csv employeee file opened")

        if heading[0].strip() == "name" and heading[1].strip() == "surname" and heading[2].strip() == "id_number" and \
        heading[3].strip() == "email" and heading[4].strip() == "role" and heading[5].strip() == "duties_csv" and \
        heading[6].strip() == "departments_csv" and heading[7].strip() == "date_started" and heading[8].strip() == "date_left" :

            for line in csv_reader:
                data_batch.append(line)
                                
                # chunk the data and only send to db if its 10
                if len(data_batch) >= batch_size:
                    current_batch =  process_employees_batch(data_batch)      
                    data_batch = []
                    # print(current_batch)
                    yield current_batch

            # its less than 10, so lest just send whats there...
            if data_batch:
                yield process_employees_batch(data_batch)
                               
        else:
            return "Error in file heading"


def process_employee_excel_file():
    # heading order : name; surname; id_number; email; role; duties_csv; departments_csv;  date_started; date_left
    batch_size = 3
    data_batch = []
            
    sheet = pe.get_sheet(file_name=find_file("employee_excel.xlsx"), auto_detect_datetime=False)
    print(" employeee Excel file opened")

    heading = sheet.row[0]

    if heading[0].strip() == "name" and heading[1].strip() == "surname" and heading[2].strip() == "id_number" and \
    heading[3].strip() == "email" and heading[4].strip() == "role" and heading[5].strip() == "duties_csv" and \
    heading[6].strip() == "departments_csv" and heading[7] == "date_started" and heading[8] == "date_left" :
        # import pdb; pdb.set_trace()
        print("Total items in the sheet:", sheet.number_of_rows() - 1)
        for row in sheet.row[1:]: #research how to start from row 2
            if not all(cell.strip() == '' for cell in row):
                data_batch.append(row)
            
            # chunk the data and only send to db if its 10
            if len(data_batch) >= batch_size:
                current_batch =  process_employees_batch(data_batch)      
                data_batch = []
                print(current_batch)
                yield current_batch

        # its less than 10, so lest just send whats there...
        if data_batch:
            print("LESSS THANN BATCH")
            print(data_batch)
            yield process_employees_batch(data_batch)
                           
    else:
        return "Error in file heading"


def process_employees_batch(data_batch):
    processed_data_batch = []
    for data in data_batch:
        processed_data = {
            "name": data[0].strip(),
            "surname": data[1].strip(),
            "id_number": data[2].strip(),
            "email": data[3].strip(),
            "role": data[4].strip(),
            "duties_csv": data[5].strip(),
            "departments_csv": data[6].strip(),
            "date_started": str(data[7]).strip().split(" ")[0],
            "date_left": str(data[8]).strip().split(" ")[0] if len(data) > 8 else None
        }
        processed_data_batch.append(processed_data)
    
    return processed_data_batch

# for batch in process_employee_excel_file():
#     print(batch)


#calling function is the generator function that will be needed to yield each batch when its available.
#its passed as a param because there are 3 functions, so we need the view calling the save to db method 
#to give the function its using coz we have employee txt, csv, excel
def save_employee_to_db(company, calling_function):
    error_list = []
    response_log = []
    for processed_data_batch in calling_function():
        for batch_item in processed_data_batch:
            # import pdb; pdb.set_trace()
            generated_employee = generate_user(batch_item=batch_item)

            if isinstance(generated_employee, dict):
                response_log.append(generated_employee)
                continue
            
            employee_response = create_to_the_employee_table(batch_item=batch_item, company=company, generated_employee=generated_employee[0])
            if "error" in employee_response:
                response_log.append(employee_response)
                continue

            role_response = create_or_change_role(batch_item=batch_item,company=company, employee=employee_response[3])
            if "error" in role_response:
                response_log.append(role_response)
                continue


            if "error" not in employee_response and "error" not in role_response:
                employee_response.pop(3)
                response_log.append(employee_response)
                response_log.append(role_response)
                #send email here....
                
    print("printing response log")
    print(response_log)
    return response_log



def process_company_txt_file():
    # heading order : name; registration_date; registration_number; address; contact_person; number_of_employees; contact_phone; email_address, department_csv       
    
    heading= []
    batch_size = 3
    data_batch = []
            
    with open(find_file("company_txt.txt"), "r") as file:
        heading = file.readline().strip().split(";")
        print("company txt file opened")

        if heading[0].strip() == "name" and heading[1].strip() == "registration_date" and heading[2].strip() == "registration_number" and \
        heading[3].strip() == "address" and heading[4].strip() == "contact_person" and heading[5].strip() == "number_of_employees" and \
        heading[6].strip() == "contact_phone" and heading[7].strip() == "email_address" and heading[8].strip() == "department_csv" :

            for line in file:
                data_batch.append(line.split(";"))
                
                # chunk the data and only send to db if its 10
                if len(data_batch) >= batch_size:
                    current_batch =  process_company_batch(data_batch)      
                    data_batch = []
                    print("batched_up")
                    yield current_batch

            # its less than 10, so lest just send whats there...
            if data_batch:
                yield process_company_batch(data_batch)
                               
        else:
            return "Error in file heading"

def process_company_csv_file():
    # heading order : name; registration_date; registration_number; address; contact_person; number_of_employees; contact_phone; email_address, department_csv       
    
    heading= []
    batch_size = 3
    data_batch = []
            
    with open(find_file("company_csv.csv"), "r") as file:
        csv_reader = csv.reader(file, delimiter=";")
        heading = next(csv_reader)
        print("ompany csv file opened")

        if heading[0].strip() == "name" and heading[1].strip() == "registration_date" and heading[2].strip() == "registration_number" and \
        heading[3].strip() == "address" and heading[4].strip() == "contact_person" and heading[5].strip() == "number_of_employees" and \
        heading[6].strip() == "contact_phone" and heading[7].strip() == "email_address" and heading[8].strip() == "department_csv" :

            for line in csv_reader:
                data_batch.append(line)
                
                # chunk the data and only send to db if its 10
                if len(data_batch) >= batch_size:
                    current_batch =  process_company_batch(data_batch)      
                    data_batch = []
                    print("batched_up")
                    yield current_batch

            # its less than 10, so lest just send whats there...
            if data_batch:
                yield process_company_batch(data_batch)
                               
        else:
            return "Error in file heading"
        

def process_company_excel_file():
    # heading order : name; registration_date; registration_number; address; contact_person; number_of_employees; contact_phone; email_address, department_csv       
    
    batch_size = 3
    data_batch = []

    sheet = pe.get_sheet(file_name=find_file("company_excel.xlsx"), auto_detect_datetime=False)        

    print("excell file file opened")
    heading=sheet.row[0]
    if heading[0].strip() == "name" and heading[1].strip() == "registration_date" and heading[2].strip() == "registration_number" and \
    heading[3].strip() == "address" and heading[4].strip() == "contact_person" and heading[5].strip() == "number_of_employees" and \
    heading[6].strip() == "contact_phone" and heading[7].strip() == "email_address" and heading[8].strip() == "department_csv" :

        for row in sheet.row[1:]:
            data_batch.append(row)
            
            # chunk the data and only send to db if its 10
            if len(data_batch) >= batch_size:
                current_batch =  process_company_batch(data_batch)      
                data_batch = []
                print("batched_up")
                yield current_batch

        # its less than 10, so lest just send whats there...
        if data_batch:
            yield process_company_batch(data_batch)
                            
    else:
        return "Error in file heading"
        

def process_company_batch(data_batch):

    processed_data_batch = []
    for data in data_batch:
        processed_data = {
            "name": data[0].strip(),
            "registration_date": str(data[1]).strip().split(" ")[0], # excel is making the string a datetime filed
            #and its returning “2004-08-23 00:00:00”. But django wants YYYY-MM-DD so we spliting it at " " and geting the firs part of the sting[0]
            "registration_number": data[2].strip(),
            "address": data[3].strip(),
            "contact_person": data[4].strip(),
            "number_of_employees": str(data[5]).strip(),
            "contact_phone": str(data[6]).strip(),
            "email_address": data[7].strip(),
            "department_csv": data[8].strip(),
        }
        processed_data_batch.append(processed_data)
    
    return processed_data_batch



def save_company_to_db(calling_function): 
    response_log = []
    for processed_data_batch in calling_function():
        
        for batch_item in processed_data_batch:

            company_response = create_to_the_company_table(batch_item=batch_item)
        
            if "error" in company_response.keys():
                response_log.append(company_response)
                continue
           
            else:
                response_log.append(company_response)

    print("printing response log")
    print(response_log)
    return response_log





# for batch in process_company_excel_file():
#     print(batch)


# class EmployeeDataModel:
#     def __init__(self, departments_csv, name, surname, id_number, email, duties_csv, role, date_started, date_left,) -> None:
#         self.departments_csv = departments_csv
#         self.name = name
#         self.surname = surname
#         self.id_number = id_number
#         self.email = email
#         self.duties_csv = duties_csv
#         self.role = role
#         self.date_started = date_started
#         self.date_left = date_left

#     def check_emploee_excel_file_heading_order(self):
#         pass

#     def check_employee_csv_first_role_order(self):
#         pass

#     def process_employee_txt_file(self):
#         pass

            

#     def read_employee_txt_file():
#         pass

  
#     def create_bulk_employees(self):
#         pass




# # a = "    df  "        

# # print(a.strip('"'))




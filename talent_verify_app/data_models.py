import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_verify_project.settings')
application = get_wsgi_application()


from .views import generate_user, create_or_change_role, create_to_the_employee_table

script_dir = os.path.dirname(__file__)
file_path = os.path.join(script_dir, "employee_textfile.txt")

def process_employee_txt_file():
    # heading order : name; surname; id_number; email; role; duties_csv; departments_csv;  date_started; date_left
    heading= []
    batch_size = 10
    data_batch = []
            
    with open(file_path, "r") as file:
        heading = file.readline().strip().split(";")
        print("file opened")

        if heading[0].strip() == "name" and heading[1].strip() == "surname" and heading[2].strip() == "id_number" and \
        heading[3].strip() == "email" and heading[4].strip() == "role" and heading[5].strip() == "duties_csv" and \
        heading[6].strip() == "departments_csv" and heading[7].strip() == "date_started" and heading[8].strip() == "date_left" :

            for line in file:
                data_batch.append(line.split(";"))
                print("for file opened")
                
                # chunk the data and only send to db if its 10
                if len(data_batch) >= batch_size:
                    process_batch(data_batch)        
                    data_batch = []

            # its less than 10, so lest just send whats there...
            if data_batch:
                print("data exiss.....................................................................")
                print(process_batch(data_batch))
                               
        else:
            return "Error in file heading"

def process_batch(data_batch):
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
            "date_started": data[7].strip(),
            "date_left": data[8].strip() if len(data) > 8 else None
        }
        processed_data_batch.append(processed_data)
    
    return processed_data_batch


process_employee_txt_file()  


def save_to_db(company):
    processed_data_batch = process_employee_txt_file()
    print(processed_data_batch)
    response_log = []
    for batch_item in processed_data_batch:
        generated_employee = generate_user(batch_item=batch_item)
        employee_response = create_to_the_employee_table(batch_item=batch_item, company=company, generated_employee=generated_employee)
        role_response = create_or_change_role(batch_item=batch_item,company=company, employee=employee_response[3])
        if generated_employee[2]:
            response_log.append([
                {"employee created": "True"},
                generated_employee[0],
                generated_employee[1],
                generated_employee[2],
                role_response[1],
                role_response[0],
                ])
                
        else:
            response_log.append([
                {"employee created": "True"},
                generated_employee[0],
                generated_employee[1],
                role_response[1],
                role_response[0],
                ])

    return response_log


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




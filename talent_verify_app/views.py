from rest_framework.decorators import api_view
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import login, logout,authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from .models import *
import secrets
import string
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import transaction
from django.db.models import F, Q
from django.core.mail import send_mail


#HELPER FUNCTIONS
def check_user_type(user):
    return user.is_staff

def send_email_to_generated_user(username, password, email):
    send_mail(
        'Welcome to talent verify ',
        f"""Please check your generated details, here is your login information:\n\nUsername: {username}\nPassword: {password}""",
        'talentverify@gmail.com',  # Replace with your own email
        [email],
        fail_silently=False,
    )


def generate_user(name=None, surname=None, email=None, username=None, passw=None, batch_item=None):
        # Get the 'Employees' group
    employee_group = Group.objects.get_or_create(name='Employees')
    #check if user creation call is for creating an employee or a company user

    if username:
        # potential company users provide their own username so its not non
        uname = username
        password = passw
        email_address = email
        is_staff = True

    # employee users have their usernames automatically gebnerated either individually or from batch
    elif name or batch_item: 
        
        if name: # the user is an employee and its individual creation
            uname = ".".join([name, surname]).lower()
            email_address = email

        else:
            uname = ".".join([batch_item["name"], batch_item["surname"]]).lower()
            name = batch_item["name"]
            surname = batch_item["surname"]
            email_address = batch_item["email"]

        uname = "@".join([uname, "tv"])
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(10))
        is_staff = False
    else:
        return {"error": "Invalid arguments"}

    # import pdb
    # pdb.set_trace()

    try:
        user = User(username=uname.strip(), email=email_address, first_name=name, last_name=surname, is_staff=is_staff)
        user.set_password(password)
        user.full_clean()
        user.save()

        if not check_user_type :
            user.groups.add(employee_group)

    except ValidationError as e:
        print("ERRRRRORRRR INNNN USSSEEERRRRR")
        return {"error": e.message_dict, "username": uname}
    
    except IntegrityError as e:
        
        if 'unique constraint' in str(e) and 'username' in str(e):
            return {"error": f"A user with the username {uname} already exists."}
        else:
            return {"error": str(e)}
        
    else:
        print("USSSEEERRRRR CCCCERRREEEAAAATTTTEEEDD BBBUUUTTT HHHOOOOWWWW")
        return [user, uname, password, email_address]
    

def create_or_change_role(current_role=None, new_role=None, batch_item=None, employee=None, company=None):
    employee_for_error_message = ""
    #this we creating  a new employee with new roles assigned to em
    if current_role is not None:
        
        duties = current_role[0].split(",") #. #strip()
        processed_role = RoleHistory(
            role = current_role[1],
            date_started = current_role[2],
            date_left = current_role[3],
            employee = current_role[4],
            company = current_role[5],
        )
        employee_for_error_message = f"{current_role[4].user.first_name} {current_role[4].user.last_name}"

    #this means that we are its an employee that has beenassigned a role aleady and is changing within the company
    elif new_role:
        duties = new_role[0].split(",") #. #strip()
        processed_role = RoleHistory(
            role = new_role[1],
            date_started = new_role[2],
            date_left = new_role[3],
            employee = new_role[4],
            company = new_role[5],
        )
        employee_for_error_message = f"{new_role[4].user.first_name} {new_role[4].user.last_name}"
    # this means we are doing a bulk upload and we     
    else:
        duties = batch_item["duties_csv"].split(",") #. #strip()
        processed_role = RoleHistory(
            role = batch_item["role"],
            date_started = batch_item["date_started"],
            date_left = batch_item["date_left"],
            employee = employee,
            company = company,

        )
        employee_for_error_message = employee

    print(employee_for_error_message)
    try:
        
        processed_role.full_clean()
        processed_role.save()

    

    except ValidationError as e:
        print("ERRRRRORRRR INNNN USSSEEERRRRR RRRROOOLLLEEE TTAABBLEE")
        return {"error": e.error_dict, "employee": employee_for_error_message}

    except IntegrityError as e:
        print("ERRRRRORRRR INNNN USSSEEERRRRR RRROOOLLLAAAEE TTTAABBLLEE")
        return {"error": str(e), "employee": employee_for_error_message}

    # now to associate the duties in the duty table with the duties provided.
    # this will check if a duty is already there or add the new duty to the table if otherwise

    print("CCCRREEEAAATTTTIINNNGG RRROOLLESSS COIOOOREEECT")
    if duties:
        for duty in duties:
            role_duty, result = DutyRole.objects.get_or_create(duty_in_role=duty)

            processed_role.duties.add(role_duty)

        role_hist_serializer = RoleHistorySerializer(processed_role)
        role_hist_response_obj = (role_hist_serializer.data, {"saved employee has duties": "True"})
        return role_hist_response_obj

    else: 
        role_hist_serializer = RoleHistorySerializer(processed_role)
        role_hist_response_obj(role_hist_serializer.data, {"saved employee has duties": "False"})
        return role_hist_response_obj


def create_to_the_employee_table(id_number=None, company=None, generated_employee=None, departments_csv=None, batch_item=None):
    id = ""
    dept_csv = ""


 #write data to the Employee table

    if batch_item:
        #the case where the users are being created in bulk
        id = batch_item["id_number"]
        dept_csv = batch_item["departments_csv"]

    else:
        id = id_number
        dept_csv = departments_csv
  
    #if not provided then its the case where users are being created normaly, one at a time       

    print(id, dept_csv)
    try:
        proccesed_employee = Employee(
        id_number=id,
        company=company,
        user=generated_employee
        )
        proccesed_employee.full_clean()
        proccesed_employee.save()

    except ValidationError as e:
        print("ERRRRRORRRR INNNN USSSEEERRRRR EEEMMMPPLOOYYEEE TAAABLLLEE")
        return {"error": e.error_dict, "user": proccesed_employee.user.username}
    
    except IntegrityError as e:
        print("ERRRRRORRRR INNNN USSSEEERRRRR EEEEMMMPPLLOOYYEEE TTTAABBBLLEE")
        return {"error": str(e), "user": proccesed_employee.user.username}
    
    # update the number of employees field in the company table with the addition of the extra 1 employee
    company_update = Company.objects.get(name=company)
    company_update.number_of_employees = F("number_of_employees") + 1
    company_update.save()


    #writing to the departments table
    departments = dept_csv.split(",")
    non_existing_departments = []
    existing_departments = []
    non_existing_departments_response = {}
    dpt_response_obj = []
   
    if departments:
        for dept in departments:
            try:
                employee_dept = Departments.objects.get(
                    department = dept
                )
            
                #associate the daprtmant with the current employee
                proccesed_employee.department.add(employee_dept)
                existing_departments.append(dept) 
        
            #capture all non existing deps to report to the company
            except Departments.DoesNotExist:
                non_existing_departments.append(dept)

        if non_existing_departments:
            non_existing_departments_response = {"non existing company departments": non_existing_departments}
            emp_serializer = EmployeeSerializer(proccesed_employee)
            dpt_response_obj = (emp_serializer.data, {"saved employee departments": existing_departments})
            
        else:
            emp_serializer = EmployeeSerializer(proccesed_employee)
            dpt_response_obj = (emp_serializer.data, {"saved employee has departments": "True"})
    else:
        emp_serializer = EmployeeSerializer(proccesed_employee)
        dpt_response_obj(emp_serializer.data, {"saved employee has departments": "False"})
    print("ADDDDDIIINNNNGGGGG EEEEMPPPLLLOOOYEEEEE SSSSUUUCCEESSS")
    return[
            dpt_response_obj[0], #seperated so i dont work with lists in lists in the create_employee view
            dpt_response_obj[1],
            non_existing_departments_response,
            proccesed_employee,
        ]


def create_to_the_company_table(single_company=None, batch_item=None):
    if single_company:
        user                = single_company["user"]          
        name                = single_company["name"] 
        registration_date   = single_company["registration_date"] 
        registration_number = single_company["registration_number"]   
        address             = single_company["address"]
        contact_person      = single_company["contact_person"]
        number_of_employees = single_company["number_of_employees"]   
        contact_phone       = single_company["contact_phone"]
        email_address       = single_company["email_address"]
        department_csv      = single_company["department_csv"]

    else:
        user                = None         
        name                = batch_item["name"]
        registration_date   = batch_item["registration_date"]
        registration_number = batch_item["registration_number"]
        address             = batch_item["address"]
        contact_person      = batch_item["contact_person"]
        number_of_employees = batch_item["number_of_employees"]
        contact_phone       = batch_item["contact_phone"]
        email_address       = batch_item["email_address"]
        department_csv      = batch_item["department_csv"]

    try: 
        processed_company = Company(
            user                = user,          
            name                = name,   
            registration_date   = registration_date,  
            registration_number = registration_number,  
            address             = address,    
            contact_person      = contact_person, 
            number_of_employees = number_of_employees,    
            contact_phone       = contact_phone,  
            email_address       = email_address
        )

        processed_company.full_clean()
        processed_company.save()


    except ValidationError as e:
        return {"error": e.error_dict, "company": processed_company.name}

    
    except IntegrityError as e:
        return {"error": str(e), "company": processed_company.name}

    # now to check if a department already exists and add if its not already there.
    
    
    if department_csv:
        departments = department_csv.split(",")
        for departnment_name in departments:
            departnment_name = departnment_name.strip()#.title()

            department, created = Departments.objects.get_or_create(department=departnment_name)

            processed_company.department.add(department)

        processed_company_serializer = CompanySerializer(processed_company)
        return {
            "data": processed_company_serializer.data,
            "saved company has departments": "True"
        }       
    
    else:
        processed_company_serializer = CompanySerializer(processed_company)
        return {"saved company has departments": "False",
                "data": processed_company_serializer.data
            }


# API METHODS
@api_view(["POST"])
def upload(request):
        file_serializer = UploadSerializer(data=request.data)
        if file_serializer.is_valid():
            file_serializer.save()
            return Response(file_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
def home(request):

    content = [
                        "AVAILABLE API ENDPOINDS::"
        "https://talent-verify-e6886a399610.herokuapp.com/",
        "https://talent-verify-e6886a399610.herokuapp.com/signup/",
        "https://talent-verify-e6886a399610.herokuapp.com/login/",
        "https://talent-verify-e6886a399610.herokuapp.com/logout/",
        "https://talent-verify-e6886a399610.herokuapp.com/create-company/",
        "https://talent-verify-e6886a399610.herokuapp.com/choose-company/",
        "https://talent-verify-e6886a399610.herokuapp.com/create-employee/",
        "https://talent-verify-e6886a399610.herokuapp.com/change-role/",
        "https://talent-verify-e6886a399610.herokuapp.com/change-company/",
        "https://talent-verify-e6886a399610.herokuapp.com/create-employees-txt/",
        "https://talent-verify-e6886a399610.herokuapp.com/create-employees-csv/",
        "https://talent-verify-e6886a399610.herokuapp.com/create-employees-excel/",
        "https://talent-verify-e6886a399610.herokuapp.com/create-companies-txt/",
        "https://talent-verify-e6886a399610.herokuapp.com/create-companies-csv/",
        "https://talent-verify-e6886a399610.herokuapp.com/create-companies-excel/",
        "https://talent-verify-e6886a399610.herokuapp.com/associate-user-with-company/",
        "https://talent-verify-e6886a399610.herokuapp.com/search-employees/",
        "https://talent-verify-e6886a399610.herokuapp.com/change-password/",
        "https://talent-verify-e6886a399610.herokuapp.com/upload/",

        {"Information - 01": "API endpoints to only be consumed with the talent-verify web app."},
        {"Information - 02": "email <<macddeemanana@gmail.com>> for the API Docs"},
        {"Information - 03": ["changes to the database are only persisted in your current session and are deleted once you leave the session.",
                            "i'm not financially ready to subscribe for a database server for an API that is not used!"]},
        {"Information - 04": ["bulk upload is working with manually uploading the file with the data in the talent_verify_app directory.",
                            "there were issues with uploading files via the DRF browsable api. to check this feature please",
                            "clone this project from <<https://github.com/Macddee/talent_verify>> activate the environment tv_venv\\scripts\\actiavte",
                            "or simply wait for the frontend to complete!!!"]},
        {"Information - 05": ["im still thinking wether to enable sending welcome email to bulk geneated users or not sinse this takes some noticeable amount of time.",
                            "for now its only enabled when creating a single employee and responses are coming after aproximately 3 seconds.",
                            "could have used Celery to que tasks such that the http response doesn't wait for the sending mail method to complete.",
                            "however, that would require addons for the message broker like RabbitMQ or Redis, which are paid services again"]}                                                            


    ]

    return Response(content, status=status.HTTP_200_OK)

#create company USUER also the admin for the company in question
@api_view(["GET","POST"])
def create_user(request):
    if request.method == "GET":
        return Response([
            {"content": "only company users(admins) are allowed to explicitly create accounts here"},
            {"content": "to avoid emloyees from creting personal accounts, all accounts will be deleted within 5 days if they not associated to a company"},
            
    ])

    username = request.data.get("username")
    password = request.data.get("password")
    email = request.data.get("email")
    name = request.data.get("name")
    surname = request.data.get("surname")

    # user = User.objects.create_user(username=username, password=password, email=email, first_name=name, last_name=surname)
    # return Response("sucess")

    # check if the returned employee is an instance of user. or retturn the the exception  
    user = generate_user(name,surname,email,username, password)
   
    if isinstance(user, dict):
        return Response(user)
    
    #lohout any logged in user to avoid not mix companies if the user has been gen
    logout(request)

    user_data = {
        "username": user[0].username,
        "email": user[0].email
    }
    
    return Response(user_data, status=status.HTTP_201_CREATED,)


@api_view(["POST"])
def login_user(request):
    """
    This view logs in a user with a given username and password.
    """
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(request, username=username, password=password)
    print(user)

    if user is not None:
        login(request, user)
        return Response({"message": "User logged in successfully"}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Invalid username or password"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def logout_user(request):
    logout(request)
    return Response({"message": "User logged out successfully!"}, status=status.HTTP_200_OK)


@api_view(["POST"])
def change_password(request):
    user = request.user
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")
    if not user.check_password(old_password):
        return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
    user.set_password(new_password)
    user.save()
    return Response({"content": "new password saved"}, status=status.HTTP_202_ACCEPTED)


@api_view(["POST"])
def create_company(request):
    user = request.user
    single_company = {
        "user": user,
        "name": request.data.get("name"),
        "registration_date": request.data.get("registration_date"),
        "registration_number": request.data.get("registration_number"),
        "address": request.data.get("address"),
        "contact_person": request.data.get("contact_person"),
        "number_of_employees": request.data.get("number_of_employees"),
        "contact_phone": request.data.get("contact_phone"),
        "email_address": request.data.get("email_address"),
        "department_csv": request.data.get("department_csv"),
    }


    if user.is_authenticated:
        if check_user_type(user):
            company_response_obj = create_to_the_company_table(single_company)
            return Response(company_response_obj,status=status.HTTP_200_OK)
        else:
            return Response({"content": "None Company users cant create companies"}, status=status.HTTP_403_FORBIDDEN)

    else:
        return Response({"content": "Please login first before creacting a company"}, status=status.HTTP_401_UNAUTHORIZED)


#pre requesits for creating an employee. (associating an employee with the company of the admmin thats creating the eployeee)
#we cant just say user.company because the user can have many companies. so we have to store the company they login as
# endpoind to be called directly after login
@api_view(["GET", "POST"])
def check_company_user_wants_users_have_many_companies(request):
    if check_user_type(request.user):

        if request.method == "GET":
            #check if the user is part of many companies and return the one with the name thats sent
            try:
                company_names = [company['name'] for company in request.user.company.values('name')]
                
                if len(company_names) > 1:
                    return Response({"content": "choose the company you want to login as",
                                    "user": request.user.username,
                                    "data": company_names},
                                    status=status.HTTP_302_FOUND
                                    )
                else:
                    #put the chosen company in a session variable so that we can look for the compnay when creating an employee
                    request.session['company_logged_in_as'] = company_names[0]
                    print(request.session.get("company_logged_in_as"))
                    return Response({"content":"User only associated to one company.", "company": company_names[0]}, status=status.HTTP_204_NO_CONTENT)
            except:
                    return Response({"content":"You are not associated to any company. Please create one"}, status=status.HTTP_204_NO_CONTENT)

        
        # return only the company that he selects.
        elif request.method == "POST":
            
            company_logged_in_as = Company.objects.filter(name=request.data.get("selected_company")).first()
            
            #put the chosen company in a session variable so that we can look for the compnay when creating an employee
            request.session['company_logged_in_as'] = company_logged_in_as.name
        
            company_logged_in_as_serializer = CompanySerializer(company_logged_in_as)
            return Response(company_logged_in_as_serializer.data)
        
    return Response({"content": "Invalid Permisions"}, status=status.HTTP_403_FORBIDDEN)


@api_view(["POST"])
def create_employee(request):
    departments_csv = request.data.get("departments_csv")

    name = request.data.get("name")
    surname= request.data.get("surname")
    id_number = request.data.get("id_number")
    email = request.data.get("email")
    company = Company.objects.filter(name=request.session.get("company_logged_in_as")).first()

    #role information same employee
    duties_csv =  request.data.get("duties_csv")
    role = request.data.get("role")
    date_started = request.data.get("date_started")
    date_left = request.data.get("date_left")
    # import pdb
    # pdb.set_trace()  
    if not request.user.is_authenticated:
        return Response({"content": "Please login to create an employee"}, status=status.HTTP_401_UNAUTHORIZED)

    if not check_user_type(request.user):
        return Response([
                    {"content": "User is not a company user"},
                    {"content": "you might want to visit the endpoind check company or create a company"}
                    ],
                    status=status.HTTP_403_FORBIDDEN)

    response_data = []
     
    #creating a custom error so that users wont be saved when the employee or roles tables make errors.
    #since all the possible errors are handled, tre exception that triggers the atomic() was offf
    #so had to create a loop coz the data is a list of dicts with [{error: xx}, error: xx]
    try:   
        with transaction.atomic():
            generated_employee = generate_user(name, surname, email)
            #check if the returned employee is an instance of user. or retturn the the exception  
            if isinstance(generated_employee, dict):
                response_data = generated_employee
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

            #create employee contains 4 items, the first 3 are strings the details of created deptatments, and not found departments 
            #the 4th items is the processed employee which is required in the role table by the create or update role function
            # this is an instance of the useer saved in the employee table. NOT THE GENERATED ONE
            create_employee_response_obj = create_to_the_employee_table(id_number,company,generated_employee[0],departments_csv)
            if "error" in create_employee_response_obj: 
                response_data = create_employee_response_obj
                raise IntegrityError
            
            
            #pass the role creation or changing function a list of the new values
            current_role = [duties_csv,
                            role,
                            date_started,
                            date_left,
                            create_employee_response_obj[3], # the proccesed employee, is required to associate the role with the employee 
                            company,
                        ]

            #getting the response object from the create or update role seperated from create_employee
            #because this one can also update roles, which is not creating employees
            role_hist_response_obj = create_or_change_role(current_role)

            
            if "error" in role_hist_response_obj: 
                response_data = role_hist_response_obj
                raise IntegrityError
                  
    except IntegrityError:
        print("errorrr caught")
        return Response(response_data, status.HTTP_400_BAD_REQUEST)

    print((create_employee_response_obj))

    if "error" not in create_employee_response_obj and "error" not in role_hist_response_obj:
        create_employee_response_obj.pop(3)
        response_data = [
            create_employee_response_obj,
            role_hist_response_obj
        ]
        #send email here
        try:
            send_email_to_generated_user(generated_employee[1], password=generated_employee[2], email=generated_employee[3])
            response_data.append({"mail  content": "Email sucessfuly sent to the user"})

        except:
            response_data.append({"mail  content": "Email not sent to the user. please send manually."})
    

        return Response(response_data, status=status.HTTP_201_CREATED)

@api_view(["POST"])
def change_role(request):
    if not check_user_type(request.user):
        return Response({"content": "Invalid Permisions"}, status=status.HTTP_403_FORBIDDEN)

    duties_csv =  request.data.get("duties_csv")
    role = request.data.get("role")
    date_started = request.data.get("date_started")
    date_left = request.data.get("date_left")
    username = request.data.get("username")

    if date_left is None:
        return Response({"content": "The date left field is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    new_company = Company.objects.filter(name=request.session.get("company_logged_in_as")).first()

    processed_employee = get_object_or_404(
        Employee,
        user__username = username
    )

    #pass the role creation or changing function a list of the new values
    new_role=[duties_csv,
              role,
              date_started,
              date_left,
              processed_employee,
              new_company.name,
              ]
    
    new_role_response_obj = create_or_change_role(new_role)

    return Response(new_role_response_obj)


@api_view(["POST"])
def onbord_exisitng_employee_to_new_company(request):
    if not check_user_type(request.user):
        return Response({"content": "Invalid Permisions"}, status=status.HTTP_403_FORBIDDEN)
    
    new_company = request.session.get("company_logged_in_as")
    username = request.data.get("username")
    departments = request.data.get("departments_csv")
    departments_csv = departments.split(",")

    user_employee_to_update = get_object_or_404(
        Employee,
        user__username=username
    )

    print(user_employee_to_update)

    if check_user_type(user_employee_to_update.user) == "Employee":
        return Response({"content": "You are not a company user"}, status=status.HTTP_401_UNAUTHORIZED)

    new_company = Company.objects.get(name=new_company)

    #update the number of emloyees from the old company
    old_company= Company.objects.filter(name=user_employee_to_update.company.name).first()
    old_company.number_of_employees = int(old_company.number_of_employees) - 1
    old_company.save()

    user_employee_to_update = Employee.objects.filter(user__username=username).first()

    #write to the company history table
    EmployeeCompanyHistory.objects.create(
        company=new_company,
        employee=user_employee_to_update
    )

    #update the employee table to point to the new company
    user_employee_to_update.company=new_company
    
    #add new deps(if any) and associate the deps to the user being updated
    for dept in departments_csv:
        print(dept)
        procced_dpt, created = Departments.objects.get_or_create(department = dept)

        user_employee_to_update.department.add(procced_dpt)
    
    user_employee_to_update.save()

    user_employee_to_update_serializer = EmployeeSerializer(user_employee_to_update)

    return Response(user_employee_to_update_serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
def search_employees(request):
    #should be able to search by the following name, employer, position, department, year started, year left
    name = request.data.get("name")
    employer = request.data.get("employer")
    role = request.data.get("role")
    department = request.data.get("department")
    year_started = request.data.get("year_started")
    year_left = request.data.get("year_left")

    query = Q()
    if name:
        query &= Q(user__username__icontains=name) | Q(user__first_name__icontains=name) | Q(user__last_name__icontains=name)

    if employer:
        query &= Q(company__name__icontains=employer)
    if role:
        query &= Q(employee__role__icontains = role)
    if department:
        query &= Q(department__department__icontains=department)
    if year_started:
        query &= Q(employee__date_started__year=year_left)
    if year_left:
        query &= Q(employee__date_left__year=year_left)

    q_results =  Employee.objects.filter(query)
    employee_serializer = EmployeeSerializer(q_results, many=True)

    if q_results:
        return Response(employee_serializer.data, status=status.HTTP_302_FOUND)
    else:
        return Response(employee_serializer.data, status=status.HTTP_404_NOT_FOUND)

def helper_fo_bulk_employee_creation(user, company, save_to_db_fn, generator_fn):
    if not check_user_type(user):
        return Response({"content": "Invalid Permisions"}, status=status.HTTP_403_FORBIDDEN)
    
    
    if user.is_authenticated:
        if check_user_type:
            company = Company.objects.filter(name = company).first()
            try:    #creating a custom error so that users wont be saved when the employee or roles tables make errors.
                with transaction.atomic():  #since all the possible errors are handled, tre exception that triggers the atomic() was offf
                    log = save_to_db_fn(company, generator_fn)   #so had to create a
                    # loop needed coz the data is a list of dicts with [{error: xx}, error: xx]
                    for item in log: 
                        if "error" in item:
                            print("errorrr code ran ")
                            raise IntegrityError
                    
            except IntegrityError:
                print("errorrr caught")
                return(log, status.HTTP_200_OK)
            return(log, status.HTTP_200_OK)
        else: 
            return("Not a company user", status.HTTP_403_FORBIDDEN)
    else:
        return("User not authenticated", status.HTTP_401_UNAUTHORIZED)

@api_view(["GET"])
def create_bulk_employee_from_txt(request):
    from . import data_models as dm
    user = request.user
    company = request.session.get("company_logged_in_as")
    response = helper_fo_bulk_employee_creation(user, company, dm.save_employee_to_db, dm.process_employee_txt_file)
    return Response(response[0], status=response[1])   


@api_view(["GET"])
def create_bulk_employee_from_csv(request):
    from . import data_models as dm
    user = request.user
    company = request.session.get("company_logged_in_as")
    response = helper_fo_bulk_employee_creation(user, company, dm.save_employee_to_db, dm.process_employee_csv_file)
    return Response(response[0], status=response[1])
            

@api_view(["GET"])
def create_bulk_employee_from_excel(request):
    from . import data_models as dm
    user = request.user
    company = request.session.get("company_logged_in_as")
    response = helper_fo_bulk_employee_creation(user, company, dm.save_employee_to_db, dm.process_employee_excel_file)
    return Response(response[0], status=response[1])




@api_view(["GET"])
def create_bulk_companies_from_txt(request):
    from . import data_models as dm
    if request.user.is_authenticated:
        log = dm.save_company_to_db(dm.process_company_txt_file)

        return Response(log, status=status.HTTP_200_OK)
    
    return Response("User not authenticated", status=status.HTTP_401_UNAUTHORIZED)

@api_view(["GET"])
def create_bulk_companies_from_csv(request):
    from . import data_models as dm
    if request.user.is_authenticated:
        log = dm.save_company_to_db(dm.process_company_csv_file)

        return Response(log, status=status.HTTP_200_OK)
    
    return Response("User not authenticated", status=status.HTTP_401_UNAUTHORIZED)

@api_view(["GET"])
def create_bulk_companies_from_excel(request):
    from . import data_models as dm
    if request.user.is_authenticated:
        log = dm.save_company_to_db(dm.process_company_excel_file)

        return Response(log, status=status.HTTP_200_OK)
    
    return Response("User not authenticated", status=status.HTTP_401_UNAUTHORIZED)


@api_view(["POST"])
def associate_bulk_created_companies_with_company_users(request):
    if not check_user_type(request.user):
        return Response({"content": "Invalid Permisions"}, status=status.HTTP_403_FORBIDDEN)

    company_name = request.data.get("name")
    if request.user.is_authenticated:
        company = Company.objects.filter(name=company_name).first()
        company.user = request.user
        company.full_clean()
        company.save()

        company_serializer = CompanySerializer(company)
        return Response(data=company_serializer.data, status=status.HTTP_201_CREATED)



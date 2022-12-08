import pandas as pd
import csv
import psycopg2
from table_commands import create_table_commands
import math

# Table Names
Subject = 'Subject'
Instructor = 'Instructor'
Course = 'Course'
User = 'User'
Review = 'Review'
Analytics = 'Analytics'
Grade = 'Grade'
Evaluation = 'Evaluation'
EvaluationScore = 'EvaluationScore'

class GradeSEC():
    def __init__(self, filename, term):
        self.filename = filename
        self.df = self.open_csv(term)
        self.connection = self.connect_db()
        self.cursor = self.connection.cursor()
        self.term = term

    def open_csv(self, term=None):
        df = pd.read_csv(self.filename, encoding='unicode_escape', low_memory=False)
        df = df.astype(object).where(pd.notnull(df), None)
        # filters by term
        if term:
            df = df.loc[df['Term'] == term]
        return df

    # Connects to postgres db on port 5432
    # Should connect to development database
    def connect_db(self):
        connection = psycopg2.connect(host="localhost", port="5432", database="umbc_sp22", user="postgres")
        return connection

    # Inserts data from new/updated .csv file
    def verify_insert(self):
        for index, row in self.df.iterrows():
            subject_id = self.insert_subject(row)
            instructor_id = self.insert_instructor(row)
            grade_id = self.insert_grade(row, instructor_id)
            evaluation_id = self.insert_evaluation(row, instructor_id)
            course_id = self.insert_course(row, subject_id, instructor_id, grade_id, evaluation_id)
            print('Inserted row | course_id:', course_id, ' | TERM:', self.term)


    # Fetches subject_id if exists otherwise Inserts a subject and returns its id
    # Uniqueness is determined by {df.Subject:name, df.CatalogNumber:catalog_number, df.CatalogTopic:catalog_topic},
    def insert_subject(self, row):
        try:
            name = row['Subject']
            catalog_number = row['CatalogNumber']
            catalog_topic = str(row['CourseTopicDescription'])
            descriptive_name = row['SubjectDescription']
            description = row['CourseDescription']
            catalog_description = row['CatalogDescription']
            credits = str(row['CreditsMin']) if row['CreditsMin'] == row['CreditsMax'] else str(row['CreditsMin']) + '-' + str(row['CreditsMax'])
            academic_org = row['AcademicOrg']
            academic_org_short_desc = row['AcademicOrgShortDesc']
            reporting_college = row['SubjectReportingCollege']
            reporting_college_short_desc = row['SubjectReportingCollegeShortDesc']
            reporting_org = row['SubjectReportingOrg']
            reporting_org_short_desc = row['SubjectReportingOrgShortDesc']

            select_subject = "SELECT id FROM \"Subject\" WHERE name=%s AND catalog_number=%s AND (catalog_topic=%s OR catalog_topic IS NULL)"
            self.cursor.execute(select_subject, (name, catalog_number, None if catalog_topic == "None" else catalog_topic))
            subject_id = self.cursor.fetchone()
            if subject_id is not None: return subject_id[0]

            insert_subject = """INSERT INTO \"Subject\"
            (name, descriptive_name, catalog_number, description, catalog_topic, catalog_description, credits, \
            academic_org, academic_org_short_desc, reporting_college, reporting_college_short_desc, reporting_org, \
            reporting_org_short_desc) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id;
            """

            self.cursor.execute(insert_subject, (name, descriptive_name, catalog_number, description,
                                                 None if catalog_topic == "None" else catalog_topic,
                                                 None if catalog_description == "None" else catalog_description,
                                                 None if credits == "None" else credits,
                                                 None if academic_org == "None" else academic_org,
                                                 None if academic_org_short_desc == "None" else academic_org_short_desc,
                                                 None if reporting_college == "None" else reporting_college,
                                                 None if reporting_college_short_desc == "None" else reporting_college_short_desc,
                                                 None if reporting_org == "None" else reporting_org,
                                                 None if reporting_org_short_desc == "None" else reporting_org_short_desc))
            print('Inserted new Subject', name + catalog_number)
            self.connection.commit()
            return self.cursor.fetchone()[0]

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

    # Inserts all unique instructors into database
    # Uniqueness is determined by {df.PrimaryFaculty:primary_faculty, df.PrimaryFacultyID:faculty_id},
    def insert_instructor(self, row):
        try:
            primary_faculty = row['PrimaryFaculty']
            faculty_id = str(row['PrimaryFacultyID'])
            middle_name = ''
            if primary_faculty == "Unknown":
                first_name = "Unknown"
                middle_name = "Unknown"
                last_name = "Unknown"
            else:
                name_split = primary_faculty.split(',')
                last_name = name_split[0].strip()
                name_split = name_split[1].split(' ')
                if len(name_split) == 2:
                    first_name = name_split[0].strip()
                    middle_name = name_split[1].strip()
                else: first_name = name_split[0].strip()

            select_instructor = "SELECT id FROM \"Instructor\" WHERE first_name=%s AND (middle_name=%s or middle_name IS NUll) AND last_name=%s AND faculty_id=%s "
            self.cursor.execute(select_instructor, (first_name, None if middle_name == "None" else middle_name, last_name, faculty_id))
            instructor_id = self.cursor.fetchone()
            if instructor_id is not None: return instructor_id[0]

            print('Inserted new Instructor', first_name + ' ' + last_name)

            insert_instr = """INSERT INTO \"Instructor\"
                            (faculty_id, first_name, middle_name, last_name) VALUES(%s,%s,%s,%s) RETURNING id;
                            """
            self.cursor.execute(insert_instr, (None if faculty_id == "None" else faculty_id,
                                                first_name,
                                                None if middle_name == "None" or middle_name == "" else middle_name,
                                                last_name))
            self.connection.commit()

            return self.cursor.fetchone()[0]

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

    # Inserts a grade into database
    def insert_grade(self, row, instructor_id):
        try:
            total_enrolled = row["TOT_ENRL"]
            A = row['GRADE_A']
            B = row['GRADE_B']
            C = row['GRADE_C']
            D = row['GRADE_D']
            F = row['GRADE_F']
            O = row['GRADE_O']

            insert_grade = """INSERT INTO \"Grade\"
                            (instructor_id, total_enrolled, "A", "B", "C", "D", "F", "O") VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id;
                            """
            self.cursor.execute(insert_grade, (
                instructor_id,
                None if total_enrolled == "None" else total_enrolled,
                None if A == "None" else A,
                None if B == "None" else B,
                None if C == "None" else C,
                None if D == "None" else D,
                None if F == "None" else F,
                None if F == "None" else O))
            self.connection.commit()

            return self.cursor.fetchone()[0]

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)


    # Inserts an evaluation and corossponding evlauation_scores
    # Bob Andrews: "One thing I wanted to point out is that this is the Primary instructor for the section, not necessarily the Instructor related to the SEEQ.
    # This column 'InstructorCampusID' is the instructor being evaluated on the SEEQ."
    def insert_evaluation(self, row, instructor_id):
        try:
            invited_count = row['InvitedCount']
            respondent_count = row['RespondentCount']
            campus_id = str(row['InstructorCampusID'])
            _id = instructor_id if campus_id == "None" else campus_id

            def insert_evaluation_score(question_number, response):
                insert_eval_score = """INSERT INTO \"EvaluationScore\"
                                        (question, "1", "2", "3", "4", "5", "N/A") VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id;
                                        """
                self.cursor.execute(insert_eval_score, (question_number,
                                                        None if row[response[0]] == "None" else row[response[0]],
                                                        None if row[response[1]] == "None" else row[response[1]],
                                                        None if row[response[2]] == "None" else row[response[2]],
                                                        None if row[response[3]] == "None" else row[response[3]],
                                                        None if row[response[4]] == "None" else row[response[4]],
                                                        None if row[response[5]] == "None" else row[response[5]]))
                self.connection.commit()
                return self.cursor.fetchone()[0]


            # inserts an evalaution_score
            eval_score_ids = []
            for i in range(1, 32+1):
                evaluation_number = 'Question'+str(i)
                evaluation_scores = [column for column in self.df.keys() if column.startswith(evaluation_number)]
                evaluation_score_id = insert_evaluation_score(evaluation_number, evaluation_scores)
                eval_score_ids.append(evaluation_score_id)

            insert_eval_score = """INSERT INTO \"Evaluation\"
                                                (instructor_id, invited_count, respondent_count, "Q1", "Q2", "Q3", "Q4" ,"Q5", "Q6", 
                                                "Q7", "Q8", "Q9", "Q10", "Q11", "Q12", "Q13", "Q14", "Q15", "Q16", "Q17", "Q18", "Q19", "Q20", "Q21", \
                                                "Q22", "Q23", "Q24", "Q25", "Q26", "Q27", "Q28", "Q29", "Q30", "Q31", "Q32") \
                                                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id;
                                                """
            self.cursor.execute(insert_eval_score, (instructor_id,
                                                    None if invited_count == "None" else invited_count,
                                                    None if respondent_count == "None" else respondent_count,
                                                    eval_score_ids[0], eval_score_ids[1], eval_score_ids[2], eval_score_ids[3], \
                                                    eval_score_ids[4], eval_score_ids[5], eval_score_ids[6], eval_score_ids[7], eval_score_ids[8], eval_score_ids[9],\
                                                    eval_score_ids[10], eval_score_ids[11], eval_score_ids[12], eval_score_ids[13],eval_score_ids[14], eval_score_ids[15], \
                                                    eval_score_ids[16], eval_score_ids[17], eval_score_ids[18], eval_score_ids[19], eval_score_ids[20], eval_score_ids[21],
                                                    eval_score_ids[22], eval_score_ids[23],eval_score_ids[24], eval_score_ids[25],eval_score_ids[26], eval_score_ids[27], \
                                                    eval_score_ids[28], eval_score_ids[29], eval_score_ids[30], eval_score_ids[31]))
            self.connection.commit()
            return self.cursor.fetchone()[0]

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)


    # inserts a course
    def insert_course(self, row, subject_id, instructor_id, grade_id, evaluation_id):
        try:
            class_number = str(row['ClassNumber'])
            section = str(row['ClassSection'])
            term = row['Term']
            session_code = str(row['SessionCode'])
            course_level = row['CourseLevel']
            total_enrolled = row['TOT_ENRL']

            def parse_semester(term):
                year = term[1:3]
                _semester = ""
                if term[3] == "0":
                    _semester = "Winter"
                elif term[3] == "2":
                    _semester = "Spring"
                elif term[3] == "6":
                    _semester = "Summer"
                elif term[3] == "8":
                    _semester = "Fall"
                return "%s 20%s" % (_semester, year)

            semester = parse_semester(str(term))

            insert_course = """INSERT INTO \"Course\"
                                    ("subject_id", "instructor_id", "grade_id", "evaluation_id", "class_number", "section", "term", \
                                    "semester", "session_code", "course_level", "total_enrolled") VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id;
                                    """
            self.cursor.execute(insert_course, (subject_id, instructor_id, grade_id, evaluation_id,
                                                class_number, section, term, semester, session_code,
                                                None if course_level == "None" else course_level,
                                                None if total_enrolled == "None" else total_enrolled))
            self.connection.commit()
            return self.cursor.fetchone()[0]

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)


    def migrate_reviews(self):
        # Should connect to prod database
        connection = psycopg2.connect(host="localhost", port="5432", database="umbc_sp22_restore", user="postgres")
        prev_db_cursor = connection.cursor()
        select_reviews = "SELECT * FROM \"Review\""
        prev_db_cursor.execute(select_reviews)
        reviews = prev_db_cursor.fetchall()
        for review in reviews:
            id, body, rating, grade, approved, user_id, subject_id, instructor_id, faculty_id, date_created, last_updated = review
            select_instructor = "SELECT faculty_id, first_name, middle_name, last_name FROM \"Instructor\" WHERE id=" + str(instructor_id)
            prev_db_cursor.execute(select_instructor)
            faculty_id, first_name, middle_name, last_name = prev_db_cursor.fetchone()

            if middle_name:
                select_instructor = "SELECT id FROM \"Instructor\" WHERE first_name=%s AND middle_name=%s AND last_name=%s"
                self.cursor.execute(select_instructor, (first_name, middle_name, last_name))
            else:
                select_instructor = "SELECT id FROM \"Instructor\" WHERE first_name=%s AND middle_name IS NULL AND last_name=%s"
                self.cursor.execute(select_instructor,  (first_name, last_name))
            instructor_id = self.cursor.fetchone()
            if instructor_id is None:
                # !!!!!!!!!!!!!!!!!!!!!!! NOTE NOTE NOTE NOTE !!!!!!!!!!!!!!!!!!!!!!!
                # some names of the professors change with every new .csv file we get. i.e Willie Billingslea -> Will Billingslea
                # we need to maunually update the instructor_id by looking at the old database. for now just setting it to 1
                # Manualy update these values using faculty_id and doing a search of the professor
                instructor_id = 1
                # !!!!!!!!!!!!!!!!!!!!!!! NOTE NOTE NOTE NOTE !!!!!!!!!!!!!!!!!!!!!!!

            # get user id
            select_username = "SELECT username FROM \"User\" WHERE id="+str(user_id)
            prev_db_cursor.execute(select_username)
            username = prev_db_cursor.fetchone()
            if username:
                select_user = "SELECT id FROM \"User\" WHERE username=%s"
                self.cursor.execute(select_user, (username))
                user_id = self.cursor.fetchone()



            # insert into new db
            insert_review = """INSERT INTO \"Review\"
                                        ("body", "rating", "grade", "approved", "user_id", "subject_id", "instructor_id", "faculty_id", "date_created", "last_updated") VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                        """
            faculty_id = faculty_id if faculty_id else "None"
            self.cursor.execute(insert_review, (body,rating,grade,approved,user_id,subject_id,instructor_id,faculty_id,date_created,last_updated))
            self.connection.commit()



    def migrate_users(self):
        # Should connect to prod database
        connection = psycopg2.connect(host="localhost", port="5432", database="umbc_sp22_restore", user="postgres")
        prev_db_cursor = connection.cursor()
        select_users = "SELECT * FROM \"User\""
        prev_db_cursor.execute(select_users)
        users = prev_db_cursor.fetchall()
        for user in users:
            id, username, email, password, token, date_created = user
            insert_user = """INSERT INTO \"User\" 
                            ("username", "email", "password", "token", "date_created") VALUES(%s,%s,%s,%s,%s)
                            """
            self.cursor.execute(insert_user, (username, email, password, token, date_created))
            self.connection.commit()


    def create_tables(self):
        for table in create_table_commands:
            self.cursor.execute(table)
            self.connection.commit()


SPRING_2021_TERM = 2212
WINTER_2022_TERM = 2220
inst = GradeSEC('/Users/natypro/Gritview_PROD/Data/CourseGradeSCEData (F17-SP22).csv', None)
# inst.create_tables()
# print(inst.verify_insert())
# inst.migrate_users()
# inst.migrate_reviews()